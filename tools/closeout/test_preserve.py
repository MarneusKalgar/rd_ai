"""Recovery compares original semantics and rejects corrupted encoder artifacts."""

import base64
import copy
import json
from pathlib import Path
from typing import Any

import pytest
from preserve import compare_queries, recover_encoder
from source_codec import SOURCE_FILES, decode_sources, encode_sources, encoded_name

from extraction_service.retrieval.core import digest


def test_query_recovery_allows_only_timing_and_float_roundoff() -> None:
    original: dict[str, Any] = {
        "outcomes": [
            {
                "case": f"Q{i:02}",
                "status": "evidence_found",
                "exact_oracle_passed": True,
                "elapsed_seconds": 1,
                "hits": [{"source_id": "fixture", "score": 0.5}],
            }
            for i in range(40)
        ]
    }
    restored = copy.deepcopy(original)
    restored["outcomes"][0]["elapsed_seconds"] = 99
    restored["outcomes"][0]["hits"][0]["score"] += 1e-7

    compare_queries(original, restored)

    # The original report may omit scores; reload still verifies the cosine oracle.
    without_scores = copy.deepcopy(original)
    for row in without_scores["outcomes"]:
        for hit in row["hits"]:
            hit.pop("score")
    compare_queries(without_scores, restored)

    restored["outcomes"][0]["hits"][0]["source_id"] = "wrong-source"
    with pytest.raises(ValueError, match="outcomes differ"):
        compare_queries(original, restored)
    with pytest.raises(ValueError, match="population differs"):
        compare_queries(original, {"outcomes": restored["outcomes"][:-1]})


def test_encoder_recovery_rejects_altered_parts_and_traversal(tmp_path: Path) -> None:
    data = b"bounded fixture model"
    profile = {
        "model": "sentence-transformers/all-MiniLM-L6-v2",
        "files": {"model.onnx": {"sha256": digest(data)}},
    }
    config = tmp_path / "workspace/config/retrieval"
    config.mkdir(parents=True)
    (config / "P03-E02-profile-v1.json").write_text(json.dumps(profile))
    part = tmp_path / "encoder/part.base64"
    part.parent.mkdir()
    part.write_bytes(base64.b64encode(data))
    manifest = {
        "model.onnx": {"sha256": digest(data), "size": len(data), "parts": ["encoder/part.base64"]}
    }
    path = tmp_path / "encoder-parts.json"
    path.write_text(json.dumps(manifest))
    destination = tmp_path / "decoded"
    destination.mkdir()

    count = recover_encoder(tmp_path, destination)

    assert count == len(data)
    assert (destination / "model.onnx").read_bytes() == data
    part.write_bytes(base64.b64encode(b"corrupt"))
    with pytest.raises(ValueError, match="digest differs"):
        recover_encoder(tmp_path, destination)
    manifest["model.onnx"]["parts"] = ["../outside.base64"]
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError):
        recover_encoder(tmp_path, destination)


def test_source_encoding_round_trip_and_corruption(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    for name in SOURCE_FILES:
        path = bundle / "workspace" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic fixture source")

    encode_sources(bundle)
    restored = decode_sources(bundle, tmp_path / "restored")

    for name in SOURCE_FILES:
        assert (restored / name).read_bytes() == b"synthetic fixture source"
        assert not (restored / encoded_name(name)).exists()
        assert not (bundle / "workspace" / name).exists()
    part = bundle / "workspace" / encoded_name(SOURCE_FILES[0])
    part.write_bytes(base64.b64encode(b"corrupt"))
    with pytest.raises(ValueError, match="Decoded source hash differs"):
        decode_sources(bundle, tmp_path / "corrupt")
