"""Native composition reuses the real runner without Docker initialization evidence."""

import json
import subprocess
import sys
from typing import Any

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.runtime.configuration import load_model_pin

from .conftest import ControlledService

INPUT = "B02-S003-PO01"


@pytest.mark.parametrize("version", ["0.40.7", "0.40.12"])
def test_native_correction_and_identity(
    service: ControlledService, gold: dict[str, Any], version: str
) -> None:
    service.native = True
    service.replacements["/api/version"] = {"version": version}
    docker_installation = service.project / "results/setup/installation.json"
    docker_installation.unlink()
    service.responses = ["{}", json.dumps(gold)]

    result = service.invoke("run", "--run-id", "native-correction", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/native-correction")
    assert len(records) == 1
    record = records[0]
    assert record.runtime.value == "ollama-native"
    assert all(attempt.runtime_version == version for attempt in record.attempts)
    assert manifest.setup["local"]["runtime"]["version"] == version
    assert all(
        attempt.model_digest == load_model_pin(service.project, native=True).digest
        for attempt in record.attempts
    )
    assert record.extraction == gold
    assert [attempt.outcome.value for attempt in record.attempts] == ["invalid", "valid"]
    assert manifest.setup["local"]["mode"] == "native"
    assert manifest.setup["local"]["loaded"]["size_vram"] == 80
    assert not docker_installation.exists()
    assert not (service.project / "results/budget-ledger.json").exists()
    assert all(authorization is None for _, _, authorization in service.requests)
    assert all(not path.startswith("/api/v1/") for path, _, _ in service.requests)
    chats = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(chats) == 4
    assert all(payload is not None and payload["truncate"] is False for payload in chats)
    assert all(payload is not None and payload["shift"] is False for payload in chats)


@pytest.mark.parametrize("defect", ["version", "digest", "missing", "context", "render"])
@pytest.mark.parametrize("version", ["0.40.7", "0.40.12"])
def test_native_mismatch_never_generates(
    service: ControlledService, defect: str, version: str
) -> None:
    service.native = True
    service.replacements["/api/version"] = {"version": version}
    pin = load_model_pin(service.project, native=True)

    if defect == "version":
        service.replacements["/api/version"] = {"version": "unreviewed-version"}
    elif defect == "digest":
        service.replacements["/api/tags"] = {
            "models": [{"name": pin.model, "digest": "b" * 64, "size": 100}]
        }
    elif defect == "missing":
        service.replacements["/api/tags"] = {"models": []}
    elif defect == "context":
        service.replacements["/api/ps"] = {
            "models": [
                {
                    "name": pin.model,
                    "digest": pin.digest,
                    "size": 100,
                    "size_vram": 100,
                    "context_length": 4096,
                }
            ]
        }
    else:
        # The simulated unsupported render API returns no evidence, never generation.
        service.replacements["/api/chat"] = {"model": pin.model}

    result = service.invoke("run", "--run-id", "native-blocked", "--input", INPUT)

    assert result.returncode == 2, result.stdout + result.stderr
    assert not service.generation_started.is_set()
    assert not any(path == "/api/pull" for path, _, _ in service.requests)
    assert all(
        payload is not None and payload.get("_debug_render_only") is True
        for path, payload, _ in service.requests
        if path == "/api/chat"
    )


@pytest.mark.parametrize("version", ["0.40.7", "0.40.12"])
def test_native_initialize_only_checks_existing_weights(
    service: ControlledService, version: str
) -> None:
    service.native = True
    service.replacements["/api/version"] = {"version": version}

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "extraction_service.runtime",
            "--project-dir",
            str(service.project),
            "initialize-native",
        ],
        env=service.environment(),
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["identity"]["runtime"] == "ollama-native"
    assert report["identity"]["runtime_version"] == version
    assert report["pulled"] is False
    assert report["inference_performed"] is False
    assert not any(
        path in {"/api/chat", "/api/generate", "/api/pull"} for path, _, _ in service.requests
    )
    assert (service.project / "results/setup/native-installation.json").exists()
    assert not (service.project / "results/budget-ledger.json").exists()


@pytest.mark.parametrize("version", ["0.40.6", "0.41.0", "1.0.0", "0.40.8-rc1"])
def test_native_unreviewed_series_stops_before_loading(
    service: ControlledService, version: str
) -> None:
    service.native = True
    service.replacements["/api/version"] = {"version": version}

    result = service.invoke("run", "--run-id", "unsupported-series", "--input", INPUT)

    assert result.returncode == 2, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"setup_error": "SetupError"}
    assert [path for path, _, _ in service.requests] == ["/api/version"]


def test_native_initialize_refuses_docker_mode_before_http(service: ControlledService) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "extraction_service.runtime",
            "--project-dir",
            str(service.project),
            "initialize-native",
        ],
        env=service.environment(),
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 2
    assert "Native initialization requires explicit native mode" in result.stdout
    assert service.requests == []
