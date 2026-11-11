"""One-call answer execution with shared admission, durable ledger and explicit stops."""

import os
from collections.abc import Callable
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any

from extraction_service.answering.contract import AnswerJob, validate_answer
from extraction_service.application.composition import PreparedTarget
from extraction_service.configuration.models import SamplingConfig
from extraction_service.execution.admission import AdmissionRejected
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop
from extraction_service.execution.policy import Clock, DependencyState
from extraction_service.inference.errors import ModelConfigurationError, ModelTransportError
from extraction_service.inference.types import ResponseKind
from extraction_service.record_types import ExecutionStage
from extraction_service.retrieval.core import canonical


class Outcome(StrEnum):
    SKIPPED = "deterministic_non_answer"
    VALID = "structurally_valid"
    INVALID = "invalid_answer"
    RESPONSE_FAILURE = "response_failure"
    TRANSPORT_FAILURE = "transport_failure"
    NOT_ATTEMPTED = "not_attempted"


class Journal:
    """Exclusive, append-only physical evidence; fsync before send and before settlement."""

    def __init__(self, path: Path) -> None:
        self.path = path
        # Never resume/repeat a partly executed invocation implicitly.
        with path.open("xb"):
            pass

    def append(self, event: dict[str, Any]) -> None:
        with self.path.open("ab") as output:
            output.write(canonical(event) + b"\n")
            output.flush()
            os.fsync(output.fileno())


