"""Freeze and verify E03 jobs, inherited real retrieval evidence and run controls."""

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field

from extraction_service.answering.contract import Answer, AnswerJob, Arm, Context
from extraction_service.application.admission import ProviderCoverage
from extraction_service.configuration.models import ModelConfig, SamplingConfig
from extraction_service.retrieval.cli import load_protocol
from extraction_service.retrieval.core import (
    MAX_ARTIFACT_BYTES,
    build_snapshot,
    canonical,
    digest,
    read_confined,
    retrieve,
)
from extraction_service.runtime_types import NonEmptyText, PositiveFloat, StrictModel

PROFILE = "config/retrieval/P03-E03-profile-v1.json"
MANIFEST = "config/retrieval/P03-E03-v1.json"
CASES = "config/evaluation/P03-cases-v1.json"
INHERITED = "results/submission/P03-I01-v1/report.json"
INHERITED_HASH = "f8388bdaae0a40cf045f0d69ff9dee67a7e20fb215864e37a56e534347d47604"


class Profile(StrictModel):
    id: Literal["P03-E03-v1"]
    model: ModelConfig
    coverage: ProviderCoverage
    reported_provider: NonEmptyText
    sampling: SamplingConfig
    prompt: NonEmptyText
    rubric: NonEmptyText
    pilot_cases: Annotated[list[str], Field(min_length=12, max_length=12)]
    request_seconds: PositiveFloat
    phase_seconds: PositiveFloat
    phase_allowance_usd: Annotated[Decimal, Field(gt=0, le=10, allow_inf_nan=False)]
    reasoning: NonEmptyText
    context_policy: NonEmptyText
    physical_policy: NonEmptyText
    continuation_policy: NonEmptyText
    integration: Literal["direct"]
    context_provenance: NonEmptyText


def load_profile(root: Path) -> Profile:
    return Profile.model_validate_json(read_confined(root, PROFILE, 65536))


def _saved_contexts(root: Path) -> dict[str, Any]:
    """Use byte-identified results of real Qdrant queries, never synthetic captures."""

    raw = read_confined(root, INHERITED, MAX_ARTIFACT_BYTES)
    if digest(raw) != INHERITED_HASH:
        raise ValueError("Inherited real retrieval report hash mismatch")
    rows = json.loads(raw)["retrieval"]
    contexts = {row["case"]: row["context"] for row in rows}
    if len(rows) != 40 or len(contexts) != 40 or not all(row["parity"] for row in rows):
        raise ValueError("Inherited context population/parity mismatch")
    return contexts


def build_jobs(root: Path, profile: Profile) -> list[AnswerJob]:
    """Revalidate every source against current scope/version before rendering evidence."""

    _, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    ids = {case.id for case in cases.cases}
    pilot = set(profile.pilot_cases)
    groups = Counter(case.group for case in cases.cases if case.id in pilot)
    if len(ids) != 40 or len(pilot) != 12 or not pilot <= ids or set(groups.values()) != {3}:
        raise ValueError("E03 pilot must contain three cases per group")
    rubric = json.loads(read_confined(root, profile.rubric, 65536))
    if set(rubric["cases"]) != ids or any(not value for value in rubric["cases"].values()):
        raise ValueError("E03 propositions must cover the exact forty cases")
    saved = _saved_contexts(root)
    if set(saved) != ids:
        raise ValueError("Inherited contexts differ from selected cases")
    jobs: list[AnswerJob] = []
    for case in cases.cases:
        snapshot = build_snapshot(root, case.catalog)
        lexical = retrieve(
            root,
            case.catalog,
            snapshot,
            query=case.query,
            scope=case.scope,
            effective_time=case.effective_time,
            method="bm25",
        ).model_dump()
        eligible: dict[bytes, Context] = {}
        for chunk in snapshot.chunks:
            ref = chunk.reference
            if (
                ref.scope in ("shared", case.scope)
                and ref.status == "active"
                and ref.effective_from <= case.effective_time
                and (ref.effective_until is None or case.effective_time < ref.effective_until)
            ):
                context = Context(
                    source_id=ref.id,
                    revision=ref.revision,
                    sha256=ref.sha256,
                    start=0,
                    end=chunk.end,
                    quote=chunk.text,
                )
                eligible[canonical(context.model_dump())] = context
        for arm in Arm:
            evidence: dict[str, Any] = (
                dict(status="insufficient_evidence", hits=[])
                if arm == Arm.NONE
                else lexical
                if arm == Arm.BM25
                else saved[case.id]
            )
            contexts = []
            for hit in evidence["hits"]:
                context = Context.model_validate(
                    {key: value for key, value in hit.items() if key != "score"}
                )
                if canonical(context.model_dump()) not in eligible:
                    raise ValueError("Ineligible or modified E03 context")
                contexts.append(context)
            jobs.append(
                AnswerJob(
                    case_id=case.id,
                    arm=arm,
                    scope=case.scope,
                    question=case.query,
                    context=contexts,
                    retrieval_status=evidence["status"],
                )
            )
    return jobs


def bindings(root: Path, profile: Profile) -> dict[str, str]:
    """Bind implementation, runtime, rubric, approved references and exact contexts."""

    paths = [
        PROFILE,
        profile.prompt,
        profile.rubric,
        CASES,
        INHERITED,
        "config/retrieval/P03-E01-v3.json",
        "pyproject.toml",
        "uv.lock",
        "Dockerfile",
        "compose.e03.yaml",
    ]
    for directory in ("src", "data/references"):
        paths.extend(
            path.relative_to(root).as_posix()
            for path in (root / directory).rglob("*")
            if path.is_file() and path.suffix in (".py", ".txt")
        )
    paths.extend(
        path.relative_to(root).as_posix()
        for path in (root / "config/retrieval").glob("catalog*.json")
    )
    return {path: digest(read_confined(root, path, MAX_ARTIFACT_BYTES)) for path in sorted(paths)}


def freeze(root: Path) -> dict[str, Any]:
    """Create once; changing any matched control requires a new experiment identity."""

    profile = load_profile(root)
    jobs = build_jobs(root, profile)
    manifest = dict(
        id=profile.id,
        bindings=bindings(root, profile),
        jobs_sha256=digest(canonical([job.model_dump(mode="json") for job in jobs])),
        schema_sha256=digest(canonical(Answer.model_json_schema())),
    )
    path = root / MANIFEST
    with path.open("xb") as output:
        output.write(json.dumps(manifest, ensure_ascii=False, indent=2).encode() + b"\n")
    return manifest


def verified_jobs(root: Path) -> tuple[Profile, list[AnswerJob], str]:
    """Reject drift before metadata or inference and again before each physical call."""

    raw = read_confined(root, MANIFEST, MAX_ARTIFACT_BYTES)
    manifest = json.loads(raw)
    profile = load_profile(root)
    if manifest["bindings"] != bindings(root, profile):
        raise ValueError("E03 frozen bindings changed")
    jobs = build_jobs(root, profile)
    if manifest["jobs_sha256"] != digest(
        canonical([j.model_dump(mode="json") for j in jobs])
    ) or manifest["schema_sha256"] != digest(canonical(Answer.model_json_schema())):
        raise ValueError("E03 frozen jobs/schema changed")
    return profile, jobs, digest(raw)


def select_phase(jobs: list[AnswerJob], profile: Profile, phase: str) -> list[AnswerJob]:
    if phase not in ("pilot", "remaining"):
        raise ValueError("Unknown E03 phase")
    return [job for job in jobs if (job.case_id in profile.pilot_cases) == (phase == "pilot")]
