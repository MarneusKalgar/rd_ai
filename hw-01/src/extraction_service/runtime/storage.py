"""Persistent setup evidence; budget files are never initialized or modified here."""

import fcntl
import json
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from uuid import uuid4

from extraction_service.runtime.errors import SetupError


@contextmanager
def setup_lock(results_dir: Path) -> Generator[Path]:
    """Serialize setup updates; concurrent setup fails instead of waiting indefinitely."""

    directory = results_dir / "setup"
    directory.mkdir(parents=True, exist_ok=True)

    with (directory / "setup.lock").open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SetupError("Another setup operation holds results/setup/setup.lock") from None

        try:
            yield directory
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def write_report(path: Path, value: dict[str, Any]) -> None:
    """Atomically replace evidence within the mounted directory and sync it to disk."""

    serialized = json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n"

    temporary_path: Path | None = None

    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(serialized)
            temporary.flush()
            os.fsync(temporary.fileno())

        temporary_path.replace(path)
        directory_fd = os.open(path.parent, os.O_DIRECTORY)

        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def verify_storage(results_dir: Path) -> dict[str, Any]:
    """Prove create, lock, replace and read permissions without touching accounting.

    The persistent ID must be identical in subsequent containers. The replacement
    probe exercises the same mounted directory used for ledger atomic replacement.
    """

    with setup_lock(results_dir) as directory:
        identity_path = directory / "storage.json"
        reused = identity_path.exists()

        if reused:
            identity = json.loads(identity_path.read_text())

            if not isinstance(identity, dict) or not isinstance(identity.get("id"), str):
                raise SetupError("Invalid setup storage identity; inspect the results volume")
        else:
            identity = {"id": str(uuid4())}
            write_report(identity_path, identity)

        with tempfile.TemporaryDirectory(prefix=".storage-probe-", dir=results_dir) as temporary:
            probe = Path(temporary) / "probe.json"
            write_report(probe, {"generation": 1})
            write_report(probe, {"generation": 2})

            if json.loads(probe.read_text()) != {"generation": 2}:
                raise SetupError("Results storage failed atomic replacement verification")

    return {"storage_id": identity["id"], "reused": reused, "uid": os.getuid()}
