"""Offline provider isolation, local initialization gates and retained setup evidence."""

import json
import socket
import subprocess
import sys
from contextlib import nullcontext
from pathlib import Path
from typing import Never

import pytest

import extraction_service.runtime.__main__ as runtime_cli
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.runtime.__main__ import main
from extraction_service.runtime.configuration import CapacityScope, SetupSettings
from extraction_service.runtime.workflows import local_setup, provider_setup

from .conftest import OllamaServer


def test_provider_setup_needs_no_key_or_ollama_and_preserves_accounting(
    project_copy: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    def reject_network(*args: object, **kwargs: object) -> Never:
        raise AssertionError("Provider setup performed network I/O")

    monkeypatch.setattr(socket.socket, "connect", reject_network)
    results = project_copy / "results"
    results.mkdir()
    ledger = results / "budget-ledger.json"
    lock = results / "budget-ledger.lock"
    ledger.write_bytes(b"preserve corrupt or unknown ledger too")
    lock.write_bytes(b"existing lock identity")

    report = provider_setup(project_copy, "provider")
    repeated = provider_setup(project_copy, "provider")

    assert report["provider_inference_performed"] is False
    assert report["provider_execution_requires_human_approval"] is True
    assert report["storage"]["storage_id"] == repeated["storage"]["storage_id"]
    assert ledger.read_bytes() == b"preserve corrupt or unknown ledger too"
    assert lock.read_bytes() == b"existing lock identity"


def test_successful_setup_then_readiness_reuses_pinned_installation_without_key(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    initialized = local_setup(project_copy, "local", setup_settings, client, initialize=True)
    installation_path = project_copy / "results/setup/installation.json"
    initial_bytes = installation_path.read_bytes()
    repeated = local_setup(project_copy, "local", setup_settings, client, initialize=False)

    assert initialized["status"] == repeated["status"] == "ready"
    assert initialized["pulled"] is True
    assert repeated["pulled"] is False
    assert initialized["loaded_model"]["context_length"] == 16384
    assert repeated["processor"] == "cpu"
    assert repeated["capacity"]["token_capacity_verified"] is True
    assert len(repeated["capacity"]["measurements"]) == 6
    assert repeated["capacity"]["scope"] == "representative"
    assert repeated["capacity"]["prepared_request_count"] == 60
    assert repeated["capacity"]["selected_request_count"] == 6
    assert repeated["capacity"]["all_prepared_requests_verified"] is False
    assert repeated["capacity"]["actual_requests_require_admission"] is True
    assert installation_path.read_bytes() == initial_bytes
    assert not (project_copy / "results/budget-ledger.json").exists()
    assert [path for path, _ in server.requests].count("/api/pull") == 1


def test_exhaustive_readiness_checks_every_request_and_preserves_sample_report(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
) -> None:
    local_setup(project_copy, "local", setup_settings, client, initialize=True)
    sample_path = project_copy / "results/setup/readiness.json"
    sample_bytes = sample_path.read_bytes()
    server.requests.clear()

    report = local_setup(
        project_copy,
        "local",
        setup_settings,
        client,
        initialize=False,
        capacity_scope=CapacityScope.EXHAUSTIVE,
    )

    assert report["status"] == "ready"
    assert report["capacity"]["scope"] == "exhaustive"
    assert report["capacity"]["selected_request_count"] == 60
    assert len(report["capacity"]["measurements"]) == 60
    assert report["capacity"]["all_prepared_requests_verified"] is True
    assert report["capacity"]["actual_requests_require_admission"] is True
    assert [path for path, _ in server.requests].count("/api/chat") == 60
    assert "/api/pull" not in [path for path, _ in server.requests]
    assert sample_path.read_bytes() == sample_bytes
    saved_path = project_copy / "results/setup/capacity-exhaustive.json"
    assert json.loads(saved_path.read_text()) == report


@pytest.mark.parametrize(
    "defect", ["image", "version", "digest", "missing_model", "missing_record"]
)
def test_readiness_cannot_accept_changed_initialization_identity_or_repull(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
    defect: str,
) -> None:
    local_setup(project_copy, "local", setup_settings, client, initialize=True)
    record = project_copy / "results/setup/installation.json"
    evidence = json.loads(record.read_text())
    message = ""

    if defect == "image":
        evidence["image"] = "different image"
        message = "image/version differs"
    elif defect == "version":
        server.replacements["/api/version"] = {"version": "different-version"}
        message = "reviewed version"
    elif defect == "digest":
        evidence["runtime"]["model_digest"] = "b" * 64
        message = "pin differs"
    elif defect == "missing_model":
        server.installed = False
        message = "model is missing"
    else:
        message = "No initialization evidence"

    record.write_text(json.dumps(evidence))

    if defect == "missing_record":
        record.unlink()

    server.requests.clear()

    with pytest.raises(ValueError, match=message):
        local_setup(project_copy, "local", setup_settings, client, initialize=False)

    assert "/api/pull" not in [path for path, _ in server.requests]
    assert "/api/chat" not in [path for path, _ in server.requests]


def test_model_load_failure_is_saved_as_blocked_not_ready(
    project_copy: Path, client: JsonHttpClient, server: OllamaServer, setup_settings: SetupSettings
) -> None:
    server.status_codes["/api/generate"] = 500
    server.replacements["/api/generate"] = {"error": "model requires more system memory"}

    report = local_setup(project_copy, "local", setup_settings, client, initialize=True)

    assert report["status"] == "blocked"
    assert report["load_error"]["http_status"] == 500
    assert "more system memory" in report["load_error"]["body"]
    assert "capacity" not in report
    assert "/api/chat" not in [path for path, _ in server.requests]
    saved = json.loads((project_copy / "results/setup/readiness.json").read_text())
    assert saved == report


def test_wrong_mode_rejected_before_local_http(
    project_copy: Path, client: JsonHttpClient, server: OllamaServer, setup_settings: SetupSettings
) -> None:
    with pytest.raises(ValueError, match="another runtime"):
        local_setup(project_copy, "provider", setup_settings, client, initialize=True)

    assert server.requests == []


def test_provider_cli_is_offline_and_reports_storage(
    project_copy: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    status = main(["--project-dir", str(project_copy), "provider"])

    output = json.loads(capsys.readouterr().out)

    assert status == 0
    assert output["input_count"] == 30
    assert output["budget_initialized"] is False
    assert output["storage"]["storage_id"]


def test_runtime_cli_hides_bad_environment_values(
    project_copy: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    private = "do-not-print-this-value"
    monkeypatch.setenv("HW01_SETUP_IMAGE", private)

    status = main(["--project-dir", str(project_copy), "readiness"])

    output = capsys.readouterr()

    assert status == 2
    assert "setup_error" in json.loads(output.out)
    assert private not in output.out + output.err


def test_exhaustive_cli_routes_to_full_diagnostic(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    local_setup(project_copy, "local", setup_settings, client, initialize=True)
    server.requests.clear()
    monkeypatch.setenv("HW01_SETUP_IMAGE", setup_settings.image)
    monkeypatch.setenv("HW01_SETUP_CONTEXT_LENGTH", "16384")
    monkeypatch.setattr(runtime_cli, "ollama_client", lambda settings: nullcontext(client))

    status = main(["--project-dir", str(project_copy), "readiness", "--exhaustive"])

    report = json.loads(capsys.readouterr().out)

    assert status == 0
    assert report["capacity"]["scope"] == "exhaustive"
    assert [path for path, _ in server.requests].count("/api/chat") == 60


@pytest.mark.parametrize("command", ["provider", "initialize", "storage"])
def test_exhaustive_cli_rejects_unrelated_commands_before_setup(
    project_copy: Path, command: str, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as error:
        main(["--project-dir", str(project_copy), command, "--exhaustive"])

    assert error.value.code == 2
    assert "only supported with readiness" in capsys.readouterr().err
    assert not (project_copy / "results").exists()


def test_local_cli_reports_blocked_exit_without_provider_calls(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("HW01_SETUP_IMAGE", setup_settings.image)
    monkeypatch.setattr(runtime_cli, "ollama_client", lambda settings: nullcontext(client))
    server.status_codes["/api/generate"] = 500
    server.replacements["/api/generate"] = {"error": "insufficient memory"}

    status = main(["--project-dir", str(project_copy), "initialize"])

    report = json.loads(capsys.readouterr().out)

    assert status == 3
    assert report["status"] == "blocked"
    assert report["load_error"]["http_status"] == 500
    assert report["provider_inference_performed"] is False


def test_runtime_provider_through_actual_process_entrypoint(project_copy: Path) -> None:
    command = [
        sys.executable,
        "-m",
        "extraction_service.runtime",
        "--project-dir",
        str(project_copy),
        "provider",
    ]

    result = subprocess.run(command, capture_output=True, text=True, timeout=10)

    report = json.loads(result.stdout)

    assert result.returncode == 0
    assert result.stderr == ""
    assert report["provider_inference_performed"] is False
    assert report["storage"]["uid"] == 10001


@pytest.mark.parametrize("unload_fails", [False, True])
def test_blocked_capacity_unloads_model_but_keeps_weights_and_primary_failure(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    setup_settings: SetupSettings,
    unload_fails: bool,
) -> None:
    server.unload_fails = unload_fails
    server.status_codes["/api/chat"] = 400
    server.replacements["/api/chat"] = {"error": "input exceeds context"}

    report = local_setup(project_copy, "local", setup_settings, client, initialize=True)

    assert report["status"] == "blocked"
    assert report["capacity"]["http_status"] == 400
    assert report["unload_acknowledged"] is not unload_fails
    assert server.installed is True
    assert server.requests[-1] == (
        "/api/generate",
        {"model": server.pin.model, "prompt": "", "stream": False, "keep_alive": 0},
    )
