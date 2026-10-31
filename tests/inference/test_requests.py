"""Request translation through real adapters and controlled HTTP transports."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from extraction_service.configuration.models import SamplingConfig
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.types import GenerationRequest, ModelAdapter


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("temperature,top_p", [(0.0, 1.0), (0.2, 0.9)])
def test_exact_schema_sampling_and_single_request(
    backend: str,
    temperature: float,
    top_p: float,
    contract: ExtractionContract,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    sampling = SamplingConfig(
        id="selected", temperature=temperature, top_p=top_p, max_output_tokens=512
    )
    request = generation.model_copy(update={"sampling": sampling})
    captured: list[httpx.Request] = []

    def handle(incoming: httpx.Request) -> httpx.Response:
        captured.append(incoming)

        return httpx.Response(200, json=response_body(backend))

    adapter = adapter_factory(backend, httpx.MockTransport(handle))

    result = adapter.generate(request)

    assert len(captured) == 1
    incoming = captured[0]
    payload = json.loads(incoming.content)
    assert incoming.method == "POST"
    assert incoming.extensions["timeout"]["read"] == 12.0
    assert payload["stream"] is False
    assert payload["messages"][1] == {"role": "user", "content": generation.source_text}
    system = payload["messages"][0]
    assert system["role"] == "system"
    assert system["content"].startswith(generation.instructions + "\n\nJSON Schema:\n")
    embedded_schema = json.loads(system["content"].split("\n\nJSON Schema:\n")[1])
    assert embedded_schema == contract.schema_for_provider()
    assert result.raw_response == "  {invalid PO}\n"
    assert result.kind == "completed"  # PO validity belongs to the coordinator.

    if backend == "openrouter":
        assert str(incoming.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert incoming.headers["Authorization"] == "Bearer adapter-test-credential"
        assert payload["model"] == "google/gemini-3.8-flash"
        assert payload["temperature"] == temperature
        assert payload["top_p"] == top_p
        assert payload["max_tokens"] == 512
        assert payload["provider"] == {
            "only": ["google-ai-studio"],
            "allow_fallbacks": False,
            "require_parameters": True,
        }
        assert payload["plugins"] == []
        assert payload["response_format"] == {
            "type": "json_schema",
            "json_schema": {
                "name": "purchase_order_extraction",
                "strict": True,
                "schema": contract.schema_for_provider(),
            },
        }
    else:
        assert str(incoming.url) == "http://ollama:11434/api/chat"
        assert "Authorization" not in incoming.headers
        assert payload["model"] == "gemma4:e4b-it-qat"
        assert payload["options"] == {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": 512,
        }
        assert payload["format"] == contract.schema_for_provider()


def test_request_schema_is_independent_of_contract(
    generation: GenerationRequest, contract: ExtractionContract
) -> None:
    generation.output_schema["properties"]["purchaseOrderNumber"]["minLength"] = 0

    original = contract.schema_for_provider()
    assert original["properties"]["purchaseOrderNumber"]["minLength"] == 1
