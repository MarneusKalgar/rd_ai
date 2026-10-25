"""Archive round trips preserve measured evidence and reject unsafe or changed payloads."""

import io
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

import pytest

from extraction_service.application.persistence import item_key, reload_records
from extraction_service.archiving.__main__ import main
from extraction_service.archiving.archive import (
    archive_path,
    create_archive,
    load_index,
    restore_archive,
    verify_archive,
)
from extraction_service.archiving.files import digest
from extraction_service.archiving.models import (
    MAX_FILE_BYTES,
    ArchiveFile,
    ArchiveIndex,
    BundleInfo,
)
from extraction_service.archiving.store_setup import initialize_store
from extraction_service.evaluation.reporting import evaluate_runs

from .conftest import ControlledService


@pytest.fixture
def archive_project(service: ControlledService, gold: dict[str, Any]) -> Path:
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "archive-source", "--input", "B02-S003-PO01")
    exported = service.invoke("export-run", "archive-source")
    assert result.returncode == exported.returncode == 0
    project = service.project
    manifest, records = reload_records(project / "results/submission/archive-source")
    record = records[0]
    key = item_key(record.input_id, record.model_id, record.prompt_id, record.sampling_id)
    membership = {
        "version": "matrix-membership-v1",
        "covered_observations": 1,
        "entries": [
            {
                "input_id": record.input_id,
                "model_id": record.model_id,
                "prompt_id": record.prompt_id,
                "sampling_id": record.sampling_id,
                "input_sha256": record.input_sha256,
                "schema_sha256": record.schema_sha256,
                "prompt_sha256": record.prompt_sha256,
                "status": "covered",
                "result_status": record.status.value,
                "source_run_id": record.run_id,
                "source_manifest_sha256": digest(
                    project / "results/runs/archive-source/manifest.json"
                ),
                "source_record_path": "results/runs/archive-source/" + manifest.records[key],
                "source_record_sha256": manifest.record_sha256[key],
            }
        ],
    }
    (project / "results/membership.json").write_text(json.dumps(membership))
    (project / "config/archives.yaml").write_text(
        "selections:\n  final-baselines:\n    membership: results/membership.json\n"
    )
    return project


def _create(project: Path) -> ArchiveIndex:
    return create_archive(project, "config/archives.yaml", "final-baselines")


def test_archive_roundtrip_is_deterministic_and_evaluates_original_evidence(
    archive_project: Path,
) -> None:
    project = archive_project
    originals = {
        path.relative_to(project / "results/submission"): path.read_bytes()
        for path in (project / "results/submission").rglob("*")
        if path.is_file()
    }
    first = _create(project)
    second = _create(project)
    assert first == second
    index_file = project / f"archive-index/{first.archive_sha256}.json"
    assert load_index(index_file) == first
    assert len(verify_archive(project, first).bundles) == 1

    restored = restore_archive(project, first)
    for relative, original in originals.items():
        assert (restored / "submission" / relative).read_bytes() == original
        assert (project / "results/submission" / relative).read_bytes() == original

    before = evaluate_runs(project, ["archive-source"])
    # Prove evaluation has no fallback to original run/export directories.
    shutil.rmtree(project / "results/runs")
    shutil.rmtree(project / "results/submission")
    after = evaluate_runs(
        project,
        ["archive-source"],
        source_dir=restored.relative_to(project).as_posix() + "/submission",
    )
    assert before == after

    with pytest.raises(FileExistsError):
        restore_archive(project, first)


def test_historical_membership_without_redundant_prompt_hash_uses_checked_run(
    archive_project: Path,
) -> None:
    path = archive_project / "results/membership.json"
    membership = json.loads(path.read_bytes())
    del membership["entries"][0]["prompt_sha256"]
    path.write_text(json.dumps(membership))

    index = _create(archive_project)
    manifest = verify_archive(archive_project, index)

    assert index.covered_observations == 1
    assert len(manifest.bundles) == 1


@pytest.mark.parametrize(
    "defect", ["duplicate", "count", "record-hash", "manifest-hash", "identity"]
)
def test_membership_defects_block_packaging(archive_project: Path, defect: str) -> None:
    path = archive_project / "results/membership.json"
    membership = json.loads(path.read_bytes())
    entry = membership["entries"][0]

    if defect == "duplicate":
        membership["entries"].append(dict(entry))
    elif defect == "count":
        membership["covered_observations"] = 2
    elif defect == "identity":
        entry["prompt_sha256"] = "0" * 64
    else:
        field = "source_record_sha256" if defect == "record-hash" else "source_manifest_sha256"
        entry[field] = "0" * 64

    path.write_text(json.dumps(membership))
    with pytest.raises(ValueError):
        _create(archive_project)
    assert not (archive_project / "archive-index").exists()


@pytest.mark.parametrize("defect", ["changed", "extra", "file-link", "directory-link", "root-link"])
def test_bundle_defects_are_not_hidden_by_a_valid_manifest(
    archive_project: Path,
    defect: str,
    tmp_path: Path,
) -> None:
    source = archive_project / "results/submission/archive-source"
    schema = source / "purchase-order-extraction.v1.schema.json"

    if defect == "changed":
        schema.write_bytes(schema.read_bytes() + b" ")
    elif defect == "extra":
        (source / "extra.json").write_text("{}")
    elif defect == "file-link":
        outside = tmp_path / "schema.json"
        schema.rename(outside)
        schema.symlink_to(outside)
    elif defect == "directory-link":
        records = source / "records"
        outside = tmp_path / "records"
        records.rename(outside)
        records.symlink_to(outside, target_is_directory=True)
    else:
        outside = tmp_path / "export"
        source.rename(outside)
        source.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError):
        _create(archive_project)


