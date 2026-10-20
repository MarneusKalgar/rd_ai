import json
from datetime import timedelta
from email.utils import format_datetime

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import FailureKind
from extraction_service.inference.types import ModelIdentity

from .helpers import FakeClock, ScriptedAdapter, failure, response


@pytest.mark.parametrize("retry_after", ["3", "http-date", "nonsense", "-2", "2.5"])
def test_retry_after_and_fallback_backoff(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    retry_after: str,
) -> None:
    header = retry_after

    if retry_after == "http-date":
        header = format_datetime(clock.now() + timedelta(seconds=3), usegmt=True)

    adapter = ScriptedAdapter(
        local_identity,
        clock,
        [
            failure(FailureKind.RATE_LIMIT, retry_after=header),
            response(local_identity, json.dumps(gold)),
        ],
    )
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    expected_delay = 2.99 if retry_after == "http-date" else 3.0 if retry_after == "3" else 1.0

    assert record.status == "succeeded"
    assert clock.sleeps == [pytest.approx(expected_delay)]
    assert record.attempts[0].retry_delay_seconds == pytest.approx(expected_delay)
    assert record.duration_ms == pytest.approx(expected_delay * 1000 + 20)


def test_excessive_retry_after_never_causes_an_early_retry(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    adapter = ScriptedAdapter(local_identity, clock, [failure(retry_after="600")])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.reason == "retry_after_exceeds_backoff_limit"
    assert len(adapter.requests) == 1
    assert clock.sleeps == []


def test_deadline_covers_requests_and_backoff_and_counts_one_availability_failure(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    configured = policy.model_copy(
        update={
            "request_timeout_seconds": 1.0,
            "input_timeout_seconds": 2.0,
            "dependency_failure_limit": 1,
        }
    )
    adapter = ScriptedAdapter(
        local_identity, clock, [failure(retry_after="3")], elapsed_seconds=0.5
    )
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)
    task = ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))

    batch = coordinator.execute_many([task, task])

    assert batch.records[0].reason == "input_deadline_exceeded"
    assert batch.records[0].duration_ms == 2000.0
    assert batch.records[0].attempts[0].retry_delay_seconds == 1.5
    assert batch.records[1].status == "not_attempted"
    assert batch.summary.dependency_stops[0].consecutive_failures == 1
    assert len(adapter.requests) == 1


def test_correction_timeout_is_clamped_to_remaining_input_deadline(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    configured = policy.model_copy(update={"input_timeout_seconds": 6.0})
    adapter = ScriptedAdapter(
        local_identity,
        clock,
        [
            response(local_identity, "{}"),
            response(local_identity, json.dumps(gold)),
        ],
        elapsed_seconds=2.0,
    )
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )

    assert record.status == "succeeded"
    assert [request.timeout_seconds for request in adapter.requests] == [5.0, 4.0]
    assert [attempt.request_timeout_seconds for attempt in record.attempts] == [5.0, 4.0]


def test_late_valid_response_is_a_deadline_failure_and_next_input_can_continue(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    late = ScriptedAdapter(
        local_identity, clock, [response(local_identity, json.dumps(gold))], elapsed_seconds=21.0
    )
    normal = ScriptedAdapter(local_identity, clock, [response(local_identity, json.dumps(gold))])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    batch = coordinator.execute_many(
        [
            ScheduledExtraction(job, ExecutionTarget(late, "http://ollama:11434")),
            ScheduledExtraction(job, ExecutionTarget(normal, "http://ollama:11434")),
        ]
    )

    assert batch.records[0].status == "failed"
    assert batch.records[0].reason == "input_deadline_exceeded"
    assert batch.records[0].attempts[0].outcome == "deadline_exceeded"
    assert batch.records[0].extraction is None
    assert batch.records[1].status == "succeeded"
    assert batch.summary.dependency_stops == []
