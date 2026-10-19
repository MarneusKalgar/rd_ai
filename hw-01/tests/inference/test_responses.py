"""Finish state, exact model text and unknown-versus-zero usage evidence."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from extraction_service.inference.types import GenerationRequest, ModelAdapter, ResponseKind


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
def test_response_preserves_identity_usage_and_raw_envelope(
    backend: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body(backend)
    raw_body = json.dumps(body, indent=2) + "\n"
    transport = httpx.MockTransport(lambda request: httpx.Response(200, text=raw_body))
    adapter = adapter_factory(backend, transport)

    try:
        result = adapter.generate(generation)
    finally:
        adapter.close()

    assert result.raw_http_body == raw_body
    assert result.kind is ResponseKind.COMPLETED
    assert result.raw_response == "  {invalid PO}\n"
    assert result.input_tokens == 120
    assert result.output_tokens == 14
    assert result.duration_ms >= 0

    if backend == "openrouter":
        assert result.identity.serving_provider == "google-ai-studio"
        assert result.serving_provider == "Google AI Studio"
        assert result.reported_model == "google/gemini-3.8-flash-20260902"
        assert result.request_id == "gen-test-01"
        assert result.cost_usd == 0.0002
        assert result.native_finish_reason == "STOP"
    else:
        assert result.identity.runtime == "ollama-docker"
        assert result.identity.runtime_version == "0.40.5"
        assert result.identity.model_digest == "a" * 64
        assert result.reported_model == "gemma4:e4b-it-qat"
        assert result.cost_usd == 0.0
        assert result.total_duration_ns == 123456789
        assert result.load_duration_ns == 12345


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("zero_usage", [True, False])
def test_missing_usage_stays_unknown_and_zero_is_retained(
    backend: str,
    zero_usage: bool,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body(backend)

    if backend == "openrouter":
        body.pop("usage")

        if zero_usage:
            body["usage"] = {"prompt_tokens": 0, "completion_tokens": 0, "cost": 0.0}
    else:
        body.pop("prompt_eval_count")
        body.pop("eval_count")

        if zero_usage:
            body.update(prompt_eval_count=0, eval_count=0)

    adapter = adapter_factory(
        backend, httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )

    try:
        result = adapter.generate(generation)
    finally:
        adapter.close()

    expected = 0 if zero_usage else None
    assert result.input_tokens == expected
    assert result.output_tokens == expected
    assert result.cost_usd == (0.0 if zero_usage or backend == "ollama" else None)


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize(
    "finish,content,expected",
    [
        ("stop", "", "completed"),
        ("stop", None, "missing_response"),
        ("length", "{}", "truncated"),
        ("unknown", "{}", "incomplete"),
    ],
)
def test_finish_state_is_independent_of_json_validity(
    backend: str,
    finish: str,
    content: str | None,
    expected: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body(backend)

    if backend == "openrouter":
        body["choices"][0]["finish_reason"] = finish
        body["choices"][0]["message"]["content"] = content
    else:
        body["done_reason"] = finish
        body["message"]["content"] = content

    adapter = adapter_factory(
        backend, httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )

    try:
        result = adapter.generate(generation)
    finally:
        adapter.close()

    assert result.kind == expected
    assert result.raw_response == content
    assert result.finish_reason == finish


@pytest.mark.parametrize("case", ["refusal", "filter", "tool", "error", "not_done"])
def test_other_noncompletion_states(
    case: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    backend = "ollama" if case == "not_done" else "openrouter"
    body = response_body(backend)
    expected = "incomplete"

    if case == "not_done":
        body["done"] = False
    else:
        choice = body["choices"][0]

        if case == "refusal":
            choice["message"]["refusal"] = "Cannot process this document"
            expected = "refused"
        elif case == "filter":
            choice["finish_reason"] = "content_filter"
            expected = "refused"
        elif case == "tool":
            choice["message"]["tool_calls"] = [{"id": "unexpected-tool"}]
        else:
            choice["error"] = {"code": 502, "message": "Provider disconnected"}
            expected = "error"

    adapter = adapter_factory(
        backend, httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )

    try:
        result = adapter.generate(generation)
    finally:
        adapter.close()

    assert result.kind == expected
    assert result.raw_response == "  {invalid PO}\n"

    if case == "refusal":
        assert result.refusal == "Cannot process this document"

    if case == "error":
        assert result.error is not None
        assert "Provider disconnected" in result.error


@pytest.mark.parametrize("explicit_error", [True, False])
def test_overlapping_states_preserve_error_and_refusal_priority(
    explicit_error: bool,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body("openrouter")
    choice = body["choices"][0]
    choice["finish_reason"] = "length"
    choice["message"]["refusal"] = "Cannot process this document"

    if explicit_error:
        choice["error"] = {"code": 502, "message": "Provider disconnected"}

    adapter = adapter_factory(
        "openrouter", httpx.MockTransport(lambda request: httpx.Response(200, json=body))
    )

    try:
        result = adapter.generate(generation)
    finally:
        adapter.close()

    expected = ResponseKind.ERROR if explicit_error else ResponseKind.REFUSED
    assert result.kind is expected
    assert result.finish_reason == "length"
    assert result.refusal == "Cannot process this document"
    assert result.raw_response == "  {invalid PO}\n"