def _hostile_archive(project: Path, index: ArchiveIndex, defect: str) -> ArchiveIndex:
    with tarfile.open(archive_path(project, index), "r:gz") as source:
        members = source.getmembers()
        payloads = []
        for member in members:
            stream = source.extractfile(member)
            assert stream is not None
            payloads.append((member, stream.read()))

    if defect == "missing":
        payloads.pop()
    elif defect == "duplicate":
        payloads.append(payloads[1])
    elif defect == "checksum":
        member, raw = payloads[1]
        payloads[1] = member, bytes([raw[0] ^ 1]) + raw[1:]
    else:
        member = tarfile.TarInfo("../escape" if defect == "traversal" else payloads[1][0].name)
        if defect == "symlink":
            member.type = tarfile.SYMTYPE
            member.linkname = "/tmp/escape"
            payloads[1] = member, b""
        else:
            member.size = 1
            payloads.append((member, b"x"))

    output = project / "hostile.tar.gz"
    with tarfile.open(output, "w:gz") as archive:
        for member, raw in payloads:
            archive.addfile(member, io.BytesIO(raw))
    checksum = digest(output)
    changed = index.model_copy(
        update={
            "archive_sha256": checksum,
            "archive_size": output.stat().st_size,
            "object_key": f"hw01/archives/sha256/{checksum}.tar.gz",
        }
    )
    shutil.copyfile(output, archive_path(project, changed))
    return changed


@pytest.mark.parametrize("defect", ["traversal", "symlink", "duplicate", "missing", "checksum"])
def test_matching_outer_checksum_does_not_bypass_inner_validation(
    archive_project: Path,
    defect: str,
) -> None:
    index = _hostile_archive(archive_project, _create(archive_project), defect)

    with pytest.raises(ValueError):
        restore_archive(archive_project, index)

    assert not (archive_project / f"results/restored/{index.archive_sha256}").exists()
    assert not list((archive_project / "results/restored").glob(".restore-*"))


def test_corrupt_cache_and_existing_evidence_are_not_overwritten(archive_project: Path) -> None:
    index = _create(archive_project)
    path = archive_path(archive_project, index)
    path.write_bytes(b"corrupt")

    with pytest.raises(ValueError, match="checksum or size"):
        verify_archive(archive_project, index)
    with pytest.raises(ValueError, match="overwrite"):
        _create(archive_project)
    assert path.read_bytes() == b"corrupt"


def test_archive_cli_failure_is_sanitized(
    archive_project: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    result = main(["--project-dir", str(archive_project), "verify", "--index", "../private"])
    report = json.loads(capsys.readouterr().out)
    assert result == 2 and report == {"archive_error": "ValueError", "command": "verify"}
    assert not (archive_project / "results/restored").exists()


def test_evaluation_source_cannot_escape_project(archive_project: Path) -> None:
    with pytest.raises(ValueError, match="owning directory"):
        evaluate_runs(archive_project, ["archive-source"], source_dir="../outside")


def test_garage_configuration_is_private_and_never_replaced(tmp_path: Path) -> None:
    initialize_store(tmp_path)
    environment = tmp_path / ".env.archive"
    original = environment.read_bytes()
    assert environment.stat().st_mode & 0o777 == 0o600
    assert b"GARAGE_DEFAULT_ACCESS_KEY=GK" in original
    assert (
        b"replication_factor = 1" in (tmp_path / "results/garage-config/garage.toml").read_bytes()
    )

    with pytest.raises(FileExistsError):
        initialize_store(tmp_path)
    assert environment.read_bytes() == original


@pytest.mark.parametrize("defect", [None, "inventory", "escape", "credential"])
def test_companion_evidence_uses_explicit_provenance_and_credential_guards(
    archive_project: Path,
    defect: str | None,
) -> None:
    companion = archive_project / "results/submission/companion"
    companion.mkdir()
    content = '{"note":"Bearer synthetic-test-placeholder"}' if defect == "credential" else "{}"
    (companion / "report.json").write_text(content)
    inventory = {"report.json": digest(companion / "report.json")}
    (companion / "files.sha256.json").write_text(json.dumps(inventory))
    reference = {
        "path": "../private" if defect == "escape" else "results/submission/companion",
        "source_inventory_sha256": "0" * 64
        if defect == "inventory"
        else digest(companion / "files.sha256.json"),
    }
    (archive_project / "results/provenance.json").write_text(json.dumps({"bundles": [reference]}))
    config = archive_project / "config/archives.yaml"
    config.write_text(config.read_text() + "    evidence_index: results/provenance.json\n")

    if defect is not None:
        expected = "credential" if defect == "credential" else "Provenance"
        with pytest.raises(ValueError, match=expected):
            _create(archive_project)
    else:
        index = _create(archive_project)
        assert len(index.bundles) == 2
        shutil.rmtree(archive_project / "results/submission")
        assert len(verify_archive(archive_project, index).bundles) == 2


def test_archive_limits_and_content_key_are_validated() -> None:
    with pytest.raises(ValueError, match="size"):
        ArchiveFile(path="submission/run/file.json", sha256="0" * 64, size=MAX_FILE_BYTES + 1)

    with pytest.raises(ValueError, match="canonical"):
        ArchiveFile(path="submission/../file.json", sha256="0" * 64, size=1)

    with pytest.raises(ValueError, match="Object key"):
        ArchiveIndex(
            archive_sha256="0" * 64,
            archive_size=1,
            manifest_sha256="0" * 64,
            object_key="arbitrary/key",
            selection="test",
            membership_sha256="0" * 64,
            bundles=(
                BundleInfo(name="run", kind="run", inventory_sha256="0" * 64, payload_files=1),
            ),
            covered_observations=0,
        )
