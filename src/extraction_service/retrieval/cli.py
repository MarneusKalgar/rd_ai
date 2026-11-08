"""Offline E01 protocol, snapshot and forty-case evaluation commands."""

import argparse
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from extraction_service.retrieval.core import (
    MAX_ARTIFACT_BYTES,
    Snapshot,
    StrictModel,
    build_snapshot,
    canonical,
    digest,
    read_confined,
    retrieve,
)

COMMANDS = ("validate-retrieval-protocol", "build-reference-index", "evaluate-retrieval")
DEFAULT_PROTOCOL = "config/retrieval/P03-E01-v3.json"


class Case(StrictModel):
    """Evaluator-only technical oracle, never supplied to the retriever."""

    id: str
    group: Literal["lookup", "free", "negative", "lifecycle"]
    query: str
    scope: Literal["A", "B"]
    topic: str | None
    catalog: str
    effective_time: int
    relevant: list[str]
    expected_status: Literal["evidence_found", "insufficient_evidence", "conflicting_evidence"]


class Cases(StrictModel):
    """Frozen complete population with explicit label authority."""

    version: Literal[1]
    authority: str
    cases: list[Case] = Field(min_length=40, max_length=40)


class Protocol(StrictModel):
    """Bind source, implementation, plan and oracle bytes before evaluation."""

    id: Literal["P03-E01-v1", "P03-E01-v2", "P03-E01-v3"]
    bindings: dict[str, str]
    cases: Literal["config/evaluation/P03-cases-v1.json"]
    catalog: Literal["config/retrieval/catalog.json"]
    model_calls: Literal[0]
    api_spend: Literal[0]
    k: Literal[3]
    recall_threshold: float = Field(ge=0.85, le=0.85)


def load_protocol(root: Path, relative: str) -> tuple[Protocol, Cases]:
    """Validate every declared binding and the complete unique case population."""

    protocol = Protocol.model_validate_json(read_confined(root, relative, MAX_ARTIFACT_BYTES))
    for path, expected in protocol.bindings.items():
        if digest(read_confined(root, path, MAX_ARTIFACT_BYTES)) != expected:
            raise ValueError(f"Protocol binding mismatch: {path}")
    cases = Cases.model_validate_json(read_confined(root, protocol.cases, MAX_ARTIFACT_BYTES))
    if len({case.id for case in cases.cases}) != 40:
        raise ValueError("Duplicate query case")
    if [
        sum(case.group == group for case in cases.cases)
        for group in ("lookup", "free", "negative", "lifecycle")
    ] != [12, 12, 8, 8]:
        raise ValueError("Case population mismatch")
    required = {protocol.cases, protocol.catalog}
    required.update(case.catalog for case in cases.cases)
    required.update(
        {
            "src/extraction_service/retrieval/core.py",
            "src/extraction_service/retrieval/cli.py",
            "config/retrieval/P03-plan-v1.md",
        }
    )
    for catalog in {case.catalog for case in cases.cases}:
        snapshot = build_snapshot(root, catalog)
        required.update(chunk.reference.path for chunk in snapshot.chunks)
    if not required.issubset(protocol.bindings):
        raise ValueError("Missing required protocol bindings")
    return protocol, cases


def relevance_metrics(ids: list[str], relevant: set[str]) -> tuple[float | None, float, float]:
    """Score deduplicated source-unit relevance with unfilled ranks penalized."""

    matches = set(ids) & relevant
    recall = len(matches) / len(relevant) if relevant else None
    precision = len(matches) / 3
    reciprocal_rank = next((1 / rank for rank, item in enumerate(ids, 1) if item in relevant), 0.0)
    return recall, precision, reciprocal_rank


