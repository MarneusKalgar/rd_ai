"""Verify the selected local deployment before composing its borrowed adapter."""

from pathlib import Path
from time import perf_counter
from typing import Any

from extraction_service.application.admission import LocalAdmission
from extraction_service.application.tokenization import GemmaTokenizer
from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings, OllamaMode
from extraction_service.execution.types import ExecutionTarget
from extraction_service.inference.ollama.adapter import OllamaAdapter
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.runtime.configuration import (
    OllamaSetupSettings,
    SetupSettings,
    load_model_pin,
)
from extraction_service.runtime.ollama import (
    installed_model,
    load_model,
    model_runtime,
    wait_for_server,
)
from extraction_service.runtime.workflows import Installation


def prepare_local(
    project_dir: Path, model: ModelConfig, settings: ApplicationSettings, client: JsonHttpClient
) -> tuple[ExecutionTarget, LocalAdmission, dict[str, Any]]:
    """Check weights/runtime policy; Docker additionally checks initialization."""

    native = settings.ollama_mode == OllamaMode.NATIVE
    local_settings = OllamaSetupSettings() if native else SetupSettings()
    pin = load_model_pin(project_dir, native=native)
    pin.check(model)
    version = wait_for_server(client, local_settings)

    pin.check_server_version(version)

    if isinstance(local_settings, SetupSettings):
        installation = Installation.model_validate_json(
            (project_dir / "results/setup/installation.json").read_bytes()
        )
        if (
            installation.image != local_settings.image
            or installation.runtime.version != version
            or installation.runtime.model_name != pin.model
            or installation.runtime.model_digest != pin.digest
        ):
            raise ValueError("Local runtime differs from initialization evidence")

    if installed_model(client, pin, local_settings) is None:
        raise ValueError("Pinned local weights are missing; run explicit setup for this mode")

    runtime = model_runtime(client, pin, version, local_settings)
    started = perf_counter()
    loaded = load_model(client, pin, local_settings)
    load_ms = (perf_counter() - started) * 1000
    details = client.post("api/show", {"model": model.model, "verbose": True}, 60.0)
    info = details.body.get("model_info")

    if not isinstance(info, dict):
        raise ValueError("Installed tokenizer metadata unavailable")

    tokenizer = GemmaTokenizer(info)
    adapter = OllamaAdapter(
        model, runtime, http_client=client, native=native, context_length=loaded.context_length
    )
    admission = LocalAdmission(
        client, pin, tokenizer, loaded.context_length, runtime_version=version
    )
    target = ExecutionTarget(adapter=adapter, endpoint=str(settings.ollama_base_url))
    evidence = {
        "mode": settings.ollama_mode.value,
        "endpoint": str(settings.ollama_base_url),
        "loaded": loaded.model_dump(mode="json"),
        "processor": "cpu" if loaded.size_vram == 0 else "gpu_or_mixed",
        "load_duration_ms": load_ms,
        "tokenizer_sha256": tokenizer.sha256,
        "runtime": runtime.model_dump(mode="json"),
    }

    return target, admission, evidence
