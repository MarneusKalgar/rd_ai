"""Explicit native weight initialization; never start or replace the desktop app."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.preflight import preflight
from extraction_service.runtime.configuration import OllamaSetupSettings, load_model_pin
from extraction_service.runtime.ollama import initialize_model, model_runtime, wait_for_server
from extraction_service.runtime.storage import setup_lock, write_report
from extraction_service.runtime.workflows import selected_model


def initialize_native(project_dir: Path, model_id: str, client: JsonHttpClient) -> dict[str, Any]:
    """Pull only the missing pinned local model; no generation or budget mutation."""

    experiment = preflight(project_dir).experiment
    model = selected_model(experiment.models, model_id, "ollama")
    pin = load_model_pin(project_dir, native=True)
    pin.check(model)
    settings = OllamaSetupSettings()

    with setup_lock(project_dir / "results") as directory:
        version = wait_for_server(client, settings)

        pin.check_server_version(version)

        installed, pulled = initialize_model(client, pin, settings)
        runtime = model_runtime(client, pin, version, settings)
        identity = runtime.identity(model, native=True)
        report = {
            "mode": "native_initialization",
            "observed_at": datetime.now(UTC).isoformat(),
            "identity": identity.model_dump(mode="json"),
            "installed_bytes": installed.size,
            "pulled": pulled,
            "inference_performed": False,
            "budget_initialized": False,
        }
        write_report(directory / "native-installation.json", report)

    return report
