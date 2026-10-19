"""Explicit setup probes; generation calls never hide metadata or model-pull requests."""

import httpx

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.capabilities import (
    OllamaRuntime,
    OpenRouterEndpoint,
    WireModel,
    openrouter_endpoint,
)
from extraction_service.inference.http import JsonHttpClient
from extraction_service.runtime_types import NonEmptyText, Sha256


class _Version(WireModel):
    version: NonEmptyText


class _InstalledModel(WireModel):
    name: NonEmptyText
    digest: Sha256


class _Tags(WireModel):
    models: list[_InstalledModel]


class _ModelDetails(WireModel):
    capabilities: list[str]


def verify_openrouter(
    config: ModelConfig,
    settings: ApplicationSettings,
    *,
    timeout_seconds: float,
    transport: httpx.BaseTransport | None = None,
) -> OpenRouterEndpoint:
    """Read the public catalog and require the configured route and common parameters.

    No key or generation is needed. Catalog support does not establish that a
    provider accepts every keyword in the frozen schema; live smoke checks that.
    """

    if config.backend != "openrouter":
        raise ValueError("OpenRouter verification requires an OpenRouter model")

    client = JsonHttpClient(str(settings.openrouter_base_url), transport=transport)

    try:
        reply = client.get(f"models/{config.model}/endpoints", timeout_seconds)

        return openrouter_endpoint(reply.body, config)
    finally:
        client.close()


def verify_ollama(
    config: ModelConfig,
    settings: ApplicationSettings,
    *,
    timeout_seconds: float,
    transport: httpx.BaseTransport | None = None,
) -> OllamaRuntime:
    """Read installed server/version, tag digest and model capabilities without a pull.

    A missing tag is a setup failure. These probes do not install a model or
    silently substitute a different tag/runtime.
    """

    if config.backend != "ollama":
        raise ValueError("Ollama verification requires an Ollama model")

    client = JsonHttpClient(str(settings.ollama_base_url), transport=transport)

    try:
        version_reply = client.get("api/version", timeout_seconds)
        version = _Version.model_validate(version_reply.body)
        tags_reply = client.get("api/tags", timeout_seconds)
        tags = _Tags.model_validate(tags_reply.body)

        for model in tags.models:
            if model.name == config.model:
                details_reply = client.post("api/show", {"model": config.model}, timeout_seconds)
                details = _ModelDetails.model_validate(details_reply.body)
                runtime = OllamaRuntime(
                    version=version.version,
                    model_name=model.name,
                    model_digest=model.digest,
                    capabilities=frozenset(details.capabilities),
                )
                runtime.identity(config)

                return runtime

        raise ValueError("Configured Ollama model is not installed; initialize it explicitly")
    finally:
        client.close()
