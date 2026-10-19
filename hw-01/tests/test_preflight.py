import json
import socket
import subprocess
import sys
from pathlib import Path
from typing import Never

import pytest
from conftest import PROJECT_DIR

from hw01.cli import main
from hw01.preflight import preflight


def test_offline_preflight_needs_no_key_and_makes_no_connections(
    project_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def reject_connection(*args: object, **kwargs: object) -> Never:
        raise AssertionError("Offline preflight attempted a network connection")

    monkeypatch.setattr(socket, "create_connection", reject_connection)
    monkeypatch.setattr(socket.socket, "connect", reject_connection)

    result = preflight(project_copy)

    assert result.input_count == 30
    assert result.gold_count == result.annotation_count == 10
    assert result.mode == "offline"
    assert result.model_capabilities_verified is False
    assert result.experiment.selection.model_id == "local"
    assert len(result.prompts[0].sha256) == 64


@pytest.mark.parametrize("case", ["missing_prompt", "empty_prompt", "missing_config", "bad_config"])
def test_preflight_rejects_unusable_prompt_or_config_references(
    project_copy: Path, capsys: pytest.CaptureFixture[str], case: str
) -> None:
    prompt = project_copy / "prompts/v1.txt"
    config = project_copy / "config/experiments.yaml"

    if case == "missing_prompt":
        prompt.unlink()
    elif case == "empty_prompt":
        prompt.write_text("   ")
    elif case == "missing_config":
        config.unlink()
    else:
        config.write_text("unexpected: true")

    status = main(["--project-dir", str(project_copy), "preflight"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)

    assert status == 2
    assert "setup_error" in report
    assert "input_count" not in report


def test_preflight_does_not_expose_supplied_key_in_success_or_errors(
    project_copy: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    private_value = "private-preflight-test-value"
    monkeypatch.setenv("OPENROUTER_API_KEY", private_value)

    status = main(["--project-dir", str(project_copy), "preflight"])

    captured = capsys.readouterr()

    assert status == 0
    assert private_value not in captured.out + captured.err

    (project_copy / ".env").write_text(f"UNEXPECTED_KEY={private_value}")

    error_status = main(["--project-dir", str(project_copy), "preflight"])

    failure = capsys.readouterr()

    assert error_status == 2
    assert private_value not in failure.out + failure.err


def test_preflight_works_through_real_module_entrypoint() -> None:
    command = [sys.executable, "-m", "hw01", "--project-dir", str(PROJECT_DIR), "preflight"]

    result = subprocess.run(command, capture_output=True, text=True, timeout=10)

    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert result.stderr == ""
    assert report["input_count"] == 30
    assert report["gold_count"] == 10
    assert report["model_capabilities_verified"] is False
