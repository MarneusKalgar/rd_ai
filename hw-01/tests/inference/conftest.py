"""Offline adapter fixtures with explicit wire examples and a harmless test credential."""

from collections.abc import Callable, Iterator
from contextlib import ExitStack
from typing import Any

import httpx
import pytest
from pydantic import SecretStr

from extraction_service.configuration.models import ModelConfig, SamplingConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.capabilities import OllamaRuntime, OpenRouterEndpoint
from extraction_service.inference.client_setup import ollama_client, openrouter_client
from extraction_service.inference.ollama import OllamaAdapter
from extraction_service.inference.openrouter import OpenRouterAdapter
from extraction_service.inference.types import GenerationRequest, ModelAdapter


@pytest.fixture
def settings() -> ApplicationSettings:
    return ApplicationSettings(OPENROUTER_API_KEY=SecretStr("adapter-test-credential"))


@pytest.fixture
def provider_config() -> ModelConfig:
    return ModelConfig(
        id="provider",
        backend="openrouter",
        model="google/gemini-3.8-flash",
        serving_provider="google-ai-studio",
    )


@pytest.fixture
def local_config() -> ModelConfig:
    return ModelConfig(id="local", backend="ollama", model="gemma4:e4b-it-qat")


@pytest.fixture
def endpoint() -> OpenRouterEndpoint:
    return OpenRouterEndpoint(
        model_name="google/gemini-3.8-flash",
        provider_slug="google-ai-studio",
        provider_name="Google AI Studio",
        supported_parameters=frozenset(
            ("temperature", "top_p", "max_tokens", "response_format", "structured_outputs")
        ),
        max_output_tokens=65536,
        pricing={"prompt": "0.00000075", "completion": "0.00000375"},
    )


@pytest.fixture
def runtime() -> OllamaRuntime:
    return OllamaRuntime(
        version="0.40.5",
        model_name="gemma4:e4b-it-qat",
        model_digest="a" * 64,
        capabilities=frozenset(("completion", "vision")),
    )


@pytest.fixture
def generation(contract: ExtractionContract) -> GenerationRequest:
    return GenerationRequest.from_contract(
        instructions="Extract the order. Do not invent missing values.",
        source_text="ORDER!A1 Purchase order | B1 PO-1001\nORDER!A2 Café supplies",
        contract=contract,
        sampling=SamplingConfig(id="sample", temperature=0.2, top_p=0.9, max_output_tokens=512),
        timeout_seconds=12.0,
    )


@pytest.fixture
def adapter_factory(
    settings: ApplicationSettings,
    provider_config: ModelConfig,
    local_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    runtime: OllamaRuntime,
) -> Iterator[Callable[[str, httpx.BaseTransport], ModelAdapter]]:
    with ExitStack() as clients:

        def create(backend: str, transport: httpx.BaseTransport) -> ModelAdapter:
            if backend == "openrouter":
                client = clients.enter_context(openrouter_client(settings, transport=transport))

                return OpenRouterAdapter(provider_config, endpoint, http_client=client)

            if backend == "ollama":
                client = clients.enter_context(ollama_client(settings, transport=transport))

                return OllamaAdapter(local_config, runtime, http_client=client)

            raise ValueError(f"Unknown test backend: {backend}")

        yield create


@pytest.fixture
def response_body() -> Callable[[str], dict[str, Any]]:
    def create(backend: str) -> dict[str, Any]:
        if backend == "openrouter":
            return {
                "id": "gen-test-01",
                "model": "google/gemini-3.8-flash-20260902",
                "provider": "Google AI Studio",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "native_finish_reason": "STOP",
                        "message": {"role": "assistant", "content": "  {invalid PO}\n"},
                    }
                ],
                "usage": {"prompt_tokens": 120, "completion_tokens": 14, "cost": 0.0002},
            }

        return {
            "model": "gemma4:e4b-it-qat",
            "message": {"role": "assistant", "content": "  {invalid PO}\n", "thinking": "private"},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 120,
            "eval_count": 14,
            "total_duration": 123456789,
            "load_duration": 12345,
        }

    return create