class AnswerRunner:
    """Borrow prepared resources; only the application owns client lifecycle.

    The MATRIX ledger stage is a legacy funding bucket, not a claim that E03 is
    an extraction matrix. E03 purpose/phase and its separate allowance are saved
    in every journal. Caller approval must explicitly authorize this funding use.
    """

    def __init__(
        self,
        *,
        prepared: PreparedTarget,
        ledger: BudgetLedger,
        journal: Journal,
        clock: Clock,
        allowance: Decimal,
        deadline_seconds: float,
        reported_provider: str,
    ) -> None:
        self.prepared = prepared
        self.ledger = ledger
        self.journal = journal
        self.clock = clock
        self.allowance = allowance
        self.deadline = clock.monotonic() + deadline_seconds
        self.accounted = Decimal("0")
        self.physical_calls = 0
        self.stop_reason: str | None = None
        self.dependency = DependencyState()
        self.reported_provider = reported_provider

    def run(
        self,
        job: AnswerJob,
        *,
        instructions: str,
        sampling: SamplingConfig,
        timeout: float,
        request_key: str,
        revalidate: Callable[[], None],
    ) -> dict[str, Any]:
        """Retain each response/failure exactly once; never retry or correct it."""

        record: dict[str, Any] = {"job": job.model_dump(mode="json"), "key": job.key}
        if job.skip_reason is not None:
            record.update(outcome=Outcome.SKIPPED, reason=job.skip_reason, physical_calls=0)
        elif self.stop_reason is not None:
            record.update(outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0)
        else:
            calls_before = self.physical_calls
            try:
                result = self._call(
                    job,
                    instructions=instructions,
                    sampling=sampling,
                    timeout=timeout,
                    request_key=request_key,
                    revalidate=revalidate,
                )
            except BudgetStop as error:
                if self.physical_calls != calls_before:
                    # A settlement failure after send must not become "not attempted".
                    raise
                self.stop_reason = error.reason.value
                result = dict(
                    outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0
                )
            except AdmissionRejected as error:
                self.stop_reason = error.reason.value
                result = dict(
                    outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0
                )
            record.update(result)
        self.journal.append({"event": "outcome", **record})
        return record

    def _call(
        self,
        job: AnswerJob,
        *,
        instructions: str,
        sampling: SamplingConfig,
        timeout: float,
        request_key: str,
        revalidate: Callable[[], None],
    ) -> dict[str, Any]:
        revalidate()
        remaining = self.deadline - self.clock.monotonic()
        if remaining <= 0:
            self.stop_reason = "phase_deadline"
            return dict(outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0)
        request = job.request(instructions, sampling, min(timeout, remaining))
        target = self.prepared.target
        admission = self.prepared.admission.check(request, target.adapter.identity)
        pricing = self.prepared.pricing
        if pricing is None:
            raise ValueError("Answer execution requires verified pricing")
        amount = pricing.reserve_for(request, target.dependency)
        if self.accounted + amount > self.allowance:
            self.stop_reason = "phase_allowance_insufficient"
            return dict(outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0)
        reservation = self.ledger.reserve(
            amount_usd=amount,
            stage=ExecutionStage.MATRIX,
            request_key=request_key,
            pricing_evidence=pricing.evidence,
        )
        self.journal.append(
            dict(
                event="reserved",
                key=job.key,
                reservation=reservation.model_dump(mode="json"),
                observed_at=self.clock.now().isoformat(),
                request=request.model_dump(mode="json"),
                admission=admission.model_dump(mode="json"),
            )
        )
        if self.clock.monotonic() >= self.deadline:
            self.ledger.settle(reservation.id, Decimal("0"))
            self.stop_reason = "phase_deadline"
            return dict(outcome=Outcome.NOT_ATTEMPTED, reason=self.stop_reason, physical_calls=0)
        response = None
        billed: Decimal | None = None
        self.physical_calls += 1
        try:
            response = target.adapter.generate(request)
        except ModelConfigurationError:
            # Adapter guarantees this exception precedes physical I/O.
            self.physical_calls -= 1
            billed = Decimal("0")
            self.stop_reason = "unsupported_before_send"
            result: dict[str, Any] = dict(
                outcome=Outcome.NOT_ATTEMPTED,
                reason=self.stop_reason,
                physical_calls=0,
            )
        except ModelTransportError as error:
            failure = error.evidence
            billed = None if failure.cost_usd is None else Decimal(str(failure.cost_usd))
            self.dependency.failed_input(failure, limit=3)
            self.stop_reason = self.dependency.stop_reason
            result = dict(
                outcome=Outcome.TRANSPORT_FAILURE,
                physical_calls=1,
                failure=failure.model_dump(mode="json"),
            )
        else:
            billed = None if response.cost_usd is None else Decimal(str(response.cost_usd))
            self.dependency.completed_response()
            result = dict(
                outcome=Outcome.RESPONSE_FAILURE,
                physical_calls=1,
                response=response.model_dump(mode="json"),
            )
            if (
                response.identity != target.adapter.identity
                or response.reported_model != target.adapter.identity.model_name
                or response.serving_provider != self.reported_provider
            ):
                self.stop_reason = "response_identity_mismatch"
                result["reason"] = self.stop_reason
            elif response.kind == ResponseKind.COMPLETED and response.raw_response is not None:
                try:
                    answer = validate_answer(response.raw_response, job)
                    result.update(
                        outcome=Outcome.VALID,
                        answer=answer.model_dump(mode="json"),
                        semantic_review="unreviewed",
                    )
                except ValueError, RecursionError:
                    result.update(outcome=Outcome.INVALID, reason="answer_schema_or_citation")
        # If an unexpected exception escapes, the durable reservation remains
        # unresolved and the phase journal cannot pass continuation checks.
        self.journal.append(
            dict(
                event="physical_result",
                key=job.key,
                observed_at=self.clock.now().isoformat(),
                reservation_id=reservation.id,
                **result,
            )
        )
        self.ledger.settle(reservation.id, billed)
        self.accounted += amount if billed is None else billed
        if billed is None:
            self.stop_reason = "unknown_charge"
        elif billed > amount:
            self.stop_reason = "unsafe_pricing"
        if self.clock.monotonic() >= self.deadline:
            self.stop_reason = "phase_deadline"
        result.update(
            reservation_id=reservation.id,
            accounted_usd=str(amount if billed is None else billed),
            stop_reason=self.stop_reason,
        )
        return result
