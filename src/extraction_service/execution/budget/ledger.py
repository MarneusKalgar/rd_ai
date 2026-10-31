"""Locked, durable homework-wide reservations across models and invocations."""

import fcntl
import hashlib
import os
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Literal, Self
from uuid import uuid4

from pydantic import Field, ValidationError, model_validator

from extraction_service.configuration.models import MAX_EXPERIMENT_BUDGET_USD, ExecutionConfig
from extraction_service.execution.budget.pricing import Money
from extraction_service.record_types import ExecutionStage
from extraction_service.runtime_types import Identifier, NonEmptyText, Sha256, StrictModel


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


class BudgetRevision(StrictModel):
    """User-authorized cap raise backed by the exact previous ledger bytes."""

    previous_budget_usd: Money
    budget_usd: Money
    previous_sha256: Sha256
    evidence: NonEmptyText
    observed_at: str


class BudgetSnapshot(StrictModel):
    """Persisted policy and reservations; totals are derived from original entries."""

    version: Literal["budget-v1"] = "budget-v1"
    budget_usd: Money
    matrix_reserve_usd: Money
    opening_spend_usd: Money
    opening_evidence: NonEmptyText
    reservations: list[Reservation]
    policy_revisions: list[BudgetRevision] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_policy(self) -> Self:
        if not Decimal("0") < self.budget_usd <= Decimal(str(MAX_EXPERIMENT_BUDGET_USD)):
            raise ValueError("Ledger budget exceeds the experiment ceiling")

        if self.matrix_reserve_usd >= self.budget_usd:
            raise ValueError("Ledger matrix reserve must stay below its budget")

        identifiers = [entry.id for entry in self.reservations]

        if len(identifiers) != len(set(identifiers)):
            raise ValueError("Duplicate reservation identity")

        previous = None

        for revision in self.policy_revisions:
            if not Decimal("0") < revision.previous_budget_usd < revision.budget_usd:
                raise ValueError("Budget revision must increase a positive cap")

            if previous is not None and revision.previous_budget_usd != previous:
                raise ValueError("Budget revision chain is discontinuous")

            previous = revision.budget_usd

        if previous is not None and previous != self.budget_usd:
            raise ValueError("Budget revisions do not match the current cap")

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

    def raise_cap(self, *, expected_budget_usd: Decimal, evidence: str) -> BudgetSnapshot:
        """Raise to the configured cap explicitly, retaining charges and an audited backup.

        A missing/corrupt ledger is never initialized. A completed raise cannot
        be replayed; a failed atomic replacement can retry against its same backup.
        """

        with self._locked():
            try:
                original = self.path.read_bytes()
                snapshot = BudgetSnapshot.model_validate_json(original)
            except OSError, ValidationError:
                raise BudgetStop(BudgetStopReason.UNAVAILABLE) from None

            new_budget = Decimal(str(self.policy.api_budget_usd))

            if snapshot.budget_usd != expected_budget_usd:
                raise ValueError("Ledger cap differs from the expected previous cap")

            if new_budget <= snapshot.budget_usd:
                raise ValueError("New budget must strictly increase the current cap")

            if snapshot.matrix_reserve_usd != Decimal(str(self.policy.matrix_reserve_usd)):
                raise ValueError("A cap raise cannot change the matrix reserve")

            digest = hashlib.sha256(original).hexdigest()
            revision = BudgetRevision(
                previous_budget_usd=snapshot.budget_usd,
                budget_usd=new_budget,
                previous_sha256=digest,
                evidence=evidence,
                observed_at=datetime.now(UTC).isoformat(),
            )
            updated = BudgetSnapshot.model_validate(
                {
                    **snapshot.model_dump(),
                    "budget_usd": new_budget,
                    "policy_revisions": [*snapshot.policy_revisions, revision],
                }
            )
            directory = self.path.parent / "budget-policy"
            directory.mkdir(exist_ok=True)
            backup = directory / f"{digest}.json"

            if backup.exists():
                if backup.read_bytes() != original:
                    raise ValueError("Budget policy backup differs from its expected hash")
            else:
                with backup.open("xb") as output:
                    output.write(original)
                    output.flush()
                    os.fsync(output.fileno())

            descriptor = os.open(directory, os.O_RDONLY)

            try:
                os.fsync(descriptor)
            finally:
                os.close(descriptor)

            self._write(updated)

            return updated

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
