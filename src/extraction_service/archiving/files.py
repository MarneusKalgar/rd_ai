"""Bounded file handling and publication without replacing existing evidence."""

import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from extraction_service.archiving.models import MAX_FILE_BYTES, safe_path


def digest(path: Path) -> str:
    checksum = hashlib.sha256()

    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            checksum.update(chunk)

    return checksum.hexdigest()


def confined(root: Path, relative: str) -> Path:
    """Reject symlinked components, including a symlink at the owning root."""

    safe_path(relative)
    candidate = root

    for component in ("", *relative.split("/")):
        candidate = candidate / component

        if candidate.is_symlink():
            raise ValueError("Symlinks are not archive evidence")

    return candidate


def regular_bytes(path: Path) -> bytes:
    info = path.lstat()

    if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE_BYTES:
        raise ValueError("Evidence must be a bounded regular file")

    content = path.read_bytes()

    if len(content) != info.st_size:
        raise ValueError("Evidence changed while being read")

    return content


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")

        result[key] = value

    return result


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(regular_bytes(path), object_pairs_hook=_unique_object)

    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")

    return value


def canonical(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()


def publish(source: Path, destination: Path) -> None:
    """Atomically add a file; accept an identical existing copy, never replace it."""

    if destination.is_symlink():
        raise ValueError("Publication destination is a symlink")

    with tempfile.NamedTemporaryFile(dir=destination.parent) as temporary:
        with source.open("rb") as original:
            shutil.copyfileobj(original, temporary)

        temporary.flush()
        os.fsync(temporary.fileno())

        try:
            os.link(temporary.name, destination)
        except FileExistsError:
            if not destination.is_file() or digest(source) != digest(destination):
                raise ValueError("Refuse to overwrite a different existing file") from None
