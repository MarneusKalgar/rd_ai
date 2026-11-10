"""Reproduce I01 semantic contexts and captures without a model or database."""

import argparse
import json
from pathlib import Path
from typing import Any

from extraction_service.retrieval.cli import load_protocol
from extraction_service.retrieval.composition import direct_compose
from extraction_service.retrieval.core import build_snapshot, canonical, digest, read_confined
from extraction_service.retrieval.integration import langchain_compose
from extraction_service.retrieval.integration_cli import (
    PROFILE,
    context_from_points,
    fixture_reply,
    inherited_vectors,
)
from extraction_service.retrieval.vector_store import cosine


def reproduce(root: Path, relative: str, expected_sha256: str) -> dict[str, int | bool]:
    """Verify the report digest and rebuild all forty contexts and 120 job outcomes."""

    raw = read_confined(root, relative, 32 * 1024 * 1024)
    if digest(raw) != expected_sha256:
        raise ValueError("I01 report digest mismatch")
    report = json.loads(raw)
    manifest = json.loads(read_confined(root, "config/retrieval/P03-I01-v1.json", 65536))
    for path, expected in manifest["bindings"].items():
        if digest(read_confined(root, path, 32 * 1024 * 1024)) != expected:
            raise ValueError("I01 reproduction binding mismatch")
    _, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    vectors = inherited_vectors(root)
    profile = json.loads(read_confined(root, PROFILE, 65536))
    lexical_report = json.loads(
        read_confined(root, "results/submission/P03-E01-v3/report.json", 32 * 1024 * 1024)
    )
    lexical = {
        row["case"]: row["evidence"]
        for row in lexical_report["outcomes"]
        if row["method"] == "bm25"
    }
    retrieval = {row["case"]: row for row in report["retrieval"]}
    captures = {(row["case"], row["arm"]): row for row in report["compositions"]}
    if (
        len(report["retrieval"]) != 40
        or len(retrieval) != 40
        or len(report["compositions"]) != 120
        or len(captures) != 120
    ):
        raise ValueError("I01 reproduction population mismatch")
    for case_index, case in enumerate(cases.cases):
        snapshot = build_snapshot(root, case.catalog)
        query_vector = vectors[digest(case.query.encode())]
        points = []
        for index, chunk in enumerate(snapshot.chunks):
            ref = chunk.reference
            if (
                ref.scope in ("shared", case.scope)
                and ref.status == "active"
                and ref.effective_from <= case.effective_time
                and (ref.effective_until is None or case.effective_time < ref.effective_until)
            ):
                points.append(dict(id=index, score=cosine(query_vector, vectors[ref.sha256])))
        context = context_from_points(
            root,
            case.catalog,
            snapshot,
            case.effective_time,
            case.scope,
            query_vector,
            vectors,
            points,
        )
        if retrieval[case.id]["context"] != context or not retrieval[case.id]["parity"]:
            raise ValueError("I01 context reproduction mismatch")
        for arm in ("none", "bm25", "vector"):
            evidence: dict[str, Any] = (
                dict(status="insufficient_evidence", hits=[])
                if arm == "none"
                else lexical[case.id]
                if arm == "bm25"
                else context
            )
            hits = [
                {key: value for key, value in hit.items() if key != "score"}
                for hit in evidence["hits"]
            ]
            job = dict(
                arm=arm,
                scope=case.scope,
                question=case.query,
                context=hits,
                status=evidence["status"],
                settings=profile["capture_settings"],
                raw_response=fixture_reply(case_index, hits),
            )
            direct = direct_compose(job)
            framework = langchain_compose(job)
            saved = captures[(case.id, arm)]
            if (
                not saved["parity"]
                or canonical(direct) != canonical(framework)
                or canonical(direct) != canonical(saved["outcome"])
            ):
                raise ValueError("I01 capture reproduction mismatch")
    return dict(
        contexts_verified=40,
        compositions_verified=120,
        semantic_reproduction=True,
        canonical_request_reproduction=True,
        database_calls=0,
        embedding_calls=0,
        generation_calls=0,
    )


def main() -> int:
    """Require an explicit trusted report checksum; never rerun live retrieval."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--report", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    print(json.dumps(reproduce(args.project_dir, args.report, args.sha256)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
