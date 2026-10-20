"""Invocation-wide paid-request policy layered over the persistent homework ledger."""

from decimal import Decimal

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget import (
    BudgetLedger,
    BudgetStop,
    BudgetStopReason,
    Reservation,
)
from extraction_service.execution.types import ScheduledExtraction
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import ModelRuntime


class SpendingGuard:
    """Own paid stop state, request admission and reconciliation for one invocation."""

    def __init__(self, execution: ExecutionConfig, ledger: BudgetLedger | None) -> None:
        if ledger is not None and (
            ledger.policy.api_budget_usd != execution.api_budget_usd
            or ledger.policy.matrix_reserve_usd != execution.matrix_reserve_usd
        ):
            raise ValueError("Coordinator and ledger budget policies differ")

        self._ledger = ledger
        self._paid_stop: BudgetStopReason | None = None
        self._stops: set[BudgetStopReason] = set()

    @property
    def paid_stop(self) -> BudgetStopReason | None:
        return self._paid_stop

    @property
    def stops(self) -> frozenset[BudgetStopReason]:
        return frozenset(self._stops)

    def note_stop(self, error: BudgetStop) -> None:
        self._stops.add(error.reason)

        if error.reason in (
            BudgetStopReason.UNAVAILABLE,
            BudgetStopReason.INSUFFICIENT,
            BudgetStopReason.UNSAFE_PRICING,
        ):
            self._paid_stop = error.reason

    def reserve(
        self,
        scheduled: ScheduledExtraction,
        request: GenerationRequest,
        *,
        attempt_number: int,
    ) -> Reservation | None:
        """Admit one physical paid request using route-specific verified coverage."""

        if scheduled.target.adapter.identity.runtime != ModelRuntime.OPENROUTER:
            return None

        if self._paid_stop is not None or self._ledger is None:
            raise BudgetStop(BudgetStopReason.UNAVAILABLE)

        if scheduled.pricing is None:
            raise BudgetStop(BudgetStopReason.UNSAFE_PRICING)

        try:
            amount = scheduled.pricing.reserve_for(request, scheduled.target.dependency)
        except ValueError:
            raise BudgetStop(BudgetStopReason.UNSAFE_PRICING) from None

        job = scheduled.job
        request_key = (
            f"{job.run_id}/{job.input_id}/{scheduled.target.adapter.identity.model_id}/"
            f"{job.prompt_id}/{job.sampling.id}/{attempt_number}"
        )

        return self._ledger.reserve(
            amount_usd=amount,
            stage=job.stage,
            request_key=request_key,
            pricing_evidence=scheduled.pricing.evidence,
        )

    def reconcile(self, reservation: Reservation | None, billed_usd: float | None) -> None:
        """Settle available cost and retain every stop when the pricing bound fails."""

        if reservation is None:
            return

        if self._ledger is None:
            raise BudgetStop(BudgetStopReason.UNAVAILABLE)

        billed = None if billed_usd is None else Decimal(str(billed_usd))
        stop: BudgetStop | None = None

        try:
            self._ledger.settle(reservation.id, billed)
        except BudgetStop as error:
            self.note_stop(error)
            stop = error

        if billed is not None and billed > reservation.reserved_usd:
            stop = BudgetStop(BudgetStopReason.UNSAFE_PRICING)
            self.note_stop(stop)

        if stop is not None:
            raise stop
