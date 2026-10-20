import json

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import FailureKind
from extraction_service.inference.types import ModelIdentity, ResponseKind
from extraction_service.records import RunRecord

from .helpers import FakeClock, ScriptedAdapter, failure, response


def test_success_preserves_response_identity_source_and_schema(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    raw = " \n" + json.dumps(gold) + "\n"
    reply = response(local_identity, raw)
    adapter = ScriptedAdapter(local_identity, clock, [reply])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)
    task = ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))

    result = coordinator.execute_many([task])
    record = result.records[0]
    restored = RunRecord.model_validate_json(
        record.model_dump_json(), context={"contract": contract}
    )

    assert record == restored
    assert record.status == "succeeded"
    assert record.extraction == gold
    assert record.attempts[0].response == reply
    assert record.attempts[0].raw_response == raw
    assert record.total_input_tokens == 12
    assert record.total_output_tokens == 4
    assert record.total_cost_usd == 0.0
    assert record.duration_ms == pytest.approx(10.0)
    assert record.dependency is not None
    assert str(record.dependency.endpoint) == "http://ollama:11434/"
    assert adapter.requests[0].source_text == job.source_text
    assert adapter.requests[0].output_schema == contract.schema_for_provider()
    assert adapter.requests[0].timeout_seconds == 5.0
    assert result.summary.succeeded == 1
    assert result.summary.comparison_complete


@pytest.mark.parametrize("first_text", ["not json", "{}"])
def test_one_correction_uses_original_source_and_exact_invalid_evidence(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    first_text: str,
) -> None:
    adapter = ScriptedAdapter(
        local_identity,
        clock,
        [response(local_identity, first_text), response(local_identity, json.dumps(gold))],
    )
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.status == "succeeded"
    assert [attempt.kind for attempt in record.attempts] == ["extraction", "correction"]
    assert [attempt.outcome for attempt in record.attempts] == ["invalid", "valid"]
    assert record.attempts[0].raw_response == first_text
    assert record.attempts[0].issues == list(contract.validate_json(first_text).issues)
    assert adapter.requests[1].source_text == job.source_text
    assert adapter.requests[1].instructions.startswith(job.instructions)
    assert json.dumps(first_text) in adapter.requests[1].instructions
    assert "validation_issues" in adapter.requests[1].instructions
    assert adapter.requests[0].output_schema == adapter.requests[1].output_schema
    assert record.total_input_tokens == 24
    assert record.total_output_tokens == 8


@pytest.mark.parametrize("retries", [0, 1, 3, 5])
def test_each_generation_has_its_own_retry_bound_and_only_one_correction(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    retries: int,
) -> None:
    values = policy.model_dump()
    values.update(transport_retries=retries, input_timeout_seconds=120.0)
    configured = ExecutionConfig.model_validate(values)
    one_generation = [failure() for _ in range(retries)] + [response(local_identity, "{}")]
    adapter = ScriptedAdapter(local_identity, clock, one_generation * 2)
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.status == "failed"
    assert record.reason == "invalid_output"
    assert len(adapter.requests) == 2 * (retries + 1)
    assert [attempt.number for attempt in record.attempts] == list(range(1, 2 * retries + 3))
    assert [attempt.kind for attempt in record.attempts] == (
        ["extraction"] * (retries + 1) + ["correction"] * (retries + 1)
    )
    assert record.total_input_tokens == (24 if retries == 0 else None)
    assert record.total_output_tokens == (8 if retries == 0 else None)
    assert record.total_cost_usd == 0.0


@pytest.mark.parametrize(
    "kind",
    [
        ResponseKind.REFUSED,
        ResponseKind.TRUNCATED,
        ResponseKind.MISSING_RESPONSE,
        ResponseKind.INCOMPLETE,
        ResponseKind.ERROR,
    ],
)
def test_noncompleted_response_never_becomes_success_or_triggers_correction(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    kind: ResponseKind,
) -> None:
    reply = response(local_identity, json.dumps(gold)).model_copy(update={"kind": kind})
    adapter = ScriptedAdapter(local_identity, clock, [reply])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.status == "failed"
    assert record.extraction is None
    assert len(adapter.requests) == 1
    assert record.attempts[0].response == reply
    assert record.attempts[0].outcome not in ("valid", "invalid")
    assert clock.sleeps == []


def test_transport_failure_does_not_start_a_correction(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    adapter = ScriptedAdapter(local_identity, clock, [failure(), failure()])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.status == "failed"
    assert [attempt.kind for attempt in record.attempts] == ["extraction", "extraction"]
    assert record.attempts[0].failure is not None
    assert record.attempts[0].failure.raw_http_body == "exact failure envelope"
    assert record.attempts[0].retry_delay_seconds == 1.0
    assert record.duration_ms == pytest.approx(1020.0)


def test_unexpected_defect_propagates_without_retries(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    defect = RuntimeError("programming defect")
    adapter = ScriptedAdapter(local_identity, clock, [defect])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    with pytest.raises(RuntimeError) as raised:
        coordinator.execute(
            ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
        )

    assert raised.value is defect
    assert len(adapter.requests) == 1
    assert clock.sleeps == []


@pytest.mark.parametrize(
    "kind",
    [
        FailureKind.AUTHENTICATION,
        FailureKind.UNSUPPORTED_REQUEST,
        FailureKind.QUOTA,
        FailureKind.PROTOCOL_ERROR,
    ],
)
def test_permanent_failure_has_no_transport_retry(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    kind: FailureKind,
) -> None:
    adapter = ScriptedAdapter(local_identity, clock, [failure(kind, retryable=False)])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.reason == f"transport_failure:{kind.value}"
    assert len(record.attempts) == 1
    assert clock.sleeps == []
