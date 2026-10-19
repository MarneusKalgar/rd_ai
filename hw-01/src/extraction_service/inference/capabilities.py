"""Verify model metadata before constructing an adapter; these calls do no inference."""

from typing import Any, Final

from pydantic import ConfigDict

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.types import ModelIdentity
from extraction_service.runtime_types import NonEmptyText, PositiveInt, Sha256, StrictModel

REQUIRED_OPENROUTER_PARAMETERS: Final[frozenset[str]] = frozenset(
    ("temperature", "top_p", "max_tokens", "response_format", "structured_outputs")
)


class WireModel(StrictModel):
    """Strict known wire fields; evolving remote extras remain in raw HTTP evidence."""

    model_config = ConfigDict(extra="allow")


class OpenRouterEndpoint(StrictModel):
    """A checked catalog endpoint; catalog support is distinct from live schema acceptance."""

    model_name: NonEmptyText
    provider_slug: NonEmptyText
    provider_name: NonEmptyText
    supported_parameters: frozenset[str]
    max_output_tokens: PositiveInt | None
    pricing: dict[str, Any]

    def check(self, config: ModelConfig) -> None:
        """Reject a different route or missing parameters before any paid request."""

        if config.backend != "openrouter" or config.model != self.model_name:
            raise ValueError("OpenRouter endpoint does not match the configured model")

        if config.serving_provider != self.provider_slug:
            raise ValueError("OpenRouter requires the verified serving-provider slug")

        missing = REQUIRED_OPENROUTER_PARAMETERS - self.supported_parameters

        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"OpenRouter endpoint lacks required parameters: {names}")


class _Endpoint(WireModel):
    model_id: str
    tag: str
    provider_name: str
    supported_parameters: list[str]
    max_completion_tokens: PositiveInt | None = None
    pricing: dict[str, Any]


class _CatalogModel(WireModel):
    id: str
    endpoints: list[_Endpoint]


class _Catalog(WireModel):
    data: _CatalogModel


def openrouter_endpoint(body: dict[str, Any], config: ModelConfig) -> OpenRouterEndpoint:
    """Select exactly the configured endpoint slug from public endpoint metadata."""

    catalog = _Catalog.model_validate(body)

    if catalog.data.id != config.model:
        raise ValueError("OpenRouter catalog model identity differs from configuration")

    for candidate in catalog.data.endpoints:
        if candidate.tag != config.serving_provider:
            continue

        endpoint = OpenRouterEndpoint(
            model_name=candidate.model_id,
            provider_slug=candidate.tag,
            provider_name=candidate.provider_name,
            supported_parameters=frozenset(candidate.supported_parameters),
            max_output_tokens=candidate.max_completion_tokens,
            pricing=candidate.pricing,
        )
        endpoint.check(config)

        return endpoint

    raise ValueError("Configured OpenRouter provider endpoint was not found")


class OllamaRuntime(StrictModel):
    """Identity read from the installed server and resolved model, without generation."""

    version: NonEmptyText
    model_name: NonEmptyText
    model_digest: Sha256
    capabilities: frozenset[str]

    def identity(self, config: ModelConfig, *, native: bool = False) -> ModelIdentity:
        """Require a matching installed text-completion model and preserve its digest."""

        if config.backend != "ollama" or config.model != self.model_name:
            raise ValueError("Installed Ollama model does not match configuration")

        if "completion" not in self.capabilities:
            raise ValueError("Installed Ollama model lacks text completion capability")

        return ModelIdentity(
            model_id=config.id,
            model_name=config.model,
            runtime="ollama-native" if native else "ollama-docker",
            runtime_version=self.version,
            model_digest=self.model_digest,
        )
