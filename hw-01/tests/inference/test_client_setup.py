"""Real client scopes: sharing, service isolation and cleanup during stack unwinding."""

import json
from collections.abc import Callable
from contextlib import AbstractContextManager, ExitStack
from typing import Any

import httpx
import pytest
from pydantic import AnyHttpUrl

from extraction_service.configuration.models import ModelConfig, SamplingConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.capabilities import OllamaRuntime, OpenRouterEndpoint
from extraction_service.inference.client_setup import (
    ollama_client,
    openrouter_client,
    openrouter_metadata_client,
)
from extraction_service.inference.errors import FailureKind, ModelTransportError
from extraction_service.inference.http import JsonHttpClient
from extraction_service.inference.ollama import OllamaAdapter
from extraction_service.inference.openrouter import OpenRouterAdapter
from extraction_service.inference.types import GenerationRequest, ModelAdapter


class TrackingTransport(httpx.MockTransport):
    """Observe actual client cleanup while retaining HTTPX request handling."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        super().__init__(handler)
        self.close_calls = 0

    def close(self) -> None:
        self.close_calls += 1
        super().close()


def client_scope(
    kind: str, settings: ApplicationSettings, transport: httpx.BaseTransport
) -> AbstractContextManager[JsonHttpClient]:
    if kind == "openrouter":
        return openrouter_client(settings, transport=transport)

    if kind == "metadata":
        return openrouter_metadata_client(settings, transport=transport)

    if kind == "ollama":
        return ollama_client(settings, transport=transport)

    raise ValueError(f"Unknown test client kind: {kind}")


@pytest.mark.parametrize(
    "kind,expected_url,expected_authorization",
    [
        ("openrouter", "https://router.invalid/custom/v1/probe", "Bearer adapter-test-credential"),
        ("metadata", "https://router.invalid/custom/v1/probe", None),
        ("ollama", "http://runtime.invalid:11434/probe", None),
    ],
)
@pytest.mark.parametrize("body_failure", [False, True])
def test_scopes_configure_clients_and_close_once_without_consuming_errors(
    kind: str,
    expected_url: str,
    expected_authorization: str | None,
    body_failure: bool,
    settings: ApplicationSettings,
) -> None:
    configured = settings.model_copy(
        update={
            "openrouter_base_url": AnyHttpUrl("https://router.invalid/custom/v1"),
            "ollama_base_url": AnyHttpUrl("http://runtime.invalid:11434"),
        }
    )
    captured: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)

        return httpx.Response(200, json={"accepted": True})

    transport = TrackingTransport(handle)
    original = RuntimeError("Application failed after a request")

    def execute() -> None:
        with client_scope(kind, configured, transport) as client:
            assert captured == []  # Construction performs no hidden requests.
            reply = client.post("probe", {"input": "neutral"}, 3.0)
            assert reply.body == {"accepted": True}
            assert transport.close_calls == 0

            if body_failure:
                raise original

    if body_failure:
        with pytest.raises(RuntimeError) as failure:
            execute()

        assert failure.value is original
    else:
        execute()

    assert transport.close_calls == 1
    assert len(captured) == 1
    assert str(captured[0].url) == expected_url
    assert captured[0].headers.get("Authorization") == expected_authorization


def test_catalog_and_generation_scopes_keep_authentication_separate(
    settings: ApplicationSettings,
) -> None:
    captured: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)

        return httpx.Response(200, json={"accepted": True})

    generation_transport = TrackingTransport(handle)
    metadata_transport = TrackingTransport(handle)

    with ExitStack() as clients:
        generation = clients.enter_context(
            openrouter_client(settings, transport=generation_transport)
        )
        metadata = clients.enter_context(
            openrouter_metadata_client(settings, transport=metadata_transport)
        )

        generation.post("chat/completions", {}, 3.0)
        metadata.get("models/example/endpoints", 3.0)
        generation.post("chat/completions", {}, 3.0)

        assert generation_transport.close_calls == 0
        assert metadata_transport.close_calls == 0

    assert len(captured) == 3
    assert captured[0].headers["Authorization"] == "Bearer adapter-test-credential"
    assert "Authorization" not in captured[1].headers
    assert captured[2].headers["Authorization"] == "Bearer adapter-test-credential"
    assert generation_transport.close_calls == 1
    assert metadata_transport.close_calls == 1


def test_native_and_docker_ollama_scopes_use_their_explicit_urls(
    settings: ApplicationSettings,
    local_config: ModelConfig,
    runtime: OllamaRuntime,
    generation: GenerationRequest,
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    captured: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)

        return httpx.Response(200, json=response_body("ollama"))

    docker_transport = TrackingTransport(handle)
    native_transport = TrackingTransport(handle)
    native_settings = settings.model_copy(
        update={"ollama_base_url": AnyHttpUrl("http://host.docker.internal:11434")}
    )

    with ExitStack() as clients:
        docker_http = clients.enter_context(ollama_client(settings, transport=docker_transport))
        native_http = clients.enter_context(
            ollama_client(native_settings, transport=native_transport)
        )
        docker = OllamaAdapter(local_config, runtime, http_client=docker_http)
        native = OllamaAdapter(local_config, runtime, http_client=native_http, native=True)

        docker_result = docker.generate(generation)
        native_result = native.generate(generation)
        docker.generate(generation)

    assert len(captured) == 3
    assert str(captured[0].url) == "http://ollama:11434/api/chat"
    assert str(captured[1].url) == "http://host.docker.internal:11434/api/chat"
    assert captured[2].url == captured[0].url
    assert docker_result.identity.runtime == "ollama-docker"
    assert native_result.identity.runtime == "ollama-native"
    assert docker_transport.close_calls == 1
    assert native_transport.close_calls == 1


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
def test_compatible_adapters_share_a_client_without_changing_each_others_requests(
    backend: str,
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    local_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    runtime: OllamaRuntime,
    generation: GenerationRequest,
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    captured: list[httpx.Request] = []
    payloads: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        payload = json.loads(request.content)
        payloads.append(payload)
        body = response_body(backend)
        body["model"] = payload["model"]

        return httpx.Response(200, json=body)

    transport = TrackingTransport(handle)
    alternate_sampling = SamplingConfig(
        id="alternate", temperature=0.7, top_p=0.8, max_output_tokens=789
    )
    alternate_request = generation.model_copy(update={"sampling": alternate_sampling})
    first: ModelAdapter
    second: ModelAdapter

    with client_scope(backend, settings, transport) as client:
        if backend == "openrouter":
            alternate_config = provider_config.model_copy(
                update={"id": "other-provider-model", "model": "google/gemini-3.1-flash-lite"}
            )
            alternate_endpoint = endpoint.model_copy(
                update={"model_name": alternate_config.model, "provider_slug": "other-route"}
            )
            alternate_config = alternate_config.model_copy(
                update={"serving_provider": "other-route"}
            )
            first = OpenRouterAdapter(provider_config, endpoint, http_client=client)
            second = OpenRouterAdapter(alternate_config, alternate_endpoint, http_client=client)
        else:
            alternate_config = local_config.model_copy(
                update={"id": "other-local-model", "model": "other-local:small"}
            )
            alternate_runtime = runtime.model_copy(update={"model_name": alternate_config.model})
            first = OllamaAdapter(local_config, runtime, http_client=client)
            second = OllamaAdapter(alternate_config, alternate_runtime, http_client=client)

        first_result = first.generate(generation)
        second_result = second.generate(alternate_request)
        repeated_result = first.generate(generation)

        assert transport.close_calls == 0
        assert first_result.identity == first.identity
        assert second_result.identity == second.identity
        assert repeated_result.identity == first.identity
        assert first_result.raw_response == "  {invalid PO}\n"
        assert second_result.raw_response == "  {invalid PO}\n"

    assert transport.close_calls == 1
    assert len(captured) == 3
    assert payloads[0] == payloads[2]
    assert payloads[0]["model"] == first.identity.model_name
    assert payloads[1]["model"] == second.identity.model_name
    assert captured[0].url == captured[1].url == captured[2].url
    authorization = "Bearer adapter-test-credential" if backend == "openrouter" else None

    for request in captured:
        assert request.headers.get("Authorization") == authorization

    if backend == "openrouter":
        assert payloads[0]["provider"]["only"] == ["google-ai-studio"]
        assert payloads[1]["provider"]["only"] == ["other-route"]
        assert payloads[0]["max_tokens"] == 512
        assert payloads[1]["max_tokens"] == 789
    else:
        assert payloads[0]["options"]["num_predict"] == 512
        assert payloads[1]["options"]["num_predict"] == 789


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
def test_generation_timeout_propagates_out_of_the_client_scope(
    backend: str,
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    local_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    runtime: OllamaRuntime,
    generation: GenerationRequest,
) -> None:
    captured: list[httpx.Request] = []

    def timeout(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        raise httpx.ReadTimeout("Scripted request timeout", request=request)

    transport = TrackingTransport(timeout)
    adapter: ModelAdapter

    with pytest.raises(ModelTransportError) as failure:
        with client_scope(backend, settings, transport) as client:
            if backend == "openrouter":
                adapter = OpenRouterAdapter(provider_config, endpoint, http_client=client)
            else:
                adapter = OllamaAdapter(local_config, runtime, http_client=client)

            adapter.generate(generation)

    assert failure.value.evidence.kind is FailureKind.TIMEOUT
    assert failure.value.evidence.message == "Scripted request timeout"
    assert len(captured) == 1
    assert transport.close_calls == 1


@pytest.mark.parametrize("defect", ["route", "runtime"])
def test_partial_adapter_setup_closes_all_registered_clients(
    defect: str,
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    local_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    runtime: OllamaRuntime,
) -> None:
    def unexpected(request: httpx.Request) -> httpx.Response:
        pytest.fail("Adapter construction must not make a request")

    provider_transport = TrackingTransport(unexpected)
    local_transport = TrackingTransport(unexpected)
    expected = "verified serving-provider slug" if defect == "route" else "does not match"

    with pytest.raises(ValueError, match=expected):
        with ExitStack() as clients:
            provider = clients.enter_context(
                openrouter_client(settings, transport=provider_transport)
            )
            local = clients.enter_context(ollama_client(settings, transport=local_transport))

            if defect == "route":
                OllamaAdapter(local_config, runtime, http_client=local)
                wrong_route = provider_config.model_copy(update={"serving_provider": "wrong"})
                OpenRouterAdapter(wrong_route, endpoint, http_client=provider)
            else:
                OpenRouterAdapter(provider_config, endpoint, http_client=provider)
                wrong_runtime = runtime.model_copy(update={"model_name": "wrong:tag"})
                OllamaAdapter(local_config, wrong_runtime, http_client=local)

    assert provider_transport.close_calls == 1
    assert local_transport.close_calls == 1
