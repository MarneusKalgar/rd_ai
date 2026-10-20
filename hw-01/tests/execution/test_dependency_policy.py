import json

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import FailureKind
from extraction_service.inference.types import ModelIdentity, ModelResponse, ResponseKind

from .helpers import FakeClock, ScriptedAdapter, failure, response


@pytest.mark.parametrize("threshold", [1, 3, 4])
def test_stop_counts_failed_inputs_not_physical_retries(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    threshold: int,
) -> None:
    configured = policy.model_copy(update={"dependency_failure_limit": threshold})
    adapter = ScriptedAdapter(local_identity, clock, [failure() for _ in range(2 * threshold)])
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)
    target = ExecutionTarget(adapter, "http://ollama:11434")
    tasks = [
        ScheduledExtraction(job.model_copy(update={"input_id": f"input-{i}"}), target)
        for i in range(threshold + 2)
    ]

    batch = coordinator.execute_many(tasks)

    assert [record.status for record in batch.records] == (
        ["failed"] * threshold + ["not_attempted"] * 2
    )
    assert len(adapter.requests) == 2 * threshold
    assert batch.summary.failed == threshold
    assert batch.summary.not_attempted == 2
    assert not batch.summary.comparison_complete
    assert batch.summary.execution.dependency_failure_limit == threshold
    assert batch.summary.dependency_stops[0].consecutive_failures == threshold
    assert batch.records[-1].attempts == []
    assert batch.records[-1].reason == "dependency_unavailable:timeout"


@pytest.mark.parametrize(
    "kind",
    [
        ResponseKind.COMPLETED,
        ResponseKind.REFUSED,
        ResponseKind.TRUNCATED,
        ResponseKind.MISSING_RESPONSE,
    ],
)
def test_returned_model_response_resets_availability_counter(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    kind: ResponseKind,
) -> None:
    configured = policy.model_copy(update={"transport_retries": 0, "dependency_failure_limit": 2})
    reply = response(local_identity, "{}").model_copy(update={"kind": kind})
    outcomes: list[ModelResponse | Exception] = [failure(), reply]

    if kind == ResponseKind.COMPLETED:
        outcomes.append(reply)  # The correction remains invalid; both responses reset state.

    outcomes.extend([failure(), failure()])
    adapter = ScriptedAdapter(local_identity, clock, outcomes)
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)
    target = ExecutionTarget(adapter, "http://ollama:11434")

    batch = coordinator.execute_many([ScheduledExtraction(job, target) for _ in range(5)])

    assert [record.status for record in batch.records] == [
        "failed",
        "failed",
        "failed",
        "failed",
        "not_attempted",
    ]
    assert batch.records[1].attempts[-1].outcome != "transport_error"
    assert batch.summary.dependency_stops[0].consecutive_failures == 2
    assert len(adapter.requests) == (5 if kind == ResponseKind.COMPLETED else 4)


def test_stop_survives_variant_and_model_alias_changes_but_isolates_endpoint(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    configured = policy.model_copy(update={"transport_retries": 0, "dependency_failure_limit": 1})
    first = ScriptedAdapter(local_identity, clock, [failure()])
    alias = local_identity.model_copy(update={"model_id": "local-alias"})
    same = ScriptedAdapter(alias, clock, [])
    independent = ScriptedAdapter(
        local_identity, clock, [response(local_identity, json.dumps(gold))]
    )
    coordinator = ExtractionCoordinator(contract, configured, clock=clock)
    second_job = job.model_copy(update={"prompt_id": "v2"})

    batch = coordinator.execute_many(
        [
            ScheduledExtraction(job, ExecutionTarget(first, "http://ollama:11434")),
            ScheduledExtraction(second_job, ExecutionTarget(same, "http://ollama:11434/")),
            ScheduledExtraction(second_job, ExecutionTarget(independent, "http://other:11434")),
        ]
    )

    assert [record.status for record in batch.records] == ["failed", "not_attempted", "succeeded"]
    assert same.requests == []
    assert len(independent.requests) == 1
    assert batch.summary.succeeded == 1


@pytest.mark.parametrize(
    "kind", [FailureKind.AUTHENTICATION, FailureKind.QUOTA, FailureKind.UNSUPPORTED_REQUEST]
)
def test_setup_failure_stops_dependency_immediately(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    kind: FailureKind,
) -> None:
    adapter = ScriptedAdapter(local_identity, clock, [failure(kind, retryable=False)])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)
    task = ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))

    batch = coordinator.execute_many([task, task])

    assert [record.status for record in batch.records] == ["failed", "not_attempted"]
    assert batch.summary.dependency_stops[0].reason == f"dependency_setup_failure:{kind.value}"
    assert batch.summary.dependency_stops[0].consecutive_failures == 0
    assert len(adapter.requests) == 1


def test_new_invocation_starts_fresh_dependency_state(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    configured = policy.model_copy(update={"transport_retries": 0, "dependency_failure_limit": 1})
    adapter = ScriptedAdapter(
        local_identity, clock, [failure(), response(local_identity, json.dumps(gold))]
    )
    task = ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    first = ExtractionCoordinator(contract, configured, clock=clock)

    failed = first.execute(task)
    skipped = first.execute(task)
    second = ExtractionCoordinator(contract, configured, clock=clock)
    recovered = second.execute(task)

    assert failed.status == "failed"
    assert skipped.status == "not_attempted"
    assert recovered.status == "succeeded"
    assert len(adapter.requests) == 2
