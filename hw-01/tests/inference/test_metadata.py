"""Catalog capabilities and installed runtime identity, independent of model inference."""

import json
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.capabilities import OllamaRuntime, OpenRouterEndpoint
from extraction_service.inference.metadata import verify_ollama, verify_openrouter
from extraction_service.inference.ollama import OllamaAdapter
from extraction_service.inference.openrouter import OpenRouterAdapter
from extraction_service.inference.types import GenerationRequest


@pytest.fixture
def catalog() -> dict[str, Any]:
    return {
        "data": {
            "id": "google/gemini-3.8-flash",
            "endpoints": [
                {
                    "model_id": "google/gemini-3.8-flash",
                    "tag": "google-ai-studio",
                    "provider_name": "Google AI Studio",
                    "supported_parameters": [
                        "temperature",
                        "top_p",
                        "max_tokens",
                        "response_format",
                        "structured_outputs",
                    ],
                    "max_completion_tokens": 65536,
                    "pricing": {"prompt": "0.00000075", "completion": "0.00000375"},
                }
            ],
        }
    }


@pytest.mark.parametrize("missing", [None, "temperature", "top_p", "structured_outputs"])
def test_catalog_probe_checks_route_parameters_and_pricing(
    missing: str | None,
    catalog: dict[str, Any],
    settings: ApplicationSettings,
    provider_config: ModelConfig,
) -> None:
    captured: list[httpx.Request] = []

    if missing is not None:
        catalog["data"]["endpoints"][0]["supported_parameters"].remove(missing)

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)

        return httpx.Response(200, json=catalog)

    transport = httpx.MockTransport(handle)

    if missing is None:
        endpoint = verify_openrouter(
            provider_config, settings, timeout_seconds=3.0, transport=transport
        )
        assert endpoint.provider_slug == "google-ai-studio"
        assert endpoint.pricing["prompt"] == "0.00000075"
        assert endpoint.max_output_tokens == 65536
    else:
        with pytest.raises(ValueError, match=f"lacks required parameters: {missing}"):
            verify_openrouter(provider_config, settings, timeout_seconds=3.0, transport=transport)

    assert len(captured) == 1
    assert captured[0].method == "GET"
    assert captured[0].url.path == "/api/v1/models/google/gemini-3.8-flash/endpoints"
    assert "Authorization" not in captured[0].headers


@pytest.mark.parametrize("defect", ["model", "route"])
def test_catalog_identity_mismatch_is_rejected(
    defect: str,
    catalog: dict[str, Any],
    settings: ApplicationSettings,
    provider_config: ModelConfig,
) -> None:
    if defect == "model":
        catalog["data"]["id"] = "different-model"
        expected = "model identity differs"
    else:
        catalog["data"]["endpoints"][0]["tag"] = "google-vertex/us"
        expected = "provider endpoint was not found"

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=catalog))

    with pytest.raises(ValueError, match=expected):
        verify_openrouter(provider_config, settings, timeout_seconds=3.0, transport=transport)


def test_output_limit_rejected_before_http(
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    generation: GenerationRequest,
) -> None:
    limited = endpoint.model_copy(update={"max_output_tokens": 10})

    def unexpected(request: httpx.Request) -> httpx.Response:
        pytest.fail("An oversized request must not reach HTTP")

    adapter = OpenRouterAdapter(
        provider_config, settings, limited, transport=httpx.MockTransport(unexpected)
    )

    try:
        with pytest.raises(ValueError, match="exceed the verified endpoint limit"):
            adapter.generate(generation)
    finally:
        adapter.close()


@dataclass
class InstalledServer:
    """Script only setup endpoints; an inference or pull request fails the test."""

    installed: bool = True
    capabilities: list[str] = field(default_factory=lambda: ["completion", "vision"])
    paths: list[str] = field(default_factory=list)

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.paths.append(request.url.path)
        assert "Authorization" not in request.headers

        if request.url.path == "/api/version":
            assert request.method == "GET"

            return httpx.Response(200, json={"version": "0.40.5"})

        if request.url.path == "/api/tags":
            models = []

            if self.installed:
                models.append({"name": "gemma4:e4b-it-qat", "digest": "a" * 64})

            return httpx.Response(200, json={"models": models})

        assert request.url.path == "/api/show"
        assert request.method == "POST"
        assert json.loads(request.content) == {"model": "gemma4:e4b-it-qat"}

        return httpx.Response(200, json={"capabilities": self.capabilities})


def test_installed_identity_and_explicit_native_mode(
    settings: ApplicationSettings, local_config: ModelConfig
) -> None:
    server = InstalledServer()
    runtime = verify_ollama(
        local_config, settings, timeout_seconds=3.0, transport=httpx.MockTransport(server.handle)
    )
    adapter = OllamaAdapter(local_config, settings, runtime, native=True)

    try:
        assert adapter.identity.runtime == "ollama-native"
        assert adapter.identity.runtime_version == "0.40.5"
        assert adapter.identity.model_digest == "a" * 64
    finally:
        adapter.close()

    assert server.paths == ["/api/version", "/api/tags", "/api/show"]


@pytest.mark.parametrize("defect", ["missing", "capabilities"])
def test_unavailable_local_model_is_a_setup_failure(
    defect: str, settings: ApplicationSettings, local_config: ModelConfig
) -> None:
    server = InstalledServer()

    if defect == "missing":
        server.installed = False
        expected = "not installed"
    else:
        server.capabilities = ["embedding"]
        expected = "lacks text completion"

    with pytest.raises(ValueError, match=expected):
        verify_ollama(
            local_config,
            settings,
            timeout_seconds=3.0,
            transport=httpx.MockTransport(server.handle),
        )

    assert "/api/chat" not in server.paths
    assert "/api/pull" not in server.paths


def test_runtime_model_mismatch_rejected(
    settings: ApplicationSettings, local_config: ModelConfig, runtime: OllamaRuntime
) -> None:
    wrong_runtime = runtime.model_copy(update={"model_name": "other-tag"})

    with pytest.raises(ValueError, match="does not match configuration"):
        OllamaAdapter(local_config, settings, wrong_runtime)


def test_provider_key_required_only_for_generation_adapter(
    provider_config: ModelConfig, endpoint: OpenRouterEndpoint
) -> None:
    without_key = ApplicationSettings()

    with pytest.raises(ValueError, match="requires OPENROUTER_API_KEY"):
        OpenRouterAdapter(provider_config, without_key, endpoint)


def test_provider_route_mismatch_rejected_before_generation(
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
) -> None:
    wrong_route = provider_config.model_copy(update={"serving_provider": "other-provider"})

    with pytest.raises(ValueError, match="verified serving-provider slug"):
        OpenRouterAdapter(wrong_route, settings, endpoint)
