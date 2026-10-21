"""Application-owned clients, installed identities and explicit route coverage."""

import json
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from typing import Any

from pydantic import TypeAdapter

from extraction_service.application.admission import (
    LocalAdmission,
    ProviderAdmission,
    ProviderCoverage,
)
from extraction_service.application.selection import RunOptions
from extraction_service.application.tokenization import GemmaTokenizer
from extraction_service.artifacts import artifact_path
from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.admission import AdmissionEvidence, RequestAdmission
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.types import ExecutionTarget
from extraction_service.inference.ollama.adapter import OllamaAdapter
from extraction_service.inference.openrouter.adapter import OpenRouterAdapter
from extraction_service.inference.openrouter.metadata import verify_openrouter
from extraction_service.inference.transport.client_setup import ollama_client, openrouter_client
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.runtime.configuration import SetupSettings, load_model_pin
from extraction_service.runtime.ollama import (
    installed_model,
    load_model,
    model_runtime,
    wait_for_server,
)
from extraction_service.runtime.storage import setup_lock
from extraction_service.runtime.workflows import Installation


@dataclass(frozen=True)
class PreparedTarget:
    target: ExecutionTarget
    admission: RequestAdmission
    pricing: VerifiedPricing | None = None


class SelectedAdmission:
    def __init__(self, targets: dict[str, PreparedTarget]) -> None:
        self._targets = targets

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        return self._targets[identity.model_id].admission.check(request, identity)


def _prepare_local(
    project_dir: Path,
    model: ModelConfig,
    settings: ApplicationSettings,
    client: JsonHttpClient,
) -> tuple[PreparedTarget, dict[str, Any]]:
    """Verify initialized identity and context; keep empty-load time outside input latency."""

    local_settings = SetupSettings()
    pin = load_model_pin(project_dir)
    pin.check(model)
    version = wait_for_server(client, local_settings)
    installation = Installation.model_validate_json(
        (project_dir / "results/setup/installation.json").read_bytes()
    )

    if (
        version != pin.server_version
        or installation.image != local_settings.image
        or installation.runtime.version != version
        or installation.runtime.model_name != pin.model
        or installation.runtime.model_digest != pin.digest
    ):
        raise ValueError("Local runtime differs from initialization evidence")

    if installed_model(client, pin, local_settings) is None:
        raise ValueError("Initialized weights are missing")

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
        model, runtime, http_client=client, context_length=loaded.context_length
    )
    admission = LocalAdmission(client, pin, tokenizer, loaded.context_length)
    target = ExecutionTarget(adapter=adapter, endpoint=str(settings.ollama_base_url))
    evidence = {
        "loaded": loaded.model_dump(mode="json"),
        "load_duration_ms": load_ms,
        "tokenizer_sha256": tokenizer.sha256,
        "runtime": runtime.model_dump(mode="json"),
    }

    return PreparedTarget(target=target, admission=admission), evidence


def _provider_coverage(
    project_dir: Path, model_id: str, options: RunOptions
) -> ProviderCoverage | None:
    if options.coverage_file is None:
        return None

    path = artifact_path(project_dir, options.coverage_file)
    coverages = TypeAdapter(dict[str, ProviderCoverage]).validate_json(path.read_bytes())

    return coverages.get(model_id)


def _prepare_provider(
    model: ModelConfig,
    settings: ApplicationSettings,
    client: JsonHttpClient,
    coverage: ProviderCoverage | None,
) -> tuple[PreparedTarget, dict[str, Any]]:
    """Refresh capabilities; unavailable or stale pricing becomes an explicit budget stop."""

    endpoint = verify_openrouter(model, settings, timeout_seconds=10.0)

    if coverage is not None:
        try:
            coverage.check_catalog(endpoint)
        except ValueError:
            coverage = None

    adapter = OpenRouterAdapter(model, endpoint, http_client=client)
    target = ExecutionTarget(adapter=adapter, endpoint=str(settings.openrouter_base_url))

    if coverage is not None and target.dependency != coverage.pricing.dependency:
        coverage = None

    prepared = PreparedTarget(
        target=target,
        admission=ProviderAdmission(coverage),
        pricing=None if coverage is None else coverage.pricing,
    )
    evidence = (
        {"pricing_stop": "unsafe_pricing", "advertised_pricing": endpoint.pricing}
        if coverage is None
        else json.loads(coverage.model_dump_json())
    )

    return prepared, evidence


@contextmanager
def compose_targets(
    project_dir: Path,
    models: list[ModelConfig],
    options: RunOptions,
) -> Generator[tuple[dict[str, PreparedTarget], dict[str, Any]]]:
    """Own compatible client scopes; adapters borrow clients without lifecycle knowledge."""

    settings = ApplicationSettings.load(project_dir)
    targets = {}
    evidence: dict[str, Any] = {}

    if any(model.backend == "openrouter" for model in models) and not options.allow_provider:
        raise ValueError("Provider execution requires explicit approval and --allow-provider")

    with ExitStack() as stack:
        local_client = None
        provider_client = None

        for model in models:
            if model.backend == "ollama":
                if local_client is None:
                    stack.enter_context(setup_lock(project_dir / "results"))
                    local_client = stack.enter_context(ollama_client(settings))

                prepared, observed = _prepare_local(project_dir, model, settings, local_client)
            else:
                coverage = _provider_coverage(project_dir, model.id, options)

                if provider_client is None:
                    provider_client = stack.enter_context(openrouter_client(settings))

                prepared, observed = _prepare_provider(model, settings, provider_client, coverage)

            targets[model.id] = prepared
            evidence[model.id] = observed

        yield targets, evidence
