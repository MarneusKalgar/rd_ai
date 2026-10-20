"""Construct validated run records and batch summaries from execution evidence."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget import BudgetStopReason
from extraction_service.execution.policy import DependencyState, DependencyStop
from extraction_service.execution.types import DependencyIdentity, InputExecution
from extraction_service.extraction import ExtractionContract
from extraction_service.record_types import (
    CONTRACT_CONTEXT_KEY,
    AttemptOutcome,
    ExecutionReason,
    RunStatus,
)
from extraction_service.records import RunRecord
from extraction_service.runtime_types import NonNegativeInt, StrictModel


class BatchSummary(StrictModel):
    """Distinguish failed work from interrupted comparisons and untouched inputs."""

    execution: ExecutionConfig
    succeeded: NonNegativeInt
    failed: NonNegativeInt
    not_attempted: NonNegativeInt
    comparison_complete: bool
    dependency_stops: list[DependencyStop]
    budget_stops: list[BudgetStopReason]


@dataclass(frozen=True)
class BatchResult:
    records: tuple[RunRecord, ...]
    summary: BatchSummary


def build_batch_result(
    records: tuple[RunRecord, ...],
    execution: ExecutionConfig,
    *,
    dependencies: Mapping[DependencyIdentity, DependencyState],
    budget_stops: frozenset[BudgetStopReason],
) -> BatchResult:
    """Summarize selected work without dropping failed or untouched combinations."""

    succeeded = sum(record.status == RunStatus.SUCCEEDED for record in records)
    failed = sum(record.status == RunStatus.FAILED for record in records)
    not_attempted = sum(record.status == RunStatus.NOT_ATTEMPTED for record in records)
    stops = []

    for dependency, state in dependencies.items():
        if state.stop_reason is not None:
            stops.append(
                DependencyStop(
                    dependency=dependency,
                    reason=state.stop_reason,
                    consecutive_failures=state.consecutive_failures,
                )
            )

    summary = BatchSummary(
        execution=execution,
        succeeded=succeeded,
        failed=failed,
        not_attempted=not_attempted,
        comparison_complete=not_attempted == 0 and not stops and not budget_stops,
        dependency_stops=stops,
        budget_stops=sorted(budget_stops),
    )

    return BatchResult(records=records, summary=summary)


def build_run_record(
    progress: InputExecution, contract: ExtractionContract, *, elapsed_ms: float
) -> RunRecord:
    """Build an operational envelope under the same authoritative PO contract."""

    scheduled = progress.scheduled
    job = scheduled.job
    identity = scheduled.target.adapter.identity
    extraction = None
    status = RunStatus.NOT_ATTEMPTED if not progress.attempts else RunStatus.FAILED

    if progress.attempts and progress.attempts[-1].outcome == AttemptOutcome.VALID:
        raw = progress.attempts[-1].raw_response
        assert raw is not None
        extraction = contract.validate_json(raw).value
        status = RunStatus.SUCCEEDED

    request_ms = sum(attempt.duration_ms for attempt in progress.attempts)
    values = {
        "run_id": job.run_id,
        "input_id": job.input_id,
        "input_sha256": job.input_sha256,
        "experiment_sha256": job.experiment_sha256,
        "model_id": identity.model_id,
        "model_name": identity.model_name,
        "runtime": identity.runtime,
        "prompt_id": job.prompt_id,
        "prompt_sha256": job.prompt_sha256,
        "sampling_id": job.sampling.id,
        "sampling": job.sampling,
        "schema_sha256": contract.identity.sha256,
        "status": status,
        "attempts": progress.attempts,
        "extraction": extraction,
        "reason": (
            None
            if status == RunStatus.SUCCEEDED
            else progress.reason or ExecutionReason.EXECUTION_FAILED.value
        ),
        "duration_ms": max(elapsed_ms, request_ms),
        "total_input_tokens": sum_known(attempt.input_tokens for attempt in progress.attempts),
        "total_output_tokens": sum_known(attempt.output_tokens for attempt in progress.attempts),
        "total_cost_usd": sum_known(attempt.cost_usd for attempt in progress.attempts),
        "stage": job.stage,
        "dependency": scheduled.target.dependency,
    }

    return RunRecord.model_validate(values, context={CONTRACT_CONTEXT_KEY: contract})


def sum_known(values: Iterable[int | float | None]) -> int | float | None:
    """Sum explicit measurements, preserving unknown accounting and known zeroes."""

    total: int | float = 0

    for value in values:
        if value is None:
            return None

        total += value

    return total
