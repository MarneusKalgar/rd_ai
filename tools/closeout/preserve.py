"""Copy-only P03 preservation, portable encoder recovery and real store reload."""

import argparse
import base64
import json
import math
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

import httpx

from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import confined, regular_bytes
from extraction_service.retrieval.core import canonical, digest
from extraction_service.retrieval.vector_cli import evaluate, lifecycle, load_profile
from extraction_service.retrieval.vector_store import QdrantStore, checked_vector

ROOT = Path("/workspace")
OUTPUT = Path("/preservation")
BUNDLES = ("P03-E01-v3", "P03-E02-v1", "P03-I01-v1", "P03-E03-v1", "P03-S08-v1")


def save(path: Path, value: Any) -> None:
    """Publish new evidence or accept an identical reconstruction only."""

    content = canonical(value)
    if path.exists():
        if path.read_bytes() != content:
            raise ValueError(f"Conflicting preservation artifact: {path.name}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def export_store(root: Path, output: Path) -> None:
    """Read only the original E02 collections; export vectors and complete payloads."""

    saved = json.loads((root / "results/submission/P03-E02-v1/report.json").read_bytes())
    exported = {}
    with httpx.Client(base_url="http://qdrant-e02:6333/", trust_env=False) as client:
        store = QdrantStore(client)
        version = client.get("", timeout=5).json()["version"]
        if version != load_profile(root)["qdrant_version"]:
            raise ValueError("Original store version differs")
        for name in saved["collections"]:
            result = store.request(
                "POST",
                f"collections/{name}/points/scroll",
                {
                    "limit": 64,
                    "with_payload": True,
                    "with_vector": True,
                },
            )
            if result["next_page_offset"] is not None or not result["points"]:
                raise ValueError("Store export incomplete or empty")
            points = result["points"]
            for point in points:
                checked_vector(point["vector"])
            exported[name] = points
    save(output / "store-export.json", {"version": version, "collections": exported})


def compare_queries(original: dict[str, Any], restored: dict[str, Any]) -> None:
    """Compare all original outcomes; only timings and float roundoff may differ."""

    if len(original["outcomes"]) != 40 or len(restored["outcomes"]) != 40:
        raise ValueError("Reload population differs")
    for left, right in zip(original["outcomes"], restored["outcomes"], strict=True):
        for row in (left, right):
            if row["status"] == "failed" or not row["exact_oracle_passed"]:
                raise ValueError("Reload oracle failed")
        a, b = dict(left), dict(right)
        a.pop("elapsed_seconds")
        b.pop("elapsed_seconds")
        for hits in (a, b):
            hits["hits"] = [dict(hit) for hit in hits["hits"]]
        for first, second in zip(a["hits"], b["hits"], strict=True):
            expected_score = first.pop("score", None)
            actual_score = second.pop("score", None)
            if expected_score is not None and (
                actual_score is None or not math.isclose(expected_score, actual_score, abs_tol=2e-6)
            ):
                raise ValueError("Reload scores differ")
        if a != b:
            raise ValueError("Reload outcomes differ")


def restore_store(root: Path, output: Path, *, reload: bool) -> None:
    """Recover only into the dedicated S09 store, never the original endpoint."""

    exported = json.loads((output / "store-export.json").read_bytes())
    endpoint = "http://qdrant-s09-restored:6333/"
    with httpx.Client(base_url=endpoint, trust_env=False) as client:
        if client.get("", timeout=5).json()["version"] != exported["version"]:
            raise ValueError("Recovery store version differs")
        store = QdrantStore(client)
        if not reload:
            existing = {item["name"] for item in store.request("GET", "collections")["collections"]}
            if existing and existing != set(exported["collections"]):
                raise ValueError("Recovery store contains unexpected collections")
            for name, points in exported["collections"].items():
                if not existing:
                    store.create(name)
                    store.upsert(name, points)
                else:
                    saved_points = store.request(
                        "POST",
                        f"collections/{name}/points/scroll",
                        {
                            "limit": 64,
                            "with_payload": True,
                            "with_vector": True,
                        },
                    )
                    if saved_points["next_page_offset"] is not None:
                        raise ValueError("Partial interrupted recovery")
                    actual_points = {point["id"]: point for point in saved_points["points"]}
                    if set(actual_points) != {point["id"] for point in points}:
                        raise ValueError("Interrupted recovery membership differs")
                    for point in points:
                        actual = actual_points[point["id"]]
                        if actual["payload"] != point["payload"] or any(
                            not math.isclose(a, b, abs_tol=2e-6)
                            for a, b in zip(actual["vector"], point["vector"], strict=True)
                        ):
                            raise ValueError("Interrupted recovery point differs")
    with tempfile.TemporaryDirectory() as directory:
        shadow = Path(directory)
        # E02 predates the optional I01 dependency group; preserve its original lock.
        for name in ("src", "tests", "config", "data", "schemas", "docs"):
            shutil.copytree(root / name, shadow / name, ignore=shutil.ignore_patterns("private"))
        vectors = Path("results/submission/P03-E02-v1/vectors.json")
        (shadow / vectors).parent.mkdir(parents=True)
        shutil.copyfile(root / vectors, shadow / vectors)
        for name in ("compose.yaml", "uv.lock", "pyproject.toml"):
            source = (
                root / name
                if name == "compose.yaml"
                else (root / "config/retrieval/I01-inherited-runtime" / name)
            )
            shutil.copyfile(source, shadow / name)
        actual = evaluate(shadow, endpoint, "e02v1", reload=True)
        original = json.loads((root / "results/submission/P03-E02-v1/report.json").read_bytes())
        compare_queries(original, actual)
        control = None if reload else lifecycle(shadow, endpoint, "s09v1")
    save(
        output / ("store-restarted.json" if reload else "store-restored.json"),
        {
            "queries_verified": 40,
            "export_sha256": digest((output / "store-export.json").read_bytes()),
            "version": exported["version"],
            "controls": control,
            "new_encoding_calls": 0,
            "generation_calls": 0,
        },
    )


def snapshot(root: Path, output: Path) -> None:
    """Freeze public source/evidence and encode binary weights into bounded text parts."""

    target = output / "workspace"
    if target.exists():
        raise ValueError("Snapshot exists; do not replace evidence")
    target.mkdir()
    for name in ("src", "tests", "config", "data", "schemas", "prompts", "docs"):
        shutil.copytree(root / name, target / name, ignore=shutil.ignore_patterns("private"))
    for name in (
        "Dockerfile",
        "Makefile",
        "README.md",
        "REPORT.md",
        "pyproject.toml",
        "uv.lock",
        "AGENTS.md",
    ):
        shutil.copyfile(root / name, target / name)
    for path in root.glob("compose*.yaml"):
        shutil.copyfile(path, target / path.name)
    for name in ("answer-evaluation", "answer-recovery", "answer-continuation", "closeout"):
        shutil.copytree(root / "tools" / name, target / "tools" / name)
    for name in BUNDLES:
        shutil.copytree(root / "results/submission" / name, target / "results/submission" / name)
    model_manifest = {}
    for name, artifact in load_profile(root)["files"].items():
        data = (root / "results/embedding-models/minilm" / name).read_bytes()
        if digest(data) != artifact["sha256"]:
            raise ValueError("Encoder artifact differs")
        parts = []
        for index, start in enumerate(range(0, len(data), 24 * 1024 * 1024)):
            part = f"encoder/{name}.{index:03}.base64"
            destination = output / part
            destination.parent.mkdir(exist_ok=True)
            destination.write_bytes(base64.b64encode(data[start : start + 24 * 1024 * 1024]))
            parts.append(part)
        model_manifest[name] = {"sha256": digest(data), "size": len(data), "parts": parts}
    save(output / "encoder-parts.json", model_manifest)
    from source_codec import encode_sources

    encode_sources(output)


def recover_encoder(output: Path, destination: Path) -> int:
    """Recover exact encoder bytes from bounded text parts, checking frozen digests."""

    manifest = json.loads((output / "encoder-parts.json").read_bytes())
    profile = load_profile(output / "workspace")
    if set(manifest) != set(profile["files"]):
        raise ValueError("Encoder file membership differs")
    total = 0
    for name, entry in manifest.items():
        if not 1 <= len(entry["parts"]) <= 6:
            raise ValueError("Encoder part count exceeds bound")
        data = b"".join(
            base64.b64decode(regular_bytes(confined(output, part)), validate=True)
            for part in entry["parts"]
        )
        if digest(data) != entry["sha256"] or digest(data) != profile["files"][name]["sha256"]:
            raise ValueError("Restored encoder digest differs")
        if len(data) != entry["size"]:
            raise ValueError("Restored encoder size differs")
        (destination / name).write_bytes(data)
        total += len(data)
    return total


def reproduce(root: Path) -> dict[str, Any]:
    """Rebuild lexical, I01, E03 and S08 results without ledger or model access."""

    from extraction_service.retrieval.cli import evaluate as lexical
    from extraction_service.retrieval.cli import load_protocol
    from extraction_service.retrieval.integration_reproduce import reproduce as integration

    protocol, cases = load_protocol(root, "config/retrieval/P03-E01-v3.json")
    current = lexical(root, protocol, cases)
    saved = json.loads((root / "results/submission/P03-E01-v3/report.json").read_bytes())
    for value in (current, saved):
        value.pop("elapsed_seconds", None)
        for row in value["outcomes"]:
            row.pop("elapsed_seconds", None)
    if saved != current:
        raise ValueError("Lexical reproduction differs")
    relative = "results/submission/P03-I01-v1/report.json"
    i01 = integration(root, relative, digest((root / relative).read_bytes()))
    sys.path.insert(0, str(root / "tools/answer-evaluation"))
    import judge
    import judge_continue
    import prepare
    from improvement import improvement
    from overall_reviews import finalize
    from replay import replay

    evidence = root / "results/submission/P03-E03-v1"
    review = root / "results/submission/P03-S08-v1"
    judge.RUNNER = review / "judge-v1"
    # This imported module constant exists at runtime but is not a mypy re-export.
    judge.EVIDENCE = evidence  # type: ignore[attr-defined]
    judge.OUTPUT = review  # type: ignore[attr-defined]
    judge_continue.ADDENDUM = judge.RUNNER / "continuation-R01.json"
    prepare.EVIDENCE = evidence
    manifest = judge_continue.verify(root)
    grades = json.loads((judge.RUNNER / "provisional-summary-R01.json").read_bytes())["rows"]
    for entry, grade in zip(manifest["jobs"], grades, strict=True):
        directory = judge.RUNNER / entry["directory"]
        checked = judge_continue.checked_result(
            directory, json.loads((directory / "bundle.json").read_bytes())
        )
        if dict(checked, status="valid_provisional") != grade:
            raise ValueError("Saved judge record differs")
    jobs, outcomes, _ = prepare.load_population(root, evidence)
    by_id = {row["id"]: row for row in grades}
    paired = [
        {
            "key": job.key,
            "operational_outcome": outcomes[job.key]["outcome"],
            "answer_status": (outcomes[job.key].get("answer") or {}).get("status", "absent"),
            "semantic_review": by_id.get(digest(job.key.encode())[:16], {"status": "unreviewed"}),
        }
        for job in jobs
    ]
    case_map = {case.id: case.model_dump() for case in cases.cases}
    metrics = improvement(paired, case_map)
    published = json.loads((root / "docs/reports/P03-evaluation-summary.json").read_bytes())
    if metrics != published["improvement_metrics"]:
        raise ValueError("Published improvement differs")
    human = finalize(review)
    if human != json.loads((review / "human-overall-review.json").read_bytes()):
        raise ValueError("Human review differs")
    actual = replay(root, evidence)
    return {
        "lexical_queries": 40,
        "i01": i01,
        "e03_jobs": len(jobs),
        "judge_records": len(grades),
        "human_items": human["coverage"],
        "actual_response_parity": actual["parity"],
        "replay_jobs": actual["jobs"],
        "improvement_metrics_verified": True,
        "ledger_access": False,
        "new_model_calls": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["export", "restore", "reload", "snapshot", "verify", "seal"]
    )
    parser.add_argument("--bundle", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.command == "export":
        export_store(ROOT, OUTPUT)
    elif args.command in ("restore", "reload"):
        restore_store(ROOT, OUTPUT, reload=args.command == "reload")
    elif args.command == "snapshot":
        snapshot(ROOT, OUTPUT)
    elif args.command == "verify":
        from source_codec import decode_sources

        with tempfile.TemporaryDirectory() as directory:
            count = recover_encoder(args.bundle, Path(directory))
            recovered = decode_sources(args.bundle, Path(directory))
            result = reproduce(recovered)
        save(OUTPUT / "reproduction.json", {**result, "encoder_bytes_recovered": count})
        print(json.dumps(result))
    else:
        inventory = {
            path.relative_to(OUTPUT).as_posix(): digest(path.read_bytes())
            for path in sorted(OUTPUT.rglob("*"))
            if path.is_file() and path.name != "files.sha256.json"
        }
        # Nested source inventories remain payload; only the root inventory is excluded.
        inventory.update(
            {
                path.relative_to(OUTPUT).as_posix(): digest(path.read_bytes())
                for path in OUTPUT.glob("workspace/**/files.sha256.json")
            }
        )
        save(OUTPUT / "files.sha256.json", inventory)
        bundle = verify_bundle(OUTPUT)
        print(bundle.model_dump_json())


if __name__ == "__main__":
    main()
