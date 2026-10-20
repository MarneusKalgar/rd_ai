"""Production adapters and HTTP envelopes feeding the shared execution policy."""

import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest

from extraction_service.configuration.models import ExecutionConfig, SamplingConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget import BudgetLedger
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.pricing import VerifiedPricing
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.types import GenerationRequest, ModelAdapter


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
def test_http_retry_then_invalid_then_correction_uses_one_policy(
    backend: str,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    response_body: Callable[[str], dict[str, Any]],
    generation: GenerationRequest,
    contract: ExtractionContract,
    gold: JsonObject,
    tmp_path: Path,
    settings: ApplicationSettings,
) -> None:
    captured: list[dict[str, Any]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        captured.append(payload)

        if len(captured) == 1:
            return httpx.Response(503, text="temporary outage", headers={"Retry-After": "0"})

        body = response_body(backend)
        text = "{}" if len(captured) == 2 else json.dumps(gold)

        if backend == "openrouter":
            body["choices"][0]["message"]["content"] = text
        else:
            body["message"]["content"] = text

        return httpx.Response(200, json=body)

    adapter = adapter_factory(backend, httpx.MockTransport(handle))
    endpoint = settings.openrouter_base_url if backend == "openrouter" else settings.ollama_base_url
    target = ExecutionTarget(adapter, str(endpoint))
    policy = ExecutionConfig(
        request_timeout_seconds=7.0,
        input_timeout_seconds=20.0,
        transport_retries=1,
        api_budget_usd=1.0,
        matrix_reserve_usd=0.5,
        backoff_initial_seconds=0.001,
        backoff_max_seconds=0.01,
    )
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="No earlier test spend")
    pricing = None

    if backend == "openrouter":
        pricing = VerifiedPricing(
            dependency=target.dependency,
            input_token_ceiling=1000,
            output_token_ceiling=1000,
            input_usd_per_token=Decimal("0.000001"),
            output_usd_per_token=Decimal("0.000001"),
            request_usd=Decimal("0"),
            evidence="Fictional bounded test prices",
        )

    job = ExtractionJob(
        run_id="integration",
        input_id="input-1",
        input_sha256="1" * 64,
        experiment_sha256="2" * 64,
        prompt_id="v1",
        prompt_sha256="3" * 64,
        instructions=generation.instructions,
        source_text=generation.source_text,
        sampling=generation.sampling,
    )
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger)

    record = coordinator.execute(ScheduledExtraction(job, target, pricing))

    assert record.status == "succeeded"
    assert record.extraction == gold
    assert [attempt.outcome for attempt in record.attempts] == [
        "transport_error",
        "invalid",
        "valid",
    ]
    assert [attempt.kind for attempt in record.attempts] == [
        "extraction",
        "extraction",
        "correction",
    ]
    assert len(captured) == 3
    assert captured[0] == captured[1]
    assert captured[2]["messages"][1]["content"] == generation.source_text
    assert "validation_issues" in captured[2]["messages"][0]["content"]
    assert all(attempt.request_timeout_seconds == 7.0 for attempt in record.attempts)
    assert record.attempts[0].failure is not None
    assert record.attempts[0].failure.raw_http_body == "temporary outage"
    assert record.total_input_tokens is None
    assert record.total_cost_usd == (None if backend == "openrouter" else 0.0)
    assert len(ledger.snapshot().reservations) == (3 if backend == "openrouter" else 0)


@pytest.mark.parametrize("backend", ["openrouter", "ollama"])
@pytest.mark.parametrize("quota", [True, False])
def test_http_429_explicit_quota_evidence_differs_from_temporary_throttling(
    backend: str,
    quota: bool,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    generation: GenerationRequest,
) -> None:
    code = "insufficient_quota" if quota else "rate_limit_exceeded"

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"type": code}})

    adapter = adapter_factory(backend, httpx.MockTransport(handle))

    with pytest.raises(ModelTransportError) as raised:
        adapter.generate(generation)

    assert raised.value.evidence.kind == ("quota" if quota else "rate_limit")
    assert raised.value.evidence.retryable is not quota


@pytest.mark.parametrize("http_status", [200, 503])
def test_error_envelope_preserves_available_billed_usage(
    http_status: int,
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    generation: GenerationRequest,
) -> None:
    body = {
        "error": {"code": 503, "message": "Failed after generation started"},
        "usage": {"prompt_tokens": 17, "completion_tokens": 9, "cost": 0.002, "total_tokens": 26},
    }

    def handle(request: httpx.Request) -> httpx.Response:
        return httpx.Response(http_status, json=body)

    adapter = adapter_factory("openrouter", httpx.MockTransport(handle))

    with pytest.raises(ModelTransportError) as raised:
        adapter.generate(generation)

    assert raised.value.evidence.kind == "server_error"
    assert raised.value.evidence.input_tokens == 17
    assert raised.value.evidence.output_tokens == 9
    assert raised.value.evidence.cost_usd == 0.002
    assert json.loads(raised.value.evidence.raw_http_body or "") == body


def test_known_unsupported_output_limit_stops_without_a_physical_request(
    adapter_factory: Callable[[str, httpx.BaseTransport], ModelAdapter],
    generation: GenerationRequest,
    contract: ExtractionContract,
    tmp_path: Path,
    settings: ApplicationSettings,
) -> None:
    def unexpected(request: httpx.Request) -> httpx.Response:
        pytest.fail("A known unsupported output limit must fail before HTTP")

    adapter = adapter_factory("openrouter", httpx.MockTransport(unexpected))
    target = ExecutionTarget(adapter, str(settings.openrouter_base_url))
    policy = ExecutionConfig(
        request_timeout_seconds=5.0,
        input_timeout_seconds=20.0,
        transport_retries=1,
        api_budget_usd=1.0,
    )
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="No earlier test spending")
    pricing = VerifiedPricing(
        dependency=target.dependency,
        input_token_ceiling=1000,
        output_token_ceiling=131072,
        input_usd_per_token=Decimal("0.000001"),
        output_usd_per_token=Decimal("0.000001"),
        request_usd=Decimal("0"),
        evidence="Deliberately broader pricing coverage than the verified adapter output limit",
    )
    job = ExtractionJob(
        run_id="unsupported-test",
        input_id="input-1",
        input_sha256="1" * 64,
        experiment_sha256="2" * 64,
        prompt_id="v1",
        prompt_sha256="3" * 64,
        instructions=generation.instructions,
        source_text=generation.source_text,
        sampling=SamplingConfig(
            id="too-large", temperature=0.0, top_p=1.0, max_output_tokens=100000
        ),
    )
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger)
    task = ScheduledExtraction(job, target, pricing)

    batch = coordinator.execute_many([task, task])

    assert [record.status for record in batch.records] == ["not_attempted", "not_attempted"]
    assert all(record.attempts == [] for record in batch.records)
    assert (
        batch.summary.dependency_stops[0].reason == "dependency_setup_failure:unsupported_request"
    )
    assert len(ledger.snapshot().reservations) == 1
    assert ledger.snapshot().accounted_usd == Decimal("0")