def evaluate(root: Path, protocol: Protocol, cases: Cases) -> dict[str, Any]:
    """Retain every outcome, score source-unit relevance and separate negatives."""

    started = time.monotonic()
    outcomes: list[dict[str, Any]] = []
    recalls: list[float] = []
    precisions: list[float] = []
    reciprocal_ranks: list[float] = []
    exact_passes = 0
    hard_status_passes = True
    for case in cases.cases:
        if time.monotonic() - started > 300:
            raise ValueError("Evaluation deadline exceeded")
        snapshot = build_snapshot(root, case.catalog)
        for method in ("exact", "bm25"):
            call_start = time.monotonic()
            response = retrieve(
                root,
                case.catalog,
                snapshot,
                query=case.query,
                scope=case.scope,
                effective_time=case.effective_time,
                method=method,
                topic=case.topic,
            )
            relevant = set(case.relevant)
            ids = [
                hit.source_id + ("@" + hit.revision if "@" in " ".join(relevant) else "")
                for hit in response.hits
            ]
            matches = set(ids) & relevant
            recall, precision, rr = relevance_metrics(ids, relevant)
            if method == "bm25" and relevant:
                recalls.append(recall if recall is not None else 0)
                precisions.append(precision)
                reciprocal_ranks.append(rr)
            if method == "exact" and case.group == "lookup":
                exact_passes += int(matches == relevant and response.status == case.expected_status)
            applicable = method == "bm25" or case.topic is not None
            # A lexical hit cannot certify semantic answerability. Exact keyed
            # lifecycle checks and the explicit negative controls have status oracles.
            status_control = (method == "exact" and case.topic is not None) or (
                method == "bm25" and case.group == "negative"
            )
            if status_control:
                hard_status_passes &= response.status == case.expected_status
            outcomes.append(
                dict(
                    case=case.id,
                    group=case.group,
                    method=method,
                    evidence=response.model_dump(),
                    recall=recall,
                    precision=precision,
                    reciprocal_rank=rr,
                    expected_status=case.expected_status,
                    status_matches=response.status == case.expected_status,
                    applicable=applicable,
                    status_control_applicable=status_control,
                    elapsed_seconds=time.monotonic() - call_start,
                )
            )
    macro_recall = sum(recalls) / len(recalls)
    return dict(
        protocol=protocol.id,
        protocol_identity=digest(canonical(protocol.model_dump())),
        authority=cases.authority,
        query_count=40,
        outcomes=outcomes,
        model_calls=0,
        api_spend=0,
        exact_passes=exact_passes,
        macro_recall_at_3=macro_recall,
        macro_precision_at_3=sum(precisions) / len(precisions),
        mrr=sum(reciprocal_ranks) / len(reciprocal_ranks),
        hard_status_controls_passed=hard_status_passes,
        lexical_decision=(
            "adopt"
            if macro_recall >= protocol.recall_threshold
            and hard_status_passes
            and exact_passes == 12
            else "reject"
        ),
        semantic_answer_accuracy=None,
        elapsed_seconds=time.monotonic() - started,
    )


def publish(path: Path, value: object) -> None:
    """Atomically publish bounded JSON without replacing historical artifacts."""

    data = canonical(value)
    if len(data) > MAX_ARTIFACT_BYTES:
        raise ValueError("Output size limit exceeded")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def add_commands(commands: Any) -> None:
    """Register strictly offline actions."""

    for name in COMMANDS:
        parser = commands.add_parser(name, help=__doc__)
        parser.add_argument("--protocol", default=DEFAULT_PROTOCOL)
        parser.add_argument("--output", type=Path)
        parser.add_argument("--check-result")


def dispatch(args: argparse.Namespace) -> int:
    """Validate, build or evaluate without model/client/ledger initialization."""

    root = args.project_dir
    protocol, cases = load_protocol(root, args.protocol)
    result: dict[str, Any]
    if args.command == "validate-retrieval-protocol":
        result = dict(protocol=protocol.id, valid=True, cases=40)
    elif args.command == "build-reference-index":
        snapshot = build_snapshot(root, protocol.catalog)
        result = snapshot.model_dump()
        Snapshot.model_validate_json(canonical(result))
    else:
        result = evaluate(root, protocol, cases)
    if args.check_result:
        saved = json.loads(read_confined(root, args.check_result, MAX_ARTIFACT_BYTES))
        # Wall-clock observations are retained, but not deterministic reproduction inputs.
        for report in (saved, result):
            report.pop("elapsed_seconds", None)
            for outcome in report.get("outcomes", []):
                outcome.pop("elapsed_seconds", None)
        if saved != result:
            raise ValueError("Result reproduction mismatch")
    if args.output:
        publish(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0
