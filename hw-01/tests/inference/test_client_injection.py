"""Adapter behavior through a borrowed post-only dependency, without HTTPX setup."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pytest

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.capabilities import OllamaRuntime, OpenRouterEndpoint
from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.http import HttpPoster, HttpReply
from extraction_service.inference.ollama import OllamaAdapter
from extraction_service.inference.openrouter import OpenRouterAdapter
from extraction_service.inference.types import GenerationRequest, ModelAdapter, ResponseKind


@dataclass
class ScriptedPoster:
    """Implement only the borrowed interface; adapters cannot close or configure it."""

    reply: HttpReply
    error: Exception | None = None
    calls: list[tuple[str, dict[str, Any], float]] = field(default_factory=list)

    def post(self, path: str, payload: dict[str, Any], timeout_seconds: float) -> HttpReply:
        self.calls.append((path, payload, timeout_seconds))

        if self.error is not None:
            raise self.error

        return self.reply


@pytest.fixture
def injected_adapter_factory(
    provider_config: ModelConfig,
    local_config: ModelConfig,
    endpoint: OpenRouterEndpoint,
    runtime: OllamaRuntime,
) -> Callable[[str, HttpPoster], ModelAdapter]:
    def create(backend: str, client: HttpPoster) -> ModelAdapter:
        if backend == "openrouter":
            return OpenRouterAdapter(provider_config, endpoint, http_client=client)

        if backend == "ollama":
            return OllamaAdapter(local_config, runtime, http_client=client)

        raise ValueError(f"Unknown test backend: {backend}")

    return create


@pytest.mark.parametrize(
    "backend,path", [("openrouter", "chat/completions"), ("ollama", "api/chat")]
)
def test_adapter_uses_post_only_client_and_parses_its_reply(
    backend: str,
    path: str,
    generation: GenerationRequest,
    response_body: Callable[[str], dict[str, Any]],
    injected_adapter_factory: Callable[[str, HttpPoster], ModelAdapter],
) -> None:
    body = response_body(backend)
    raw_body = json.dumps(body)
    reply = HttpReply(body=body, raw_body=raw_body, duration_ms=17.0, credentials_redacted=False)
    client = ScriptedPoster(reply)
    adapter = injected_adapter_factory(backend, client)

    result = adapter.generate(generation)

    assert len(client.calls) == 1
    sent_path, payload, timeout = client.calls[0]
    assert sent_path == path
    assert timeout == 12.0
    assert payload["model"] == adapter.identity.model_name
    assert payload["messages"][1] == {"role": "user", "content": generation.source_text}
    assert result.kind is ResponseKind.COMPLETED
    assert result.raw_response == "  {invalid PO}\n"
    assert result.raw_http_body == raw_body
    assert result.duration_ms == 17.0


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("failure_type", ["transport", "unexpected"])
def test_adapter_propagates_the_original_exception_without_retry(
    backend: str,
    failure_type: str,
    generation: GenerationRequest,
    injected_adapter_factory: Callable[[str, HttpPoster], ModelAdapter],
) -> None:
    original: Exception

    if failure_type == "transport":
        evidence = FailureEvidence(
            kind=FailureKind.TIMEOUT,
            retryable=True,
            message="Scripted timeout",
            duration_ms=9.0,
        )
        original = ModelTransportError(evidence)
    else:
        original = RuntimeError("Unexpected client defect")

    unused_reply = HttpReply(body={}, raw_body="{}", duration_ms=0.0, credentials_redacted=False)
    client = ScriptedPoster(reply=unused_reply, error=original)
    adapter = injected_adapter_factory(backend, client)

    with pytest.raises(type(original)) as failure:
        adapter.generate(generation)

    assert failure.value is original
    assert len(client.calls) == 1
