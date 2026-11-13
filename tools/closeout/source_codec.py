"""Preserve known synthetic credential fixtures without weakening archive scanning."""

import base64
import json
import shutil
from pathlib import Path

from extraction_service.archiving.files import confined
from extraction_service.retrieval.core import canonical, digest

# These are reviewed source files containing synthetic fixtures/header templates.
# No wildcard credential exclusion or encoding of unknown flagged files is allowed.
SOURCE_FILES = (
    "src/extraction_service/application/exporting.py",
    "src/extraction_service/inference/transport/http.py",
    "tests/inference/test_client_setup.py",
    "tests/inference/test_requests.py",
    "tests/application/test_archiving.py",
    "tests/application/test_persistence.py",
    "tests/application/test_process.py",
    "tests/application/__init__.py",
    "tests/execution/__init__.py",
    "tests/inference/__init__.py",
    "tests/runtime/__init__.py",
    "src/extraction_service/__init__.py",
    "src/extraction_service/__main__.py",
    "src/extraction_service/answering/__init__.py",
    "src/extraction_service/application/__init__.py",
    "src/extraction_service/archiving/__init__.py",
    "src/extraction_service/archiving/__main__.py",
    "src/extraction_service/configuration/__init__.py",
    "src/extraction_service/corpus/__init__.py",
    "src/extraction_service/corrections/__init__.py",
    "src/extraction_service/corrections/__main__.py",
    "src/extraction_service/diagnostics/__init__.py",
    "src/extraction_service/evaluation/__init__.py",
    "src/extraction_service/execution/__init__.py",
    "src/extraction_service/extraction/__init__.py",
    "src/extraction_service/inference/__init__.py",
    "src/extraction_service/prompting/__init__.py",
    "src/extraction_service/retrieval/__init__.py",
    "src/extraction_service/runtime/__init__.py",
    "src/extraction_service/runtime/__main__.py",
    "src/extraction_service/source_support/__init__.py",
    "src/extraction_service/staged/__init__.py",
    "src/extraction_service/staged/__main__.py",
    "src/extraction_service/inference/ollama/__init__.py",
    "src/extraction_service/inference/openrouter/__init__.py",
    "src/extraction_service/inference/transport/__init__.py",
    "src/extraction_service/execution/budget/__init__.py",
)


def encoded_name(name: str) -> str:
    """Map approved Python module filenames into canonical archive names."""

    path = Path(name)
    if path.name.startswith("__"):
        path = path.with_name("python-" + path.name.lstrip("_"))
    return path.as_posix() + ".base64"


def encode_sources(bundle: Path) -> None:
    """Encode only copied source files; original checkout remains untouched."""

    root = bundle / "workspace"
    previous = bundle / "source-parts.json"
    manifest = json.loads(previous.read_bytes()) if previous.exists() else {}
    if not set(manifest).issubset(SOURCE_FILES):
        raise ValueError("Unexpected prior source membership")
    for name in SOURCE_FILES:
        # Exact compile-time paths only; underscores are deliberately not archive names.
        path = root / name
        target = encoded_name(name)
        if not path.exists() and name in manifest:
            entry = manifest[name]
            data = base64.b64decode(confined(root, target).read_bytes(), validate=True)
            if entry["encoded"] != target or entry["sha256"] != digest(data):
                raise ValueError("Prior encoded source differs")
            continue
        data = path.read_bytes()
        with confined(root, target).open("xb") as output:
            output.write(base64.b64encode(data))
        manifest[name] = {"encoded": target, "sha256": digest(data)}
    (bundle / "source-parts.json").write_bytes(canonical(manifest))
    for name in SOURCE_FILES:
        (root / name).unlink(missing_ok=True)


def decode_sources(bundle: Path, destination: Path) -> Path:
    """Reconstruct a temporary source tree with exact expected files and hashes."""

    manifest = json.loads((bundle / "source-parts.json").read_bytes())
    if set(manifest) != set(SOURCE_FILES):
        raise ValueError("Encoded source membership differs")
    root = destination / "workspace"
    shutil.copytree(bundle / "workspace", root)
    for name, entry in manifest.items():
        if entry["encoded"] != encoded_name(name):
            raise ValueError("Encoded source path differs")
        data = base64.b64decode(confined(root, entry["encoded"]).read_bytes(), validate=True)
        if digest(data) != entry["sha256"]:
            raise ValueError("Decoded source hash differs")
        with (root / name).open("xb") as output:
            output.write(data)
        confined(root, entry["encoded"]).unlink()
    return root
