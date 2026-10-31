"""Versioned archive metadata; payload hashes remain inside the archive."""

import hashlib
import re
from pathlib import PurePosixPath
from typing import Final, Literal, Self

from pydantic import Field, field_validator, model_validator

from extraction_service.runtime_types import NonNegativeInt, Sha256, StrictModel

MAX_FILES: Final[int] = 10_000
MAX_BYTES: Final[int] = 512 * 1024 * 1024
MAX_FILE_BYTES: Final[int] = 64 * 1024 * 1024
MAX_MANIFEST_BYTES: Final[int] = 8 * 1024 * 1024
NAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


def safe_path(value: str) -> str:
    """Accept canonical ASCII relative paths, without links or traversal aliases."""

    parts = value.split("/")

    if not parts or any(part in (".", "..") or not NAME_PATTERN.fullmatch(part) for part in parts):
        raise ValueError("Archive paths must be canonical relative paths")

    if PurePosixPath(value).as_posix() != value:
        raise ValueError("Archive path alias")

    return value


def safe_name(value: str) -> str:
    safe_path(value)

    if "/" in value:
        raise ValueError("Bundle names must have one component")

    return value


class BundleInfo(StrictModel):
    name: str
    kind: Literal["run", "evidence"]
    inventory_sha256: Sha256
    payload_files: int = Field(ge=1, le=MAX_FILES)

    _name = field_validator("name")(safe_name)


class ArchiveFile(StrictModel):
    path: str
    sha256: Sha256
    size: int = Field(ge=0, le=MAX_FILE_BYTES)

    _path = field_validator("path")(safe_path)


class ArchiveManifest(StrictModel):
    version: Literal["hw01-archive-manifest-v1"] = "hw01-archive-manifest-v1"
    selection: str
    membership_sha256: Sha256
    membership_json: str
    evidence_index_sha256: Sha256 | None = None
    bundles: tuple[BundleInfo, ...] = Field(min_length=1, max_length=MAX_FILES)
    files: tuple[ArchiveFile, ...] = Field(min_length=1, max_length=MAX_FILES)

    @model_validator(mode="after")
    def check_inventory(self) -> Self:
        if hashlib.sha256(self.membership_json.encode()).hexdigest() != self.membership_sha256:
            raise ValueError("Membership snapshot checksum differs")

        names = {bundle.name for bundle in self.bundles}
        file_names = {file.path for file in self.files}

        if len(names) != len(self.bundles) or len(file_names) != len(self.files):
            raise ValueError("Duplicate archive member or bundle")

        for file in self.files:
            parts = file.path.split("/")

            if len(parts) < 3 or parts[0] != "submission" or parts[1] not in names:
                raise ValueError("Payload is outside the selected bundles")

        if sum(file.size for file in self.files) > MAX_BYTES:
            raise ValueError("Archive expanded size exceeds limit")

        return self


class ArchiveIndex(StrictModel):
    version: Literal["hw01-archive-index-v1"] = "hw01-archive-index-v1"
    archive_sha256: Sha256
    archive_size: int = Field(gt=0, le=MAX_BYTES)
    manifest_sha256: Sha256
    object_key: str
    selection: str
    membership_sha256: Sha256
    bundles: tuple[BundleInfo, ...] = Field(min_length=1, max_length=MAX_FILES)
    covered_observations: NonNegativeInt

    @model_validator(mode="after")
    def check_key(self) -> Self:
        if self.object_key != f"hw01/archives/sha256/{self.archive_sha256}.tar.gz":
            raise ValueError("Object key must match the archive checksum")

        return self
