"""Admission uses the actual correction and consumes the input deadline."""

from dataclasses import dataclass, field

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.admission import (
    AdmissionEvidence,
    AdmissionReason,
    AdmissionRejected,
)
from extraction_service.execution.coordinator import ExtractionCoordinator
from extraction_service.execution.types import (
    ExecutionTarget,
    ExtractionJob,
    InputExecution,
    ScheduledExtraction,
)
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.types import GenerationRequest, ModelIdentity

from .helpers import FakeClock, ScriptedAdapter, failure, response


@dataclass
class TimedAdmission:
    clock: FakeClock
    elapsed: float
    reject_number: int = 0
    requests: list[GenerationRequest] = field(default_factory=list)

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        self.requests.append(request)
        self.clock.seconds += self.elapsed

        if len(self.requests) == self.reject_number:
            raise AdmissionRejected(AdmissionReason.CONTEXT_CAPACITY_EXCEEDED)

        return AdmissionEvidence(
            method="controlled-test-counter",
            request_sha256="a" * 64,
            counter_identity="fictional-test-counter",
            prompt_token_bound=20,
            output_allowance=request.sampling.max_output_tokens,
            context_length=1000,
        )


@pytest.mark.parametrize("elapsed,physical_count,timeout", [(19.0, 1, 1.0), (20.0, 0, None)])
def test_admission_time_reduces_generation_deadline(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
    elapsed: float,
    physical_count: int,
    timeout: float | None,
) -> None:
    admission = TimedAdmission(clock, elapsed)
    adapter = ScriptedAdapter(local_identity, clock, [response(local_identity, "{}")])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock, admission=admission)

    record = coordinator.execute(ScheduledExtraction(job, ExecutionTarget(adapter, "http://local")))

    assert len(adapter.requests) == physical_count
    assert record.reason == "input_deadline_exceeded"

    if timeout is not None:
        assert adapter.requests[0].timeout_seconds == timeout


def test_rejected_correction_preserves_initial_attempt(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    admission = TimedAdmission(clock, 0.0, reject_number=2)
    adapter = ScriptedAdapter(local_identity, clock, [response(local_identity, "{}")])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock, admission=admission)

    record = coordinator.execute(ScheduledExtraction(job, ExecutionTarget(adapter, "http://local")))

    assert len(adapter.requests) == 1
    assert record.status.value == "failed"
    assert record.reason == "context_capacity_exceeded"
    assert record.attempts[0].raw_response == "{}"
    assert "{}" in admission.requests[1].instructions
    assert admission.requests[1].source_text == job.source_text
    assert admission.requests[1].output_schema == contract.schema_for_provider()


def test_checkpoint_failure_stops_before_retry(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> None:
    adapter = ScriptedAdapter(local_identity, clock, [failure(), failure()])
    seen = []

    def checkpoint(progress: InputExecution) -> None:
        if progress.attempts:
            seen.append(progress.attempts[-1].model_dump())
            raise OSError("controlled disk failure")

    coordinator = ExtractionCoordinator(contract, policy, clock=clock, checkpoint=checkpoint)

    with pytest.raises(OSError, match="controlled disk failure"):
        coordinator.execute(ScheduledExtraction(job, ExecutionTarget(adapter, "http://local")))

    assert len(adapter.requests) == len(seen) == 1
    assert seen[0]["number"] == 1
    assert clock.sleeps == []
