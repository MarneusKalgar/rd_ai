"""Explicit credential-safe output export, never an inference or Git operation."""

import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Final

from extraction_service.application.persistence import RunState, reload_records
from extraction_service.extraction.constants import SCHEMA_FILENAME

SECRET_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"sk-or-v1-[a-f0-9]{32,}|Bearer\s+[^\s\"]+|-----BEGIN .*PRIVATE KEY-----"
)


def export_run(source: Path, destination: Path) -> dict[str, object]:
    """Revalidate results and copy a unique public bundle with byte hashes.

    The destination is new; partial exports are removed on failure. Budget files,
    application settings and operational server logs are never copied.
    """

    manifest, records = reload_records(source)

    if manifest.state == RunState.RUNNING:
        raise ValueError("Cannot export a run still marked running")

    if destination.exists():
        raise FileExistsError("Export destination already exists")

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir()

    try:
        selected = [Path("manifest.json"), Path(SCHEMA_FILENAME)]
        selected.extend(Path(relative) for relative in manifest.records.values())
        selected.extend(Path("checkpoints") / f"{key}.json" for key in manifest.checkpoint_sha256)
        hashes = {}

        for relative in selected:
            path = source / relative

            if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
                raise ValueError("Export source escapes its run directory")

            content = path.read_bytes()

            if SECRET_PATTERN.search(content.decode("utf-8")):
                raise ValueError("Potential credential material blocks public export")

            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            hashes[relative.as_posix()] = hashlib.sha256(content).hexdigest()

        (destination / "files.sha256.json").write_text(json.dumps(hashes, indent=2) + "\n")
        verify_export(destination)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise

    return {
        "run_id": manifest.run_id,
        "exported_records": len(records),
        "state": manifest.state.value,
    }


def verify_export(directory: Path) -> dict[str, object]:
    """Check every exported byte hash and then reload the operational records."""

    hashes = json.loads((directory / "files.sha256.json").read_bytes())
    expected_files = set(hashes) | {"files.sha256.json"}
    actual_files = {
        path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()
    }

    if expected_files != actual_files:
        raise ValueError("Export file inventory differs")

    for relative, digest in hashes.items():
        path = directory / relative

        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Export path escapes its directory")

        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("Export byte hash mismatch")

    manifest, records = reload_records(directory)

    return {
        "run_id": manifest.run_id,
        "verified_records": len(records),
        "state": manifest.state.value,
    }
