"""Explicit installed-runtime probes without inference or model pulls."""

import httpx

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.transport.client_setup import ollama_client
from extraction_service.inference.wire_models import WireModel
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

    with ollama_client(settings, transport=transport) as client:
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
