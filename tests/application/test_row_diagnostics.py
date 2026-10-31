"""The real CLI checks source evidence without inference, gold answers or writes."""

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path
from typing import Final

import pytest

from extraction_service.diagnostics.catalog_rows import check_ordered_rows
from extraction_service.diagnostics.reporting import diagnose_runs
from extraction_service.extraction.validation import JsonObject

from .conftest import ControlledService

INPUT: Final[str] = "B02-S016-PO01"


def snapshot(directory: Path) -> dict[str, str]:
    return {
        str(path.relative_to(directory)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in directory.rglob("*")
        if path.is_file()
    }


def save_example(service: ControlledService) -> str:
    extraction = json.loads((service.project / f"data/gold/{INPUT}.json").read_bytes())
    catalog = deepcopy(extraction["lineItems"][0])
    catalog["buyerProductName"] = "Sealing compound RC-54 500 kg bulk bag"
    catalog["buyerProductQuantity"] = None
    extraction["lineItems"].append(catalog)
    service.responses = [json.dumps(extraction)]
    run_id = "diagnostic-fixture"

    run = service.invoke("run", "--run-id", run_id, "--input", INPUT)
    assert run.returncode == 0, run.stdout + run.stderr
    exported = service.invoke("export-run", run_id)
    assert exported.returncode == 0, exported.stdout + exported.stderr

    return run_id


@pytest.mark.parametrize("source", ["runs", "submission"])
def test_real_diagnostic_command_reads_no_gold_makes_no_calls_and_preserves_results(
    service: ControlledService,
    source: str,
) -> None:
    run_id = save_example(service)
    before = snapshot(service.project / "results")
    requests = len(service.requests)
    shutil.rmtree(service.project / "data/gold")
    shutil.rmtree(service.project / "data/annotations")

    first = service.invoke("diagnose-rows", run_id, "--source", source)
    second = service.invoke("diagnose-rows", run_id, "--source", source)

    assert first.returncode == second.returncode == 0, first.stdout + first.stderr
    report = json.loads(first.stdout)
    assert json.loads(second.stdout) == report
    assert report["check_id"] == "catalog-order-evidence-v1"
    assert report["diagnostic_only"] and not report["gold_answers_read"]
    code_directory = Path(__file__).resolve().parents[2] / "src/extraction_service/diagnostics"
    expected_hashes = {
        name: hashlib.sha256((code_directory / name).read_bytes()).hexdigest()
        for name in ("types.py", "order_forms.py", "catalog_rows.py", "reporting.py")
    }
    expected_definition = json.dumps(expected_hashes, sort_keys=True).encode()
    assert report["check_files_sha256"] == expected_hashes
    assert report["check_sha256"] == hashlib.sha256(expected_definition).hexdigest()
    assert report["row_counts"] == {"supported": 1, "contradicted": 1, "unknown": 0}
    record = report["runs"][0]["records"][0]
    assert record["original_status"] == "succeeded"
    assert record["diagnostic"]["profile_id"] == "hu-entered-order-quantity-v1"
    assert len(record["diagnostic"]["source_rows"]) == 67
    finding = record["diagnostic"]["findings"][1]
    assert finding["output_path"] == "/lineItems/1"
    assert finding["reason"] == "blank_order_quantity"
    assert finding["source_rows"][0]["quantity_cell"] == "ORDER!C21"
    assert len(service.requests) == requests
    assert snapshot(service.project / "results") == before


@pytest.mark.parametrize("source", ["runs", "submission"])
def test_failed_saved_extraction_is_retained_as_unknown_in_diagnostic_report(
    service: ControlledService,
    source: str,
) -> None:
    service.responses = ["{}", "{}"]
    run_id = "failed-row-diagnostic"
    run = service.invoke("run", "--run-id", run_id, "--input", INPUT)
    assert run.returncode == 1, run.stdout + run.stderr
    exported = service.invoke("export-run", run_id)
    assert exported.returncode == 0, exported.stdout + exported.stderr
    saved_path = next((service.project / "results/runs" / run_id / "records").iterdir())
    saved_record = json.loads(saved_path.read_bytes())
    assert saved_record["status"] == "failed" and saved_record["extraction"] is None
    before = snapshot(service.project / "results")
    requests = len(service.requests)

    result = service.invoke("diagnose-rows", run_id, "--source", source)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert len(report["runs"]) == 1
    records = report["runs"][0]["records"]
    assert len(records) == 1
    record = records[0]
    assert record["input_id"] == INPUT
    assert record["original_status"] == "failed"
    assert record["original_reason"] == saved_record["reason"]
    assert record["diagnostic"]["status"] == "unknown"
    assert record["diagnostic"]["reason"] == "unusable_extraction"
    assert record["diagnostic"]["findings"] == []
    assert record["row_counts"] == {"supported": 0, "contradicted": 0, "unknown": 0}
    assert report["row_counts"] == record["row_counts"]
    assert len(service.requests) == requests
    assert snapshot(service.project / "results") == before


@pytest.mark.parametrize("artifact", ["input", "record"])
def test_diagnostic_rejects_tampered_source_or_saved_record(
    service: ControlledService,
    artifact: str,
) -> None:
    run_id = save_example(service)

    if artifact == "input":
        path = service.project / f"data/inputs/{INPUT}.txt"
    else:
        path = next((service.project / "results/submission" / run_id / "records").iterdir())

    path.write_bytes(path.read_bytes() + b"\n")
    result = service.invoke("diagnose-rows", run_id)

    assert result.returncode == 2
    assert json.loads(result.stdout)["setup_error"] == (
        "ArtifactError" if artifact == "input" else "ValueError"
    )


def test_duplicate_run_requests_are_rejected(project_copy: Path) -> None:
    with pytest.raises(ValueError, match="distinct saved runs"):
        diagnose_runs(project_copy, ["same", "same"])


def test_unknown_layout_still_reports_all_output_rows(gold: JsonObject) -> None:
    result = check_ordered_rows("Product and quantity in an unsupported layout", gold)

    assert result.status.value == "unknown"
    assert len(result.findings) == 1
    assert result.findings[0].reason.value == "unsupported_layout"
