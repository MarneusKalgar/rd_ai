"""Vector provenance controls reject both byte tampering and invalid bound contents."""

import json
from pathlib import Path

import pytest

from extraction_service.retrieval import vector_cli
from extraction_service.retrieval.core import canonical, digest


@pytest.fixture
def bound_vectors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    profile = json.loads(Path(vector_cli.PROFILE).read_bytes())
    key = digest(b"query")
    cache = dict(
        profile=digest(canonical(profile)),
        vectors={key: [1.0] + [0.0] * 383},
        encoder_source=digest(Path(vector_cli.__file__).with_name("encoder.py").read_bytes()),
    )
    files = {
        vector_cli.PROFILE: canonical(profile),
        vector_cli.VECTOR_CACHE: canonical(cache),
        "uv.lock": b"fixture lock",
        "config/retrieval/P03-E01-v3.json": b"fixture identity",
        "src/extraction_service/retrieval/vector_cli.py": b"driver fixture",
        "src/extraction_service/retrieval/vector_store.py": b"store fixture",
        "src/extraction_service/retrieval/encoder.py": b"encoder fixture",
    }
    for relative, data in files.items():
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest = dict(bindings={key: digest(value) for key, value in files.items()})
    (tmp_path / "config/retrieval/P03-E02-v1.json").write_bytes(canonical(manifest))
    monkeypatch.setattr(vector_cli, "inputs", lambda root: {key: "query"})
    return tmp_path


def test_valid_bound_vectors(bound_vectors: Path) -> None:
    result = vector_cli.load_vectors(bound_vectors)

    assert result == {digest(b"query"): [1.0] + [0.0] * 383}


def test_changed_vector_bytes_fail_before_use(bound_vectors: Path) -> None:
    path = bound_vectors / vector_cli.VECTOR_CACHE
    path.write_bytes(path.read_bytes() + b" ")

    with pytest.raises(ValueError, match="artifact binding mismatch"):
        vector_cli.load_vectors(bound_vectors)


def test_missing_required_binding(bound_vectors: Path) -> None:
    path = bound_vectors / "config/retrieval/P03-E02-v1.json"
    manifest = json.loads(path.read_bytes())
    del manifest["bindings"][vector_cli.VECTOR_CACHE]
    path.write_bytes(canonical(manifest))

    with pytest.raises(ValueError, match="Missing E02 artifact bindings"):
        vector_cli.load_vectors(bound_vectors)


@pytest.mark.parametrize(
    "defect,expected",
    [
        ("population", "population mismatch"),
        ("profile", "profile mismatch"),
        ("implementation", "implementation mismatch"),
        ("dimension", "dimension mismatch"),
        ("zero", "Zero vector"),
    ],
)
def test_hash_valid_but_invalid_embedding_data(
    bound_vectors: Path, defect: str, expected: str
) -> None:
    path = bound_vectors / vector_cli.VECTOR_CACHE
    cache = json.loads(path.read_bytes())
    if defect == "population":
        cache["vectors"] = {}
    elif defect == "profile":
        cache["profile"] = "wrong"
    elif defect == "implementation":
        cache["encoder_source"] = "wrong"
    else:
        cache["vectors"][digest(b"query")] = [1.0] if defect == "dimension" else [0.0] * 384
    path.write_bytes(canonical(cache))
    manifest_path = bound_vectors / "config/retrieval/P03-E02-v1.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["bindings"][vector_cli.VECTOR_CACHE] = digest(path.read_bytes())
    manifest_path.write_bytes(canonical(manifest))

    with pytest.raises(ValueError, match=expected):
        vector_cli.load_vectors(bound_vectors)
