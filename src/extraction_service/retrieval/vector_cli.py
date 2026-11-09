"""Explicit E02 preparation, CPU encoding and direct Qdrant comparison."""

import argparse
import importlib.metadata
import json
import math
import time
from collections import Counter
from pathlib import Path
from typing import Any

import httpx

from extraction_service.retrieval.cli import load_protocol, publish, relevance_metrics
from extraction_service.retrieval.core import (
    MAX_CONTEXT_BYTES,
    build_snapshot,
    canonical,
    digest,
    read_confined,
)
from extraction_service.retrieval.vector_store import QdrantStore, checked_vector, cosine

PROFILE = "config/retrieval/P03-E02-profile-v1.json"
MODEL_DIRECTORY = "results/embedding-models/minilm"
VECTOR_CACHE = "results/submission/P03-E02-v1/vectors.json"


def load_profile(root: Path) -> dict[str, Any]:
    """Load the pre-download immutable execution profile."""

    profile: dict[str, Any] = json.loads(read_confined(root, PROFILE, 65536))
    if profile["model"] != "sentence-transformers/all-MiniLM-L6-v2":
        raise ValueError("Unsupported encoder profile")
    return profile


def prepare(root: Path) -> dict[str, Any]:
    """Download only pinned neutral model artifacts and verify every digest."""

    profile = load_profile(root)
    directory = root / MODEL_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    downloaded = 0
    with httpx.Client(follow_redirects=True, timeout=30, trust_env=False) as client:
        for name, artifact in profile["files"].items():
            target = directory / name
            if target.exists():
                if digest(read_confined(directory, name, 128 * 1024 * 1024)) != artifact["sha256"]:
                    raise ValueError("Existing model artifact differs; no replacement")
                continue
            url = (
                f"https://huggingface.co/{profile['model']}/resolve/"
                f"{profile['revision']}/{artifact['remote']}"
            )
            data = bytearray()
            with client.stream("GET", url) as response:
                response.raise_for_status()
                for part in response.iter_bytes():
                    if (
                        time.monotonic() - started > 600
                        or len(data) + len(part) > 128 * 1024 * 1024
                    ):
                        raise ValueError("Model download limit exceeded")
                    data.extend(part)
            if digest(bytes(data)) != artifact["sha256"]:
                raise ValueError("Downloaded encoder hash mismatch")
            with target.open("xb") as output:
                output.write(data)
            downloaded += len(data)
    return dict(
        profile=digest(canonical(profile)),
        downloaded_bytes=downloaded,
        elapsed_seconds=time.monotonic() - started,
    )


def inputs(root: Path) -> dict[str, str]:
    """Collect actual chunks and questions without passing relevance labels to encoding."""

    _, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    values: dict[str, str] = {}
    for catalog in {case.catalog for case in cases.cases}:
        for chunk in build_snapshot(root, catalog).chunks:
            values[digest(chunk.text.encode())] = chunk.text
    for case in cases.cases:
        values[digest(case.query.encode())] = case.query
    if len(values) > 104:
        raise ValueError("Encoding population limit exceeded")
    return values


def encode(root: Path) -> dict[str, Any]:
    """Encode at most 104 unique inputs once, with no store or provider access."""

    from extraction_service.retrieval.encoder import SentenceEncoder

    profile = load_profile(root)
    started = time.monotonic()
    encoder = SentenceEncoder(
        root / MODEL_DIRECTORY, {name: item["sha256"] for name, item in profile["files"].items()}
    )
    vectors = {key: encoder.encode(text) for key, text in sorted(inputs(root).items())}
    return dict(
        profile=digest(canonical(profile)),
        vectors=vectors,
        batches=encoder.calls,
        runtime=importlib.metadata.version("onnxruntime"),
        numpy=importlib.metadata.version("numpy"),
        encoder_source=digest(Path(__file__).with_name("encoder.py").read_bytes()),
        elapsed_seconds=time.monotonic() - started,
    )


def load_vectors(root: Path) -> dict[str, list[float]]:
    """Revalidate saved encoding membership and identities before any store query."""

    manifest_path = "config/retrieval/P03-E02-v1.json"
    manifest = json.loads(read_confined(root, manifest_path, 65536))
    for path, expected in manifest["bindings"].items():
        limit = 32 * 1024 * 1024 if path == VECTOR_CACHE else 1024 * 1024
        if digest(read_confined(root, path, limit)) != expected:
            raise ValueError("E02 artifact binding mismatch")
    required = {
        VECTOR_CACHE,
        PROFILE,
        "uv.lock",
        "config/retrieval/P03-E01-v3.json",
        "src/extraction_service/retrieval/vector_cli.py",
        "src/extraction_service/retrieval/vector_store.py",
        "src/extraction_service/retrieval/encoder.py",
    }
    if not required.issubset(manifest["bindings"]):
        raise ValueError("Missing E02 artifact bindings")
    cache = json.loads(read_confined(root, VECTOR_CACHE, 32 * 1024 * 1024))
    if cache["profile"] != digest(canonical(load_profile(root))):
        raise ValueError("Embedding profile mismatch")
    if cache["encoder_source"] != digest(Path(__file__).with_name("encoder.py").read_bytes()):
        raise ValueError("Encoder implementation mismatch")
    if set(cache["vectors"]) != set(inputs(root)):
        raise ValueError("Embedding population mismatch")
    return {key: checked_vector(value) for key, value in cache["vectors"].items()}


