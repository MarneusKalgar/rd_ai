"""Incremental durability, reload checks and failure visibility."""

import hashlib
import json
from typing import Any

import pytest

from extraction_service.application.persistence import (
    RunState,
    RunStore,
    reload_records,
)
from extraction_service.application.runner import run
from extraction_service.application.selection import RunOptions
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.records import RunRecord

from .conftest import ControlledService

INPUTS = ["B02-S002-PO01", "B02-S003-PO01", "B02-S006-PO01"]


def test_default_selection_persists_all_thirty(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    service.responses = [json.dumps(gold)] * 30
    # This controlled endpoint's rendered vocabulary is deliberately tiny. The
    # source payload is still sent in full; separate tests exercise context rejection.
    service.rendered_override = "<bos>ab"

    result = service.invoke("run", "--run-id", "all-thirty")

    assert result.returncode == 0, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/all-thirty")
    assert len(manifest.jobs) == len(records) == 30
    assert len({record.input_id for record in records}) == 30
    assert manifest.summary is not None and manifest.summary.succeeded == 30
    generations = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload is not None and not payload.get("_debug_render_only")
    ]
    assert len(generations) == 30
    declared = json.loads((service.project / "data/corpus-manifest.json").read_bytes())["cases"]
    expected_sources = [
        (service.project / "data" / case["inputFile"]).read_text() for case in declared
    ]
    assert [payload["messages"][1]["content"] for payload in generations] == expected_sources
    instructions = (service.project / "prompts/v1.txt").read_text()
    schema = json.loads(
        (service.project / "schemas/purchase-order-extraction.v1.schema.json").read_bytes()
    )

    for payload in generations:
        assert payload["format"] == schema
        system = payload["messages"][0]["content"]
        assert system.startswith(instructions + "\n\nJSON Schema:\n")
        assert json.loads(system.split("\n\nJSON Schema:\n", 1)[1]) == schema


def test_later_write_failure_retains_earlier_records_and_closes_once(
    service: ControlledService,
    gold: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service.responses = [json.dumps(gold)] * 3
    original_save = RunStore.save
    original_close = JsonHttpClient.close
    closed: list[JsonHttpClient] = []

    def close(client: JsonHttpClient) -> None:
        closed.append(client)
        original_close(client)

    def fail_second(store: RunStore, record: RunRecord) -> None:
        if store.manifest.records:
            raise OSError("controlled write failure")

        original_save(store, record)

    for key, value in service.environment().items():
        monkeypatch.setenv(key, value)

    monkeypatch.setattr(JsonHttpClient, "close", close)
    monkeypatch.setattr(RunStore, "save", fail_second)

    with pytest.raises(OSError, match="controlled write failure"):
        run(service.project, RunOptions(run_id="disk-failure", input_ids=INPUTS))

    manifest, records = reload_records(service.project / "results/runs/disk-failure")
    assert manifest.state == RunState.INTERRUPTED
    assert len(records) == 1
    assert records[0].input_id == INPUTS[0]
    checkpoints = list((service.project / "results/runs/disk-failure/checkpoints").glob("*.json"))
    assert len(checkpoints) == 2
    assert all(len(json.loads(path.read_bytes())["attempts"]) == 1 for path in checkpoints)
    assert len(closed) == 1
    assert len(service.responses) == 1


@pytest.mark.parametrize(
    "defect", ["record-bytes", "record-path", "schema-bytes", "record-identity", "summary"]
)
def test_reload_rejects_corruption(
    service: ControlledService,
    gold: dict[str, Any],
    defect: str,
) -> None:
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "tampered", "--input", INPUTS[-1])
    assert result.returncode == 0
    directory = service.project / "results/runs/tampered"
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    key = next(iter(manifest["records"]))
    record_path = directory / manifest["records"][key]

    if defect == "record-bytes":
        record_path.write_bytes(record_path.read_bytes() + b" ")
        expected = "record hash mismatch"
    elif defect == "record-path":
        manifest["records"][key] = "../escape.json"
        expected = "record path"
    elif defect == "schema-bytes":
        schema_path = next(directory.glob("*.schema.json"))
        schema_path.write_bytes(schema_path.read_bytes() + b" ")
        expected = "schema hash"
    elif defect == "record-identity":
        record = json.loads(record_path.read_bytes())
        record["input_id"] = "different-input"
        record_path.write_text(json.dumps(record))
        manifest["record_sha256"][key] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        expected = "declared run job"
    else:
        manifest["summary"]["succeeded"] = 2
        expected = "summary differs"

    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(ValueError, match=expected):
        reload_records(directory)


def test_failed_public_export_removes_partial_bundle(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    gold["buyerName"] = "Bearer deliberately-unsafe-test-text"
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "unsafe-export", "--input", INPUTS[-1])
    assert result.returncode == 0

    exported = service.invoke("export-run", "unsafe-export")

    assert exported.returncode == 2
    assert not (service.project / "results/submission/unsafe-export").exists()
    manifest, records = reload_records(service.project / "results/runs/unsafe-export")
    assert manifest.state == RunState.COMPLETE
    assert records[0].extraction == gold
