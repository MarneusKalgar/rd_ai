"""Typed failures, credential-safe evidence and absence of hidden retry requests."""

import json
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.types import GenerationRequest, ModelAdapter, ModelResponse


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize(
    "status,kind,retryable",
    [
        (401, "authentication", False),
        (403, "authentication", False),
        (402, "quota", False),
        (400, "unsupported_request", False),
        (404, "unsupported_request", False),
        (422, "unsupported_request", False),
        (429, "rate_limit", True),
        (500, "server_error", True),
        (502, "server_error", True),
        (503, "server_error", True),
        (504, "timeout", True),
        (302, "http_error", False),
    ],
)
def test_http_failures_are_preserved_without_retries_or_redirects(
    backend: str,
    status: int,
    kind: str,
    retryable: bool,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
) -> None:
    requests: list[httpx.Request] = []
    raw_body = '{"error":{"message":"upstream failure"}}\n'

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        return httpx.Response(
            status,
            text=raw_body,
            headers={"Retry-After": "7", "Location": "https://other-provider.invalid/"},
        )

    adapter = adapter_factory(backend, httpx.MockTransport(handle))

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    evidence = failure.value.evidence
    assert isinstance(evidence.kind, FailureKind)
    assert evidence.kind == kind
    assert evidence.retryable is retryable
    assert evidence.status_code == status
    assert evidence.raw_http_body == raw_body
    assert evidence.retry_after == "7"
    assert evidence.duration_ms >= 0
    assert len(requests) == 1


@pytest.mark.parametrize("location", ["exception", "retry_after"])
def test_credential_redaction_flag_covers_failure_messages_and_headers(
    location: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
) -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        if location == "exception":
            raise httpx.ConnectError("echo adapter-test-credential", request=request)

        return httpx.Response(
            401, text="denied", headers={"Retry-After": "adapter-test-credential"}
        )

    adapter = adapter_factory("openrouter", httpx.MockTransport(handle))

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    evidence = failure.value.evidence
    assert evidence.credentials_redacted is True
    assert "adapter-test-credential" not in evidence.model_dump_json()
    assert "adapter-test-credential" not in str(failure.value)

    if location == "exception":
        assert evidence.kind == "connection"
        assert evidence.message == "echo [REDACTED]"
    else:
        assert evidence.kind == "authentication"
        assert evidence.retry_after == "[REDACTED]"


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("timeout", [True, False])
def test_transport_exceptions_are_single_attempts(
    backend: str,
    timeout: bool,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
) -> None:
    requests: list[httpx.Request] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)

        if timeout:
            raise httpx.ReadTimeout("upstream timeout", request=request)

        raise httpx.ConnectError("connection failed", request=request)

    adapter = adapter_factory(backend, httpx.MockTransport(handle))

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    evidence = failure.value.evidence
    assert evidence.kind == ("timeout" if timeout else "connection")
    assert evidence.retryable is True
    assert evidence.raw_http_body is None
    assert evidence.status_code is None
    assert failure.value.__cause__ is None
    assert len(requests) == 1


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("raw_body", ["not json", "[]", '{"model":1,"model":2}', '{"x":NaN}'])
def test_malformed_envelopes_keep_exact_body(
    backend: str,
    raw_body: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
) -> None:
    adapter = adapter_factory(
        backend, httpx.MockTransport(lambda request: httpx.Response(200, text=raw_body))
    )

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    assert failure.value.evidence.kind == "protocol_error"
    assert failure.value.evidence.retryable is False
    assert failure.value.evidence.raw_http_body == raw_body


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("defect", ["role", "token_type", "negative_tokens", "identity"])
def test_invalid_wire_fields_fail_from_valid_envelope(
    backend: str,
    defect: str,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body(backend)

    if defect == "role":
        message = body["choices"][0]["message"] if backend == "openrouter" else body["message"]
        message["role"] = "user"
    elif defect == "identity":
        if backend == "openrouter":
            body["choices"].append(body["choices"][0])
        else:
            body["model"] = "different-model"
    else:
        tokens = "14" if defect == "token_type" else -1

        if backend == "openrouter":
            body["usage"]["completion_tokens"] = tokens
        else:
            body["eval_count"] = tokens

    raw_body = json.dumps(body)
    adapter = adapter_factory(
        backend, httpx.MockTransport(lambda request: httpx.Response(200, text=raw_body))
    )

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    assert failure.value.evidence.kind == "protocol_error"
    assert failure.value.evidence.raw_http_body == raw_body


def test_http_200_openrouter_error_is_not_a_completion(
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
) -> None:
    raw_body = '{"error":{"code":402,"message":"credits exhausted"}}'
    adapter = adapter_factory(
        "openrouter", httpx.MockTransport(lambda request: httpx.Response(200, text=raw_body))
    )

    try:
        with pytest.raises(ModelTransportError) as failure:
            adapter.generate(generation)
    finally:
        adapter.close()

    assert failure.value.evidence.kind == "quota"
    assert failure.value.evidence.retryable is False
    assert failure.value.evidence.status_code == 402
    assert failure.value.evidence.raw_http_body == raw_body


@pytest.mark.parametrize("status", [200, 401])
def test_reflected_credentials_are_redacted_from_evidence(
    status: int,
    generation: GenerationRequest,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    body = response_body("openrouter")
    body["choices"][0]["message"]["content"] = "echo adapter-test-credential"
    adapter = adapter_factory(
        "openrouter", httpx.MockTransport(lambda request: httpx.Response(status, json=body))
    )
    evidence: ModelResponse | FailureEvidence

    try:
        if status == 200:
            evidence = adapter.generate(generation)
            assert evidence.raw_response == "echo [REDACTED]"
        else:
            with pytest.raises(ModelTransportError) as failure:
                adapter.generate(generation)

            evidence = failure.value.evidence
            assert "adapter-test-credential" not in str(failure.value)

        assert evidence.credentials_redacted is True
        assert "adapter-test-credential" not in evidence.model_dump_json()
        assert "adapter-test-credential" not in repr(evidence)
    finally:
        adapter.close()