def evaluate(root: Path, endpoint: str, run_id: str, *, reload: bool = False) -> dict[str, Any]:
    """Run all forty scoped queries against real Qdrant with independent exact oracles."""

    if not run_id.isalnum() or len(run_id) > 32:
        raise ValueError("Invalid vector run identity")
    vectors = load_vectors(root)
    protocol, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    outcomes: list[dict[str, Any]] = []
    collections: set[str] = set()
    started = time.monotonic()
    with httpx.Client(base_url=endpoint.rstrip("/") + "/", trust_env=False) as client:
        store = QdrantStore(client)
        metadata = client.get("", timeout=5)
        metadata.raise_for_status()
        server_version = metadata.json()["version"]
        if server_version != load_profile(root)["qdrant_version"]:
            raise ValueError("Qdrant server identity mismatch")
        for case in cases.cases:
            snapshot = build_snapshot(root, case.catalog)
            identity = digest(
                canonical(dict(snapshot=snapshot.model_dump(), time=case.effective_time))
            )
            collection = "p03_" + run_id + "_" + identity[:16]
            if collection not in collections:
                if not reload:
                    store.create(collection)
                    points = []
                    for index, chunk in enumerate(snapshot.chunks):
                        ref = chunk.reference
                        eligible = (
                            ref.status == "active"
                            and ref.effective_from <= case.effective_time
                            and (
                                ref.effective_until is None
                                or case.effective_time < ref.effective_until
                            )
                        )
                        points.append(
                            dict(
                                id=index,
                                vector=vectors[ref.sha256],
                                payload=dict(
                                    scope=ref.scope,
                                    snapshot=identity,
                                    eligible=eligible,
                                    source_id=ref.id,
                                    revision=ref.revision,
                                    sha256=ref.sha256,
                                ),
                            )
                        )
                    store.upsert(collection, points)
                collections.add(collection)
            query_vector = vectors[digest(case.query.encode())]
            query_started = time.monotonic()
            try:
                found = store.query(collection, query_vector, scope=case.scope, snapshot=identity)
                if build_snapshot(root, case.catalog) != snapshot:
                    raise ValueError("Source authority changed during vector search")
                eligible_chunks = {}
                for index, chunk in enumerate(snapshot.chunks):
                    ref = chunk.reference
                    if (
                        ref.scope in ("shared", case.scope)
                        and ref.status == "active"
                        and ref.effective_from <= case.effective_time
                        and (
                            ref.effective_until is None or case.effective_time < ref.effective_until
                        )
                    ):
                        eligible_chunks[index] = chunk
                # Reject all returned ineligible IDs before loading any source bytes into context.
                if {point["id"] for point in found} != set(eligible_chunks):
                    raise ValueError("Vector result eligibility or completeness mismatch")
                oracle = {
                    index: cosine(query_vector, vectors[chunk.reference.sha256])
                    for index, chunk in eligible_chunks.items()
                }
                for point in found:
                    if not math.isclose(point["score"], oracle[point["id"]], abs_tol=2e-6):
                        raise ValueError("Exact similarity oracle mismatch")
                actual_scores = {point["id"]: point["score"] for point in found}
                ordered = sorted(
                    actual_scores,
                    key=lambda index: (
                        -round(actual_scores[index], 6),
                        eligible_chunks[index].reference.id,
                        eligible_chunks[index].reference.revision,
                    ),
                )
                selected = ordered[:3]
                quotes: list[dict[str, Any]] = []
                ids = []
                for index in selected:
                    chunk = eligible_chunks[index]
                    ref = chunk.reference
                    ids.append(
                        ref.id
                        + ("@" + ref.revision if any("@" in x for x in case.relevant) else "")
                    )
                    quotes.append(
                        dict(
                            source_id=ref.id,
                            revision=ref.revision,
                            sha256=ref.sha256,
                            start=0,
                            end=chunk.end,
                            quote=chunk.text,
                            score=actual_scores[index],
                        )
                    )
                if sum(len(item["quote"].encode()) for item in quotes) > MAX_CONTEXT_BYTES:
                    raise ValueError("Vector context limit exceeded")
                counts = Counter(
                    chunk.reference.exclusive_key for chunk in eligible_chunks.values()
                )
                conflict = any(
                    counts[eligible_chunks[index].reference.exclusive_key] > 1 for index in selected
                )
                recall, precision, rr = relevance_metrics(ids, set(case.relevant))
                outcomes.append(
                    dict(
                        case=case.id,
                        group=case.group,
                        status=(
                            "conflicting_evidence"
                            if conflict
                            else "evidence_found"
                            if quotes
                            else "insufficient_evidence"
                        ),
                        hits=quotes,
                        recall=recall,
                        precision=precision,
                        reciprocal_rank=rr,
                        exact_oracle_passed=True,
                        elapsed_seconds=time.monotonic() - query_started,
                    )
                )
            except (ValueError, httpx.HTTPError) as error:
                outcomes.append(
                    dict(
                        case=case.id,
                        group=case.group,
                        status="failed",
                        error=type(error).__name__,
                        recall=0 if case.relevant else None,
                        precision=0,
                        reciprocal_rank=0,
                        elapsed_seconds=time.monotonic() - query_started,
                    )
                )
        calls = store.calls
    scored = [item for item in outcomes if item["recall"] is not None]
    return dict(
        protocol="P03-E02-v1",
        inherited_protocol=protocol.id,
        run_id=run_id,
        reload=reload,
        profile=digest(canonical(load_profile(root))),
        implementation=digest(Path(__file__).read_bytes()),
        vector_cache_sha256=digest(read_confined(root, VECTOR_CACHE, 32 * 1024 * 1024)),
        server_version=server_version,
        outcomes=outcomes,
        macro_recall_at_3=sum(item["recall"] for item in scored) / len(scored),
        macro_precision_at_3=sum(item["precision"] for item in scored) / len(scored),
        mrr=sum(item["reciprocal_rank"] for item in scored) / len(scored),
        store_calls=calls,
        collections=sorted(collections),
        generation_calls=0,
        api_spend=0,
        elapsed_seconds=time.monotonic() - started,
    )


