import json
from pathlib import Path

import pytest
from conftest import PROJECT_DIR

from hw01.cli import main
from hw01.extraction.validation import JsonObject


def test_gold_check_reports_the_pinned_schema_and_all_approved_cases(
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = main(["--project-dir", str(PROJECT_DIR), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 0
    assert report["gold_count"] == report["valid_count"] == 10
    assert report["schema"]["version"] == "v1"
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


def test_missing_schema_or_manifest_is_a_setup_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    status = main(["--project-dir", str(tmp_path), "validate-gold"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 2
    assert "setup_error" in report
