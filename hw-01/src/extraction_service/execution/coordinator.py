"""Coordinate extraction, correction, retries and invocation-local dependency policy."""

from collections.abc import Callable, Iterable

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.admission import AdmissionRejected, RequestAdmission
from extraction_service.execution.budget.guard import SpendingGuard
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop, Reservation
from extraction_service.execution.evidence import (
    AttemptContext,
    correction_instructions,
    failure_attempt,
    response_attempt,
)
from extraction_service.execution.policy import (
    AVAILABILITY_FAILURES,
    Clock,
    DependencyState,
    SystemClock,
    retry_delay,
)
from extraction_service.execution.reasons import failure_reason
from extraction_service.execution.results import BatchResult as BatchResult
from extraction_service.execution.results import BatchSummary as BatchSummary
from extraction_service.execution.results import (
    build_batch_result,
    build_run_record,
)
from extraction_service.execution.types import DependencyIdentity, InputExecution
from extraction_service.execution.types import ScheduledExtraction as ScheduledExtraction
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.errors import (
    FailureKind,
    ModelConfigurationError,
    ModelTransportError,
)
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import (
    AttemptKind,
    AttemptOutcome,
    ExecutionReason,
    ModelRuntime,
)
from extraction_service.records import AttemptResult, RunRecord


