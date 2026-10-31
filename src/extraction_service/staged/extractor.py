"""Reuse request admission, bounded schema correction and shared dependency stops per stage."""

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.admission import RequestAdmission
from extraction_service.execution.coordinator import ExtractionCoordinator
from extraction_service.execution.policy import Clock, DependencyState, SystemClock
from extraction_service.execution.types import (
    DependencyIdentity,
    ExecutionTarget,
    ExtractionJob,
    InputExecution,
    ScheduledExtraction,
)
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.record_types import ModelRuntime
from extraction_service.records import RunRecord
from extraction_service.staged.contracts import (
    SplitStage,
    assemble,
    stage_contract,
    stage_instructions,
)


@dataclass(frozen=True)
class SplitResult:
    """Both measured stage records and their assembly, never a selected best-field output."""

    records: dict[SplitStage, RunRecord]
    extraction: JsonObject | None
    duration_ms: float


class SplitExtractor:
    """Two sequential, independent calls over identical source; no previous-stage feedback."""

    def __init__(
        self,
        contract: ExtractionContract,
        target: ExecutionTarget,
        admission: RequestAdmission,
        execution: ExecutionConfig,
        *,
        clock: Clock | None = None,
        checkpoint: Callable[[SplitStage, InputExecution], None] | None = None,
    ) -> None:
        if target.adapter.identity.runtime != ModelRuntime.OLLAMA_NATIVE:
            raise ValueError(
                "Split experiment requires native Ollama; paid/Docker inference disabled"
            )
        self.contract = contract
        self.target = target
        self.clock = SystemClock() if clock is None else clock
        self.coordinators = {}
        shared: dict[DependencyIdentity, DependencyState] = {}
        for stage in SplitStage:

            def persist(progress: InputExecution, selected: SplitStage = stage) -> None:
                if checkpoint is not None:
                    checkpoint(selected, progress)

            self.coordinators[stage] = ExtractionCoordinator(
                stage_contract(contract, stage),
                execution,
                clock=self.clock,
                admission=admission,
                checkpoint=persist,
                dependency_states=shared,
            )

    def extract(self, job: ExtractionJob) -> SplitResult:
        """Run header then lines independently, retaining failures in both stage records."""

        started = self.clock.monotonic()
        records = {}
        for stage in SplitStage:
            instructions = stage_instructions(job.instructions, stage)
            staged_job = job.model_copy(
                update={
                    "prompt_id": f"{job.prompt_id}-{stage.value}",
                    "instructions": instructions,
                    "prompt_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
                }
            )
            scheduled = ScheduledExtraction(job=staged_job, target=self.target)
            records[stage] = self.coordinators[stage].execute(scheduled)
        extraction = assemble(
            self.contract,
            records[SplitStage.HEADERS].extraction,
            records[SplitStage.LINES].extraction,
        )
        return SplitResult(records, extraction, (self.clock.monotonic() - started) * 1000)
