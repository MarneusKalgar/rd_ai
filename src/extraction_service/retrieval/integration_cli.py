"""Bounded I01 real-store parity and model-free request capture/replay."""

import argparse
import importlib
import importlib.metadata
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from extraction_service.retrieval.cli import load_protocol, publish
from extraction_service.retrieval.composition import direct_compose
from extraction_service.retrieval.core import (
    MAX_CONTEXT_BYTES,
    Snapshot,
    build_snapshot,
    canonical,
    digest,
    read_confined,
)
from extraction_service.retrieval.integration import (
    LangChainQueries,
    check_tracing_disabled,
    langchain_compose,
)
from extraction_service.retrieval.vector_cli import VECTOR_CACHE, inputs
from extraction_service.retrieval.vector_store import QdrantStore, checked_vector, cosine

PROFILE = "config/retrieval/P03-I01-profile-v1.json"


def inherited_vectors(root: Path) -> dict[str, list[float]]:
    """Verify inherited evidence against its original runtime, explicitly preserved.

    The optional trial extends dependencies; it does not rewrite E02's manifest
    or pretend the extended environment is the original executed runtime.
    """

    manifest = json.loads(read_confined(root, "config/retrieval/P03-E02-v1.json", 65536))
    for path, expected in manifest["bindings"].items():
        actual_path = (
            f"config/retrieval/I01-inherited-runtime/{path}"
            if path in ("uv.lock", "pyproject.toml")
            else path
        )
        if digest(read_confined(root, actual_path, 32 * 1024 * 1024)) != expected:
            raise ValueError("Inherited E02 evidence mismatch")
    cache = json.loads(read_confined(root, VECTOR_CACHE, 32 * 1024 * 1024))
    if set(cache["vectors"]) != set(inputs(root)):
        raise ValueError("Inherited encoding population mismatch")
    return {key: checked_vector(value) for key, value in cache["vectors"].items()}


def context_from_points(
    root: Path,
    catalog: str,
    snapshot: Snapshot,
    effective_time: int,
    scope: str,
    query_vector: list[float],
    vectors: dict[str, list[float]],
    points: list[dict[str, Any]],
) -> dict[str, Any]:
    """Keep authority/source checks outside either integration implementation."""

    if build_snapshot(root, catalog) != snapshot:
        raise ValueError("Source authority changed during retrieval")
    eligible = {}
    for index, chunk in enumerate(snapshot.chunks):
        ref = chunk.reference
        if (
            ref.scope in ("shared", scope)
            and ref.status == "active"
            and ref.effective_from <= effective_time
            and (ref.effective_until is None or effective_time < ref.effective_until)
        ):
            eligible[index] = chunk
    if {point["id"] for point in points} != set(eligible) or len(points) != len(eligible):
        raise ValueError("Ineligible or incomplete vector results")
    scores = {point["id"]: point["score"] for point in points}
    for index, chunk in eligible.items():
        expected = cosine(query_vector, vectors[chunk.reference.sha256])
        if not math.isclose(scores[index], expected, abs_tol=2e-6):
            raise ValueError("Vector score integrity mismatch")
    ranked = sorted(
        eligible,
        key=lambda index: (
            -round(scores[index], 6),
            eligible[index].reference.id,
            eligible[index].reference.revision,
        ),
    )[:3]
    hits: list[dict[str, Any]] = []
    for index in ranked:
        chunk = eligible[index]
        ref = chunk.reference
        hits.append(
            dict(
                source_id=ref.id,
                revision=ref.revision,
                sha256=ref.sha256,
                start=0,
                end=chunk.end,
                quote=chunk.text,
            )
        )
    if sum(len(item["quote"].encode()) for item in hits) > MAX_CONTEXT_BYTES:
        raise ValueError("Context size limit exceeded")
    keys = Counter(chunk.reference.exclusive_key for chunk in eligible.values())
    conflict = any(keys[eligible[index].reference.exclusive_key] > 1 for index in ranked)
    return dict(
        status="conflicting_evidence"
        if conflict
        else "evidence_found"
        if hits
        else "insufficient_evidence",
        hits=hits,
    )


