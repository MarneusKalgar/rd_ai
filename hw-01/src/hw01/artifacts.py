"""Read checked artifacts and resolve paths within their owning project area."""

import hashlib
from pathlib import Path


class ArtifactError(ValueError):
    """A required artifact cannot be trusted or read."""


def artifact_path(root: Path, relative_path: str) -> Path:
    """Resolve a relative artifact path without permitting directory escape."""

    candidate = Path(relative_path)
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()

    if candidate.is_absolute() or not resolved.is_relative_to(resolved_root):
        raise ArtifactError("Artifact path must stay within its owning directory")

    return resolved


def read_text(path: Path) -> str:
    """Read UTF-8 bytes without newline translation, reporting file failures."""

    try:
        return path.read_bytes().decode("utf-8")
    except (OSError, UnicodeError) as error:
        raise ArtifactError(f"Cannot read UTF-8 artifact: {path}") from error


def read_checked(path: Path, expected_sha256: str) -> str:
    """Verify original artifact bytes before decoding UTF-8 text."""

    try:
        data = path.read_bytes()
    except OSError as error:
        raise ArtifactError(f"Cannot read approved artifact: {path}") from error

    actual_sha256 = hashlib.sha256(data).hexdigest()

    if actual_sha256 != expected_sha256:
        raise ArtifactError(f"Approved artifact hash mismatch: {path}")

    try:
        return data.decode("utf-8")
    except UnicodeError as error:
        raise ArtifactError(f"Approved artifact is not UTF-8: {path}") from error
