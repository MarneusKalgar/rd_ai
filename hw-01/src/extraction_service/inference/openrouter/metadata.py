"""Explicit public OpenRouter catalog probes without inference requests."""

import httpx

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.openrouter.capabilities import (
    OpenRouterEndpoint,
    openrouter_endpoint,
)
from extraction_service.inference.transport.client_setup import openrouter_metadata_client


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

    with openrouter_metadata_client(settings, transport=transport) as client:
        reply = client.get(f"models/{config.model}/endpoints", timeout_seconds)

        return openrouter_endpoint(reply.body, config)