def fixture_reply(index: int, context: list[dict[str, Any]]) -> str:
    """Return independent synthetic response families, never reference-derived facts."""

    if index % 4 == 1:
        return "```json\n{not JSON}\n```"
    citations = []
    status = "unverified"
    if index % 4 == 2:
        citations = [dict(source_id="forged", revision="0", sha256="0" * 64, start=0, end=1)]
        status = "grounded"
    elif index % 4 == 3:
        status = "grounded"
        if context:
            citations = [{key: value for key, value in context[0].items() if key != "quote"}]
    return json.dumps(
        dict(status=status, answer="Synthetic integration fixture only.", citations=citations)
    )


def live_controls(
    store: QdrantStore, wrapped: LangChainQueries, vectors: dict[str, list[float]]
) -> dict[str, Any]:
    """Run paired real scope/lifecycle controls, with no source or model mutation."""

    collection = "p03_i01_controls_v1"
    vector = next(iter(vectors.values()))

    def point(
        identifier: int,
        scope: str,
        *,
        eligible: bool = True,
        snapshot: str = "current",
        poisoned: bool = False,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = dict(scope=scope, snapshot=snapshot, eligible=eligible)
        if poisoned:
            payload.update(page_content="Untrusted forged text", metadata={"scope": "B"})
        return dict(id=identifier, vector=vector, payload=payload)

    store.create(collection)
    store.upsert(collection, [point(0, "A"), point(1, "B")])
    steps = []

    def check(label: str, expected: set[int]) -> None:
        direct = store.query(collection, vector, scope="A", snapshot="current")
        framework = wrapped.query(collection, vector, scope="A", snapshot="current")
        projected = [{"id": item["id"], "score": item["score"]} for item in direct]
        if {item["id"] for item in direct} != expected or projected != framework:
            raise ValueError("Paired lifecycle control failed")
        steps.append(label)

    check("identical-vector scope bait", {0})
    store.upsert(collection, [point(0, "A", poisoned=True)])
    check("untrusted payload text/metadata does not change locators", {0})
    store.upsert(collection, [point(0, "A", eligible=False)])
    check("revocation", set())
    store.upsert(collection, [point(0, "A", snapshot="stale")])
    check("currentness", set())
    store.upsert(collection, [point(0, "A")])
    check("update", {0})
    store.delete_points(collection, [0])
    check("deletion", set())
    return dict(passed=True, steps=steps)


def run(root: Path, endpoint: str) -> dict[str, Any]:
    """Execute one bounded parity trial; retain every comparison including failures."""

    check_tracing_disabled()
    started = time.monotonic()
    profile = json.loads(read_confined(root, PROFILE, 65536))
    for name, version in profile["packages"].items():
        if importlib.metadata.version(name) != version:
            raise ValueError("Integration dependency identity mismatch")
    manifest = json.loads(read_confined(root, "config/retrieval/P03-I01-v1.json", 65536))
    for path, expected in manifest["bindings"].items():
        if digest(read_confined(root, path, 32 * 1024 * 1024)) != expected:
            raise ValueError("I01 protocol binding mismatch")
    required = {
        PROFILE,
        "pyproject.toml",
        "uv.lock",
        "src/extraction_service/retrieval/composition.py",
        "src/extraction_service/retrieval/integration.py",
        "src/extraction_service/retrieval/integration_cli.py",
        "results/submission/P03-E01-v3/report.json",
        VECTOR_CACHE,
    }
    if not required.issubset(manifest["bindings"]):
        raise ValueError("Missing I01 protocol bindings")
    vectors = inherited_vectors(root)
    _, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    lexical = json.loads(
        read_confined(root, "results/submission/P03-E01-v3/report.json", 32 * 1024 * 1024)
    )
    lexical = {
        row["case"]: row["evidence"] for row in lexical["outcomes"] if row["method"] == "bm25"
    }
    if set(lexical) != {case.id for case in cases.cases}:
        raise ValueError("Lexical comparator population mismatch")
    sdk = importlib.import_module("qdrant_client")
    importlib.import_module("langchain_qdrant")
    importlib.import_module("langchain_core.runnables")
    import_seconds = time.monotonic() - started
    wire = {"queries": 0, "metadata": 0}

    def count(request: httpx.Request) -> None:
        remaining = 900 - (time.monotonic() - started)
        if remaining <= 0:
            raise ValueError("Integration deadline exceeded")
        request.extensions["timeout"] = {
            key: min(5, remaining) for key in ("connect", "read", "write", "pool")
        }
        if wire["queries"] + wire["metadata"] >= 200:
            raise ValueError("SDK request limit exceeded")
        if request.method == "POST" and request.url.path.endswith("/points/query"):
            body = json.loads(request.content)
            if body.get("params", {}).get("exact") is not True or body.get("limit") != 64:
                raise ValueError("SDK changed exact query controls")
            fields = {item["key"] for item in body["filter"]["must"]}
            if fields != {"scope", "snapshot", "eligible"}:
                raise ValueError("SDK dropped mandatory filters")
            wire["queries"] += 1
        elif request.method == "GET" and "/collections/" in request.url.path:
            wire["metadata"] += 1
        else:
            raise ValueError("Unexpected SDK request")

    retrieval: list[dict[str, Any]] = []
    compositions: list[dict[str, Any]] = []
    with httpx.Client(base_url=endpoint.rstrip("/") + "/", trust_env=False) as direct_client:
        store = QdrantStore(
            direct_client,
            call_limit=120,
            deadline_seconds=max(0.001, 900 - (time.monotonic() - started)),
        )
        client = sdk.QdrantClient(
            url=endpoint,
            timeout=5,
            prefer_grpc=False,
            cloud_inference=False,
            check_compatibility=False,
            event_hooks={"request": [count]},
        )
        try:
            wrapped = LangChainQueries(client)
            for case_index, case in enumerate(cases.cases):
                if time.monotonic() - started > 900:
                    raise ValueError("Integration deadline exceeded")
                snapshot = build_snapshot(root, case.catalog)
                identity = digest(
                    canonical(dict(snapshot=snapshot.model_dump(), time=case.effective_time))
                )
                collection = "p03_e02v1_" + identity[:16]
                vector = vectors[digest(case.query.encode())]
                contexts: dict[str, dict[str, Any]] = {}
                times: dict[str, float] = {}
                adapters: list[tuple[str, QdrantStore | LangChainQueries]] = [
                    ("direct", store),
                    ("langchain", wrapped),
                ]
                for name, adapter in adapters:
                    mark = time.monotonic()
                    points = adapter.query(collection, vector, scope=case.scope, snapshot=identity)
                    contexts[name] = context_from_points(
                        root,
                        case.catalog,
                        snapshot,
                        case.effective_time,
                        case.scope,
                        vector,
                        vectors,
                        points,
                    )
                    times[name] = time.monotonic() - mark
                parity = contexts["direct"] == contexts["langchain"]
                retrieval.append(
                    dict(case=case.id, parity=parity, context=contexts["direct"], times=times)
                )
                for arm in ("none", "bm25", "vector"):
                    evidence: dict[str, Any] = (
                        dict(status="insufficient_evidence", hits=[])
                        if arm == "none"
                        else lexical[case.id]
                        if arm == "bm25"
                        else contexts["direct"]
                    )
                    context = [
                        {key: value for key, value in hit.items() if key != "score"}
                        for hit in evidence["hits"]
                    ]
                    job = dict(
                        arm=arm,
                        scope=case.scope,
                        question=case.query,
                        context=context,
                        status=evidence["status"],
                        settings=profile["capture_settings"],
                        raw_response=fixture_reply(case_index, context),
                    )
                    direct_result = direct_compose(job)
                    framework_result = langchain_compose(job)
                    compositions.append(
                        dict(
                            case=case.id,
                            arm=arm,
                            parity=direct_result == framework_result,
                            outcome=direct_result,
                        )
                    )
            controls = live_controls(store, wrapped, vectors)
            direct_calls = store.calls
        finally:
            client.close()
    return dict(
        protocol="P03-I01-v1",
        retrieval=retrieval,
        compositions=compositions,
        controls=controls,
        sdk_requests=wire,
        direct_store_requests=direct_calls,
        capture_invocations_per_path=sum(
            row["outcome"]["capture_invocations"] for row in compositions
        ),
        embedding_calls=0,
        generation_calls=0,
        api_spend=0,
        packages={
            name: importlib.metadata.version(name)
            for name in ["langchain-core", "langchain-qdrant", "qdrant-client"]
        },
        import_and_validation_seconds=import_seconds,
        elapsed_seconds=time.monotonic() - started,
        decision=(
            "retain direct integration; no demonstrated maintenance benefit "
            "justifies the trial dependencies"
        ),
    )


def main() -> int:
    """Explicit local integration trial; no model initialization or credentials."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--endpoint", default="http://qdrant-e02:6333")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists; no database actions started")
    result = run(args.project_dir, args.endpoint)
    publish(args.output, result)
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in ("retrieval", "compositions")
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