def lifecycle(root: Path, endpoint: str, run_id: str) -> dict[str, Any]:
    """Exercise real update, revocation, cross-scope bait and deletion operations."""

    if not run_id.isalnum():
        raise ValueError("Invalid control run identity")
    cache = list(load_vectors(root).values())
    collection = "p03_control_" + run_id

    def point(
        identifier: int,
        scope: str,
        vector: list[float],
        *,
        eligible: bool = True,
        snapshot: str = "current",
    ) -> dict[str, Any]:
        return dict(
            id=identifier,
            vector=vector,
            payload=dict(scope=scope, snapshot=snapshot, eligible=eligible),
        )

    with httpx.Client(base_url=endpoint.rstrip("/") + "/", trust_env=False) as client:
        store = QdrantStore(client)
        store.create(collection)
        store.upsert(collection, [point(0, "A", cache[0]), point(1, "B", cache[0])])
        for scope, expected in [("A", {0}), ("B", {1})]:
            result = store.query(collection, cache[0], scope=scope, snapshot="current")
            if {item["id"] for item in result} != expected:
                raise ValueError("Cross-scope bait control failed")
        store.upsert(collection, [point(0, "A", cache[0], eligible=False)])
        if store.query(collection, cache[0], scope="A", snapshot="current"):
            raise ValueError("Revocation control failed")
        store.upsert(collection, [point(0, "A", cache[0], snapshot="superseded")])
        if store.query(collection, cache[0], scope="A", snapshot="current"):
            raise ValueError("Currentness control failed")
        store.upsert(collection, [point(0, "A", cache[1])])
        updated = store.query(collection, cache[0], scope="A", snapshot="current")
        if len(updated) != 1 or not math.isclose(
            updated[0]["score"], cosine(cache[0], cache[1]), abs_tol=2e-6
        ):
            raise ValueError("Vector update control failed")
        store.delete_points(collection, [0])
        if store.query(collection, cache[0], scope="A", snapshot="current"):
            raise ValueError("Deletion control failed")
        return dict(
            collection=collection,
            store_calls=store.calls,
            controls_passed=True,
            controls=["scope A/B bait", "revocation", "currentness", "update", "deletion"],
        )


def main() -> int:
    """Run only the explicitly selected E02 phase."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "encode", "evaluate", "reload", "lifecycle"])
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--endpoint", default="http://qdrant-e02:6333")
    parser.add_argument("--run-id", default="e02v1")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise ValueError("Output already exists; no encoding or database action started")
    if args.command == "prepare":
        result = prepare(args.project_dir)
    elif args.command == "encode":
        result = encode(args.project_dir)
    elif args.command == "lifecycle":
        result = lifecycle(args.project_dir, args.endpoint, args.run_id)
    else:
        result = evaluate(
            args.project_dir, args.endpoint, args.run_id, reload=args.command == "reload"
        )
    if args.output:
        publish(args.output, result)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
