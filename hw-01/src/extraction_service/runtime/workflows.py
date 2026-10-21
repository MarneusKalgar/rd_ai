"""Coordinate explicit setup with borrowed HTTP; provider execution is absent."""

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from time import perf_counter
from typing import Any

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.preflight import preflight
from extraction_service.runtime.capacity import measure_capacity
from extraction_service.runtime.configuration import CapacityScope, SetupSettings, load_model_pin
from extraction_service.runtime.context import context_inventory, prepared_requests
from extraction_service.runtime.errors import SetupError
from extraction_service.runtime.ollama import (
    InstalledModel,
    initialize_model,
    installed_model,
    load_model,
    model_runtime,
    unload_model,
    wait_for_server,
)
from extraction_service.runtime.selection import select_capacity_requests
from extraction_service.runtime.storage import setup_lock, verify_storage, write_report
from extraction_service.runtime_types import StrictModel


class Installation(StrictModel):
    """Persistent identity established only after a successful exact-model check."""

    image: str
    runtime: OllamaRuntime
    initialized_at: str
    installed_bytes: int
    initialization_duration_ms: float


class ReadinessStatus(StrEnum):
    READY = "ready"
    BLOCKED = "blocked"


def selected_model(models: list[ModelConfig], model_id: str, backend: str) -> ModelConfig:
    """Select exactly one explicit mode; listing a candidate never schedules it."""

    for model in models:
        if model.id == model_id and model.backend == backend:
            return model

    raise SetupError("Selected model is missing or belongs to another runtime")


def provider_setup(project_dir: Path, model_id: str) -> dict[str, Any]:
    """Validate public artifacts/storage only; no key, provider HTTP or Ollama calls."""

    report = preflight(project_dir)
    model = selected_model(report.experiment.models, model_id, "openrouter")

    return {
        "mode": "provider_setup_offline",
        "model_id": model.id,
        "model_name": model.model,
        "input_count": report.input_count,
        "storage": verify_storage(project_dir / "results"),
        "provider_inference_performed": False,
        "provider_execution_requires_human_approval": True,
        "budget_initialized": False,
    }


def local_setup(
    project_dir: Path,
    model_id: str,
    settings: SetupSettings,
    client: JsonHttpClient,
    *,
    initialize: bool,
    capacity_scope: CapacityScope = CapacityScope.REPRESENTATIVE,
) -> dict[str, Any]:
    """Initialize explicitly or inspect a prior installation, then attempt a cold load.

    Identity failures propagate; readiness never accepts a replacement model.
    Load failures are saved with a blocked status and actionable resource evidence.
    No setup path creates, reopens or resets a budget ledger.
    """

    preflight_report = preflight(project_dir)
    experiment = preflight_report.experiment
    model = selected_model(experiment.models, model_id, "ollama")
    pin = load_model_pin(project_dir)
    pin.check(model)
    storage = verify_storage(project_dir / "results")

    with setup_lock(project_dir / "results") as directory:
        version = wait_for_server(client, settings)

        if version != pin.server_version:
            raise SetupError("Ollama server differs from the reviewed version in the model pin")

        path = directory / "installation.json"
        previous = Installation.model_validate_json(path.read_text()) if path.exists() else None

        if previous is not None:
            if previous.image != settings.image or previous.runtime.version != version:
                raise SetupError("Ollama image/version differs from initialization evidence")

            if (
                previous.runtime.model_name != pin.model
                or previous.runtime.model_digest != pin.digest
            ):
                raise SetupError("Model pin differs from initialization evidence")

        started = perf_counter()
        installed: InstalledModel | None

        if initialize:
            installed, pulled = initialize_model(client, pin, settings)
        else:
            if previous is None:
                raise SetupError("No initialization evidence; run make setup-local first")

            installed = installed_model(client, pin, settings)
            pulled = False

            if installed is None:
                raise SetupError("Initialized model is missing; run explicit local setup")

        pull_duration_ms = (perf_counter() - started) * 1000
        runtime = model_runtime(client, pin, version, settings)
        runtime.identity(model)
        installation = previous or Installation(
            image=settings.image,
            runtime=runtime,
            initialized_at=datetime.now(UTC).isoformat(),
            installed_bytes=installed.size,
            initialization_duration_ms=pull_duration_ms,
        )

        if initialize and previous is None:
            write_report(path, installation.model_dump(mode="json"))

        report: dict[str, Any] = {
            "status": ReadinessStatus.BLOCKED,
            "observed_at": datetime.now(UTC).isoformat(),
            "mode": "local_setup_diagnostics",
            "installation": installation.model_dump(mode="json"),
            "storage": storage,
            "pulled": pulled,
            "installed_bytes": installed.size,
            "initialization_duration_ms": pull_duration_ms,
            "requested_context_length": settings.context_length,
            "request_inventory": context_inventory(project_dir, experiment),
            "provider_inference_performed": False,
            "budget_initialized": False,
        }
        started = perf_counter()

        try:
            loaded = load_model(client, pin, settings)
        except ModelTransportError as error:
            report["load_error"] = {
                "kind": error.evidence.kind.value,
                "http_status": error.evidence.status_code,
                "body": error.evidence.raw_http_body,
                "action": "Inspect Ollama logs and Docker memory allocation; retry readiness "
                "after resolving load failure. Do not substitute a model or shorten inputs.",
            }
        else:
            report["loaded_model"] = loaded.model_dump(mode="json")
            report["processor"] = "cpu" if loaded.size_vram == 0 else "gpu_or_mixed"

        report["load_duration_ms"] = (perf_counter() - started) * 1000

        if "loaded_model" in report:
            started = perf_counter()
            all_requests = list(prepared_requests(project_dir, experiment))
            selected_requests = select_capacity_requests(all_requests, capacity_scope)
            capacity = measure_capacity(client, selected_requests, pin, settings)
            capacity.update(
                scope=capacity_scope.value,
                prepared_request_count=len(all_requests),
                selected_request_count=len(selected_requests),
                selection_method=(
                    "all_prepared_requests"
                    if capacity_scope == CapacityScope.EXHAUSTIVE
                    else "smallest_middle_largest_initial_message_bytes_per_variant"
                ),
                all_prepared_requests_verified=(
                    capacity["token_capacity_verified"]
                    and len(selected_requests) == len(all_requests)
                ),
                actual_requests_require_admission=True,
            )
            report["capacity"] = capacity
            report["capacity_duration_ms"] = (perf_counter() - started) * 1000

            if capacity["token_capacity_verified"]:
                report["status"] = ReadinessStatus.READY

        if report["status"] == ReadinessStatus.BLOCKED and "loaded_model" in report:
            try:
                unload_model(client, pin, settings)
            except ModelTransportError, ValueError:
                report["unload_acknowledged"] = False
                report["cleanup_action"] = "Run make down to release local model memory"
            else:
                report["unload_acknowledged"] = True

        report_name = (
            "capacity-exhaustive.json"
            if capacity_scope == CapacityScope.EXHAUSTIVE
            else "readiness.json"
        )
        write_report(directory / report_name, report)

        return report