class ExtractionCoordinator:
    """One sequential invocation borrowing adapters and a persistent spending guard.

    Reuse this instance across prompt/sampling variants to retain dependency
    stops. A later invocation uses a new coordinator and the same budget ledger.
    Application setup owns client cleanup and persistence. Public result and
    scheduling imports remain available here for existing callers.
    """

    def __init__(
        self,
        contract: ExtractionContract,
        execution: ExecutionConfig,
        *,
        ledger: BudgetLedger | None = None,
        clock: Clock | None = None,
        admission: RequestAdmission | None = None,
        checkpoint: Callable[[InputExecution], None] | None = None,
    ) -> None:
        self._contract = contract
        self._execution = execution
        self._spending = SpendingGuard(execution, ledger)
        self._clock = SystemClock() if clock is None else clock
        self._dependencies: dict[DependencyIdentity, DependencyState] = {}
        self._admission = admission
        self._checkpoint = checkpoint

    def execute_many(self, scheduled: Iterable[ScheduledExtraction]) -> BatchResult:
        """Process selected work, retaining empty histories for untouched combinations."""

        records = []

        for item in scheduled:
            records.append(self.execute(item))

        return build_batch_result(
            tuple(records),
            self._execution,
            dependencies=self._dependencies,
            budget_stops=self._spending.stops,
        )

    def execute(self, scheduled: ScheduledExtraction) -> RunRecord:
        """Execute at most two generations, each with at most R + 1 physical requests."""

        started = self._clock.monotonic()
        progress = InputExecution(
            scheduled=scheduled,
            started=started,
            deadline=started + self._execution.input_timeout_seconds,
        )
        dependency = scheduled.target.dependency
        self._save_progress(progress)
        state = self._dependencies.setdefault(dependency, DependencyState())
        paid_stop = self._spending.paid_stop

        if state.stop_reason is not None:
            progress.reason = state.stop_reason
        elif scheduled.target.adapter.identity.runtime == ModelRuntime.OPENROUTER and paid_stop:
            progress.reason = paid_stop.value
        else:
            self._extract(progress, state)

        elapsed_ms = (self._clock.monotonic() - progress.started) * 1000

        return build_run_record(progress, self._contract, elapsed_ms=elapsed_ms)

    def _extract(self, progress: InputExecution, state: DependencyState) -> None:
        instructions = progress.scheduled.job.instructions

        for kind in (AttemptKind.EXTRACTION, AttemptKind.CORRECTION):
            try:
                returned = self._generation(progress, state, instructions, kind)
            except ModelConfigurationError:
                state.stop_reason = failure_reason(
                    ExecutionReason.DEPENDENCY_SETUP_FAILURE, FailureKind.UNSUPPORTED_REQUEST
                )
                progress.reason = state.stop_reason

                return

            if not returned:
                if progress.last_failure is not None and not progress.budget_stopped:
                    state.failed_input(
                        progress.last_failure, self._execution.dependency_failure_limit
                    )

                return

            final = progress.attempts[-1]

            if final.outcome == AttemptOutcome.VALID:
                return

            progress.reason = final.error or ExecutionReason.INVALID_OUTPUT.value

            if final.outcome != AttemptOutcome.INVALID or kind == AttemptKind.CORRECTION:
                return

            instructions = correction_instructions(progress.scheduled.job.instructions, final)

    def _generation(
        self,
        progress: InputExecution,
        state: DependencyState,
        instructions: str,
        kind: AttemptKind,
    ) -> bool:
        for retry_number in range(self._execution.transport_retries + 1):
            attempt = self._next_attempt(progress, instructions, kind)

            if attempt is None:
                return False

            if attempt.failure is None:
                state.completed_response()
                progress.last_failure = None

                return True

            progress.last_failure = attempt.failure
            progress.reason = failure_reason(
                ExecutionReason.TRANSPORT_FAILURE, attempt.failure.kind
            )

            if self._clock.monotonic() >= progress.deadline:
                progress.reason = ExecutionReason.INPUT_DEADLINE_EXCEEDED.value

                return False

            if retry_number == self._execution.transport_retries:
                return False

            if not self._backoff(progress, attempt, retry_number):
                return False

        raise AssertionError("Transport policy must return within its configured request bound")

    def _next_attempt(
        self, progress: InputExecution, instructions: str, kind: AttemptKind
    ) -> AttemptResult | None:
        """Admit one request after deadline and durable spending checks."""

        remaining = progress.deadline - self._clock.monotonic()

        if remaining <= 0:
            progress.reason = ExecutionReason.INPUT_DEADLINE_EXCEEDED.value

            return None

        request = GenerationRequest.from_contract(
            instructions=instructions,
            source_text=progress.scheduled.job.source_text,
            contract=self._contract,
            sampling=progress.scheduled.job.sampling,
            timeout_seconds=min(self._execution.request_timeout_seconds, remaining),
        )

        if self._admission is not None:
            try:
                evidence = self._admission.check(
                    request, progress.scheduled.target.adapter.identity
                )
            except BudgetStop as error:
                self._stop_budget(progress, error)
                self._save_progress(progress)

                return None
            except AdmissionRejected as error:
                progress.reason = str(error)
                progress.last_failure = None
                self._save_progress(progress)

                return None

            progress.admissions.append(evidence)
            self._save_progress(progress)

        if self._clock.monotonic() >= progress.deadline:
            progress.reason = ExecutionReason.INPUT_DEADLINE_EXCEEDED.value

            return None

        try:
            reservation = self._spending.reserve(
                progress.scheduled, request, attempt_number=len(progress.attempts) + 1
            )
        except BudgetStop as error:
            self._stop_budget(progress, error)

            return None

        # Filesystem reservation time also belongs to the input deadline.
        remaining = progress.deadline - self._clock.monotonic()

        if remaining <= 0:
            try:
                self._spending.reconcile(reservation, 0.0)
            except BudgetStop as error:
                self._stop_budget(progress, error)

                return None

            progress.reason = ExecutionReason.INPUT_DEADLINE_EXCEEDED.value

            return None

        request = request.model_copy(
            update={"timeout_seconds": min(request.timeout_seconds, remaining)}
        )

        return self._request(progress, request, kind, reservation)

    def _request(
        self,
        progress: InputExecution,
        request: GenerationRequest,
        kind: AttemptKind,
        reservation: Reservation | None,
    ) -> AttemptResult:
        adapter = progress.scheduled.target.adapter
        context = AttemptContext(
            number=len(progress.attempts) + 1,
            kind=kind,
            identity=adapter.identity,
            timeout_seconds=request.timeout_seconds,
            reservation=reservation,
        )

        try:
            response = adapter.generate(request)
        except ModelConfigurationError:
            try:
                self._spending.reconcile(reservation, 0.0)
            except BudgetStop as error:
                self._stop_budget(progress, error)

            raise
        except ModelTransportError as error:
            attempt = failure_attempt(context, error.evidence)
        else:
            attempt = response_attempt(
                context,
                response,
                self._contract,
                expired=self._clock.monotonic() >= progress.deadline,
            )

            if self._clock.monotonic() >= progress.deadline:
                values = attempt.model_dump()
                values.update(
                    outcome=AttemptOutcome.DEADLINE_EXCEEDED,
                    error=ExecutionReason.INPUT_DEADLINE_EXCEEDED.value,
                )
                attempt = AttemptResult.model_validate(values)

        progress.attempts.append(attempt)
        self._save_progress(progress)

        try:
            self._spending.reconcile(reservation, attempt.cost_usd)
        except BudgetStop as error:
            self._stop_budget(progress, error)

        return attempt

    def _stop_budget(self, progress: InputExecution, error: BudgetStop) -> None:
        progress.reason = error.reason.value
        progress.budget_stopped = True
        self._spending.note_stop(error)

    def _backoff(self, progress: InputExecution, attempt: AttemptResult, retry_number: int) -> bool:
        failure = attempt.failure

        if failure is None or not failure.retryable or failure.kind not in AVAILABILITY_FAILURES:
            return False

        delay = retry_delay(failure, retry_number, self._execution, self._clock.now())

        if delay is None:
            progress.reason = ExecutionReason.RETRY_AFTER_EXCEEDS_BACKOFF_LIMIT.value

            return False

        remaining = max(0.0, progress.deadline - self._clock.monotonic())
        actual_delay = min(delay, remaining)
        values = attempt.model_dump()
        values["retry_delay_seconds"] = actual_delay
        progress.attempts[-1] = AttemptResult.model_validate(values)
        self._save_progress(progress)
        self._clock.sleep(actual_delay)

        if self._clock.monotonic() >= progress.deadline:
            progress.reason = ExecutionReason.INPUT_DEADLINE_EXCEEDED.value

            return False

        return True

    def _save_progress(self, progress: InputExecution) -> None:
        if self._checkpoint is not None:
            self._checkpoint(progress)

    def summarize(self, records: Iterable[RunRecord]) -> BatchResult:
        """Summarize incrementally saved work without resetting dependency state."""

        return build_batch_result(
            tuple(records),
            self._execution,
            dependencies=self._dependencies,
            budget_stops=self._spending.stops,
        )
