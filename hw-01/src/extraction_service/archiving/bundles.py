"""Validate exact public bundle inventories before packaging or after restoration."""

import hashlib
import stat
from pathlib import Path
from typing import Literal

from extraction_service.application.exporting import SECRET_PATTERN, verify_export
from extraction_service.archiving.files import confined, digest, read_json, regular_bytes
from extraction_service.archiving.models import BundleInfo, safe_path


def verify_bundle(directory: Path) -> BundleInfo:
    """Keep every original payload byte, including failed attempts and checkpoints."""

    if directory.is_symlink():
        raise ValueError("Bundle root must not be a symlink")

    inventory_path = confined(directory, "files.sha256.json")
    inventory = read_json(inventory_path)
    actual = set()

    for path in directory.rglob("*"):
        mode = path.lstat().st_mode

        if stat.S_ISDIR(mode):
            continue

        if not stat.S_ISREG(mode):
            raise ValueError("Bundle contains a link or special file")

        actual.add(path.relative_to(directory).as_posix())

    if not inventory or actual != set(inventory) | {"files.sha256.json"}:
        raise ValueError("Bundle file inventory differs")

    for relative, expected in inventory.items():
        safe_path(relative)
        path = confined(directory, relative)
        content = regular_bytes(path)

        if not isinstance(expected, str) or hashlib.sha256(content).hexdigest() != expected:
            raise ValueError("Bundle payload checksum differs")

        if path.name.startswith(".env") or path.name == "budget-ledger.json":
            raise ValueError("Private settings/accounting files cannot enter a public archive")

        if SECRET_PATTERN.search(content.decode("utf-8")):
            raise ValueError("Potential credential material blocks archiving")

    kind: Literal["run", "evidence"] = "run" if "manifest.json" in inventory else "evidence"

    if kind == "run":
        verify_export(directory)

    return BundleInfo(
        name=directory.name,
        kind=kind,
        inventory_sha256=digest(inventory_path),
        payload_files=len(actual),
    )
