"""Locked, durable homework-wide reservations across models and invocations."""

import fcntl
import os
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Self
from uuid import uuid4

from pydantic import ValidationError, model_validator

from extraction_service.configuration.models import ASSIGNMENT_API_CAP_USD, ExecutionConfig
from extraction_service.execution.budget.pricing import Money
from extraction_service.record_types import ExecutionStage
from extraction_service.runtime_types import Identifier, NonEmptyText, StrictModel


class BudgetStopReason(StrEnum):
    """Expected spending stops, distinct from dependency-availability failures."""

    UNAVAILABLE = "budget_unavailable"
    INSUFFICIENT = "budget_insufficient"
    MATRIX_PROTECTED = "matrix_budget_protected"
    UNSAFE_PRICING = "unsafe_pricing"


class BudgetStop(ValueError):
    """Further paid work cannot safely proceed; local work may continue."""

    def __init__(self, reason: BudgetStopReason) -> None:
        self.reason = reason

        super().__init__(reason.value)


class Reservation(StrictModel):
    """One persisted pre-request allowance, retained if billing is unavailable."""

    id: Identifier
    request_key: NonEmptyText
    stage: ExecutionStage
    reserved_usd: Money
    pricing_evidence: NonEmptyText
    billed_usd: Money | None = None
    resolved: bool = False

    @property
    def accounted_usd(self) -> Decimal:
        return self.reserved_usd if self.billed_usd is None else self.billed_usd

    @model_validator(mode="after")
    def check_resolution(self) -> Self:
        if self.billed_usd is not None and not self.resolved:
            raise ValueError("Billed cost requires a resolved request")

        return self


class BudgetSnapshot(StrictModel):
    """Persisted policy and reservations; totals are derived from original entries."""

    version: Literal["budget-v1"] = "budget-v1"
    budget_usd: Money
    matrix_reserve_usd: Money
    opening_spend_usd: Money
    opening_evidence: NonEmptyText
    reservations: list[Reservation]

    @model_validator(mode="after")
    def check_policy(self) -> Self:
        if not Decimal("0") < self.budget_usd < Decimal(str(ASSIGNMENT_API_CAP_USD)):
            raise ValueError("Ledger budget must stay below the assignment cap")

        if self.matrix_reserve_usd >= self.budget_usd:
            raise ValueError("Ledger matrix reserve must stay below its budget")

        identifiers = [entry.id for entry in self.reservations]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate reservation identity")

        return self

    @property
    def accounted_usd(self) -> Decimal:
        return self.opening_spend_usd + sum(
            (entry.accounted_usd for entry in self.reservations), start=Decimal("0")
        )

    @property
    def protected_matrix_usd(self) -> Decimal:
        matrix_spend = sum(
            (
                entry.accounted_usd
                for entry in self.reservations
                if entry.stage == ExecutionStage.MATRIX
            ),
            start=Decimal("0"),
        )

        return max(Decimal("0"), self.matrix_reserve_usd - matrix_spend)


class BudgetLedger:
    """Use one fixed ledger below the HW root; never initialize it implicitly.

    Application setup must explicitly initialize once with prior homework spend,
    including smoke/screening outside this runner. Atomic replacement plus a
    separate advisory lock prevents lost updates across cooperating processes.
    Mount the results directory persistently when the application runs in Docker.
    """

    def __init__(self, project_dir: Path, policy: ExecutionConfig) -> None:
        self.path = project_dir / "results" / "budget-ledger.json"
        self.policy = policy

    @contextmanager
    def _locked(self) -> Generator[None]:
        with ExitStack() as resources:
            try:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                lock = resources.enter_context(self.path.with_suffix(".lock").open("a"))
                fcntl.flock(lock, fcntl.LOCK_EX)
            except OSError:
                raise BudgetStop(BudgetStopReason.UNAVAILABLE) from None

            # Closing this descriptor releases its advisory lock, including on errors.
            yield

    def initialize(self, *, opening_spend_usd: Decimal, evidence: str) -> None:
        """Record prior spending explicitly; refuse to replace an existing ledger."""

        snapshot = BudgetSnapshot(
            budget_usd=Decimal(str(self.policy.api_budget_usd)),
            matrix_reserve_usd=Decimal(str(self.policy.matrix_reserve_usd)),
            opening_spend_usd=opening_spend_usd,
            opening_evidence=evidence,
            reservations=[],
        )

        with self._locked():
            if self.path.exists():
                raise FileExistsError("Homework budget ledger already exists")

            self._write(snapshot)

    def _read(self) -> BudgetSnapshot:
        try:
            snapshot = BudgetSnapshot.model_validate_json(self.path.read_bytes())
        except OSError, ValidationError:
            raise BudgetStop(BudgetStopReason.UNAVAILABLE) from None

        if snapshot.budget_usd != Decimal(
            str(self.policy.api_budget_usd)
        ) or snapshot.matrix_reserve_usd != Decimal(str(self.policy.matrix_reserve_usd)):
            raise BudgetStop(BudgetStopReason.UNAVAILABLE)

        return snapshot

    def _write(self, snapshot: BudgetSnapshot) -> None:
        temporary_path: Path | None = None

        try:
            with NamedTemporaryFile(mode="w", dir=self.path.parent, delete=False) as temporary:
                temporary_path = Path(temporary.name)
                temporary.write(snapshot.model_dump_json(indent=2))
                temporary.flush()
                os.fsync(temporary.fileno())

            temporary_path.replace(self.path)

            directory = os.open(self.path.parent, os.O_RDONLY)

            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except OSError:
            raise BudgetStop(BudgetStopReason.UNAVAILABLE) from None
        finally:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)

    def snapshot(self) -> BudgetSnapshot:
        with self._locked():
            return self._read()

    def reserve(
        self,
        *,
        amount_usd: Decimal,
        stage: ExecutionStage,
        request_key: str,
        pricing_evidence: str,
    ) -> Reservation:
        """Durably reserve before inference; optional work cannot consume matrix funds."""

        reservation = Reservation(
            id=uuid4().hex,
            request_key=request_key,
            stage=stage,
            reserved_usd=amount_usd,
            pricing_evidence=pricing_evidence,
        )

        with self._locked():
            snapshot = self._read()
            available = snapshot.budget_usd - snapshot.accounted_usd

            if amount_usd > available:
                raise BudgetStop(BudgetStopReason.INSUFFICIENT)

            if stage != ExecutionStage.MATRIX:
                if snapshot.matrix_reserve_usd == 0:
                    raise BudgetStop(BudgetStopReason.MATRIX_PROTECTED)

                if amount_usd > available - snapshot.protected_matrix_usd:
                    raise BudgetStop(BudgetStopReason.MATRIX_PROTECTED)

            updated = snapshot.model_copy(
                update={"reservations": [*snapshot.reservations, reservation]}
            )
            self._write(updated)

        return reservation

    def settle(self, reservation_id: str, billed_usd: Decimal | None) -> None:
        """Reconcile reported cost; unresolved charges continue consuming their allowance."""

        with self._locked():
            snapshot = self._read()
            entries = list(snapshot.reservations)

            for index, entry in enumerate(entries):
                if entry.id != reservation_id:
                    continue

                if entry.resolved:
                    raise ValueError("Reservation was already settled")

                values = entry.model_dump()
                values.update(billed_usd=billed_usd, resolved=True)
                entries[index] = Reservation.model_validate(values)
                self._write(snapshot.model_copy(update={"reservations": entries}))

                return

            raise ValueError("Unknown budget reservation")
