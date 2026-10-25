"""Deterministic copy-only archives and bounded verification before installation."""

import gzip
import hashlib
import io
import json
import os
import tarfile
import tempfile
from pathlib import Path

from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import canonical, confined, digest, publish, read_json
from extraction_service.archiving.models import (
    MAX_BYTES,
    MAX_MANIFEST_BYTES,
    ArchiveFile,
    ArchiveIndex,
    ArchiveManifest,
)
from extraction_service.archiving.selection import select_evidence, verify_membership


def load_index(path: Path) -> ArchiveIndex:
    return ArchiveIndex.model_validate_json(json.dumps(read_json(path)))


def archive_path(project: Path, index: ArchiveIndex) -> Path:
    return confined(project, f"results/archives/{index.archive_sha256}.tar.gz")


def _add(archive: tarfile.TarFile, name: str, content: bytes) -> None:
    entry = tarfile.TarInfo(name)
    entry.size = len(content)
    entry.mode = 0o644
    archive.addfile(entry, io.BytesIO(content))


def _extract(archive: Path, index: ArchiveIndex, destination: Path) -> ArchiveManifest:
    if archive.stat().st_size != index.archive_size or digest(archive) != index.archive_sha256:
        raise ValueError("Archive checksum or size differs")

    with tarfile.open(archive, "r:gz") as source:
        first = source.next()

        if (
            first is None
            or first.name != "archive-manifest.json"
            or not first.isreg()
            or first.size > MAX_MANIFEST_BYTES
        ):
            raise ValueError("Archive must begin with a bounded manifest")

        manifest_stream = source.extractfile(first)
        assert manifest_stream is not None
        raw = manifest_stream.read(MAX_MANIFEST_BYTES + 1)

        if hashlib.sha256(raw).hexdigest() != index.manifest_sha256:
            raise ValueError("Archive manifest checksum differs")

        manifest = ArchiveManifest.model_validate_json(raw)

        if (
            manifest.bundles != index.bundles
            or manifest.selection != index.selection
            or manifest.membership_sha256 != index.membership_sha256
        ):
            raise ValueError("Archive manifest differs from the compact index")

        expected = {file.path: file for file in manifest.files}
        seen = set()

        # Iterate the remaining stream, not extractall: no links, devices or path aliases.
        while member := source.next():
            file = expected.get(member.name)

            if (
                file is None
                or member.name in seen
                or not member.isreg()
                or member.sparse is not None
                or member.size != file.size
            ):
                raise ValueError("Unexpected, duplicate or unsafe archive member")

            target = confined(destination, file.path)
            target.parent.mkdir(parents=True, exist_ok=True)
            stream = source.extractfile(member)
            assert stream is not None
            checksum = hashlib.sha256()
            remaining = file.size

            with target.open("xb") as output:
                while remaining:
                    chunk = stream.read(min(1024 * 1024, remaining))

                    if not chunk:
                        raise ValueError("Truncated archive member")

                    output.write(chunk)
                    checksum.update(chunk)
                    remaining -= len(chunk)

            if checksum.hexdigest() != file.sha256:
                raise ValueError("Restored payload checksum differs")

            seen.add(file.path)

        if seen != set(expected):
            raise ValueError("Archive is missing expected payloads")

    for bundle in manifest.bundles:
        actual = verify_bundle(destination / "submission" / bundle.name)

        if actual != bundle:
            raise ValueError("Restored bundle metadata differs")

    _, covered = verify_membership(destination / "submission", json.loads(manifest.membership_json))

    if covered != index.covered_observations:
        raise ValueError("Covered membership count differs from the archive index")

    return manifest


def verify_archive(project: Path, index: ArchiveIndex) -> ArchiveManifest:
    """Verify compression, inventory and record reload using an isolated temporary restore."""

    return verify_archive_file(archive_path(project, index), index)


def verify_archive_file(archive: Path, index: ArchiveIndex) -> ArchiveManifest:
    with tempfile.TemporaryDirectory(prefix="hw01-verify-") as temporary:
        return _extract(archive, index, Path(temporary))


def create_archive(project: Path, config_file: str, selection: str) -> ArchiveIndex:
    selected = select_evidence(project, config_file, selection)
    files = []

    for bundle in selected.bundles:
        directory = confined(project, f"results/submission/{bundle.name}")

        for path in sorted(directory.rglob("*")):
            if path.is_file():
                relative = path.relative_to(directory).as_posix()
                files.append(
                    ArchiveFile(
                        path=f"submission/{bundle.name}/{relative}",
                        sha256=digest(path),
                        size=path.stat().st_size,
                    )
                )

    manifest = ArchiveManifest(
        selection=selection,
        membership_sha256=selected.membership_sha256,
        membership_json=selected.membership_json,
        evidence_index_sha256=selected.evidence_index_sha256,
        bundles=selected.bundles,
        files=tuple(files),
    )
    metadata = canonical(manifest.model_dump(mode="json"))

    if len(metadata) > MAX_MANIFEST_BYTES:
        raise ValueError("Manifest exceeds size limit")

    cache = confined(project, "results/archives")
    indexes = confined(project, "archive-index")
    cache.mkdir(parents=True, exist_ok=True)
    indexes.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=cache, prefix=".create-") as temporary:
        path = Path(temporary) / "archive.tar.gz"

        with (
            path.open("wb") as output,
            gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0) as compressed,
        ):
            with tarfile.open(
                fileobj=compressed, mode="w|", format=tarfile.USTAR_FORMAT
            ) as archive:
                _add(archive, "archive-manifest.json", metadata)

                for file in manifest.files:
                    source = confined(project / "results", file.path)
                    content = source.read_bytes()

                    if (
                        len(content) != file.size
                        or hashlib.sha256(content).hexdigest() != file.sha256
                    ):
                        raise ValueError("Source changed during packaging")

                    _add(archive, file.path, content)

        if path.stat().st_size > MAX_BYTES:
            raise ValueError("Compressed archive exceeds size limit")

        checksum = digest(path)
        index = ArchiveIndex(
            archive_sha256=checksum,
            archive_size=path.stat().st_size,
            manifest_sha256=hashlib.sha256(metadata).hexdigest(),
            object_key=f"hw01/archives/sha256/{checksum}.tar.gz",
            selection=selection,
            membership_sha256=selected.membership_sha256,
            bundles=selected.bundles,
            covered_observations=selected.covered_observations,
        )
        # Test full restoration before publishing either cache or Git-facing index.
        restored = Path(temporary) / "restore"
        restored.mkdir()
        _extract(path, index, restored)
        publish(path, archive_path(project, index))
        index_file = Path(temporary) / "index.json"
        index_file.write_bytes(canonical(index.model_dump(mode="json")))
        publish(index_file, confined(indexes, f"{checksum}.json"))

    return index


def restore_archive(project: Path, index: ArchiveIndex) -> Path:
    """Install into a new isolated directory; never overlay an existing restore or live runs."""

    root = confined(project, "results/restored")
    root.mkdir(parents=True, exist_ok=True)
    destination = confined(root, index.archive_sha256)

    if destination.exists():
        raise FileExistsError("Restore destination already exists")

    with tempfile.TemporaryDirectory(dir=root, prefix=".restore-") as temporary:
        staged = Path(temporary) / "verified"
        staged.mkdir()
        _extract(archive_path(project, index), index, staged)
        # rename is atomic on the same filesystem. The private stage has no symlinks.
        if destination.exists():
            raise FileExistsError("Restore destination was created concurrently")

        os.rename(staged, destination)

    return destination
