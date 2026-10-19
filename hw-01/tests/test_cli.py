import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import PROJECT_DIR

from extraction_service.cli import main
from extraction_service.extraction.validation import JsonObject


def test_gold_check_reports_the_pinned_schema_and_all_approved_cases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = main(["--project-dir", str(PROJECT_DIR), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 0
    assert report["gold_count"] == report["valid_count"] == 10
    assert report["schema"]["version"] == "v1"
    schema_bytes = (PROJECT_DIR / "schemas/purchase-order-extraction.v1.schema.json").read_bytes()
    assert report["schema"]["sha256"] == hashlib.sha256(schema_bytes).hexdigest()
    assert report["failures"] == []


def test_invalid_response_has_nonzero_exit_and_structured_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    gold: JsonObject,
) -> None:
    gold["model"] = "must stay outside the extraction"
    response = tmp_path / "response.json"
    response.write_text(json.dumps(gold))

    status = main(["--project-dir", str(PROJECT_DIR), "validate-response", str(response)])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 1
    assert report["value"] is None
    assert report["issues"][0]["keyword"] == "additionalProperties"
    assert report["raw_response"] == response.read_text()


def test_missing_manifest_is_a_setup_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = main(["--project-dir", str(tmp_path), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 2
    assert "manifest.json" in report["setup_error"]


@pytest.mark.parametrize("valid_response", [True, False], ids=["valid", "invalid"])
def test_module_entrypoint_returns_process_status_and_response_evidence(
    tmp_path: Path,
    gold: JsonObject,
    valid_response: bool,
) -> None:
    if not valid_response:
        gold["model"] = "metadata"

    raw_response = json.dumps(gold, ensure_ascii=False, indent=2)
    response_file = tmp_path / "response.json"
    response_file.write_text(raw_response, encoding="utf-8")
    command = [
        sys.executable,
        "-m",
        "extraction_service",
        "--project-dir",
        str(PROJECT_DIR),
        "validate-response",
        str(response_file),
    ]

    result = subprocess.run(command, capture_output=True, text=True, timeout=10)

    report = json.loads(result.stdout)
    expected_status = 0 if valid_response else 1

    assert result.returncode == expected_status
    assert result.stderr == ""
    assert report["raw_response"] == raw_response

    if valid_response:
        assert report["value"] == gold
        assert report["issues"] == []
    else:
        assert report["value"] is None
        assert report["issues"][0]["stage"] == "schema"
        assert report["issues"][0]["keyword"] == "additionalProperties"


def test_changed_gold_bytes_are_a_setup_failure(
    project_copy: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest = json.loads((project_copy / "data/manifest.json").read_text())
    gold_path = project_copy / "data" / manifest["cases"][0]["goldFile"]
    original_text = gold_path.read_text(encoding="utf-8")
    gold_path.write_text(original_text + "\n", encoding="utf-8")

    status = main(["--project-dir", str(project_copy), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 2
    assert report["setup_error"].startswith("Approved artifact hash mismatch:")
    assert str(gold_path) in report["setup_error"]


def test_matching_hash_does_not_hide_invalid_gold_contents(
    project_copy: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    manifest_path = project_copy / "data/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    case = manifest["cases"][0]
    gold_path = project_copy / "data" / case["goldFile"]
    invalid_gold = json.loads(gold_path.read_text())
    invalid_gold["model"] = "metadata"
    modified_bytes = json.dumps(invalid_gold).encode("utf-8")
    gold_path.write_bytes(modified_bytes)
    case["goldSha256"] = hashlib.sha256(modified_bytes).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    status = main(["--project-dir", str(project_copy), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 1
    assert report["gold_count"] == 10
    assert report["valid_count"] == 9
    assert len(report["failures"]) == 1
    assert report["failures"][0]["inputId"] == case["inputId"]
    issues = report["failures"][0]["issues"]
    assert len(issues) == 1
    assert issues[0]["stage"] == "schema"
    assert issues[0]["keyword"] == "additionalProperties"
    assert issues[0]["instance_path"] == ""
