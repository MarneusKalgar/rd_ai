"""Budget stops preserve paid evidence without blocking affordable independent work."""

import json
from decimal import Decimal
from pathlib import Path

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop, BudgetStopReason
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.coordinator import ExtractionCoordinator
from extraction_service.execution.types import ExecutionTarget, ExtractionJob, ScheduledExtraction
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import ExecutionStage

from .helpers import FakeClock, ScriptedAdapter, response


def test_settlement_failure_retains_evidence_and_stops_only_paid_work(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    local_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settlement_calls: list[tuple[str, Decimal | None]] = []

    def fail_settlement(reservation_id: str, billed_usd: Decimal | None) -> None:
        settlement_calls.append((reservation_id, billed_usd))

        raise BudgetStop(BudgetStopReason.UNAVAILABLE)

    monkeypatch.setattr(ledger, "settle", fail_settlement)
    paid_reply = response(paid_identity, json.dumps(gold))
    paid = ScriptedAdapter(paid_identity, clock, [paid_reply, paid_reply])
    local_reply = response(local_identity, json.dumps(gold))
    local = ScriptedAdapter(local_identity, clock, [local_reply])
    paid_task = ScheduledExtraction(
        job, ExecutionTarget(paid, "https://provider.test/api/v1"), pricing
    )
    local_task = ScheduledExtraction(job, ExecutionTarget(local, "http://ollama:11434"))
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    batch = coordinator.execute_many([paid_task, paid_task, local_task])
    snapshot = ledger.snapshot()
    reservation = snapshot.reservations[0]

    assert [record.status for record in batch.records] == [
        "succeeded",
        "not_attempted",
        "succeeded",
    ]
    assert batch.records[0].attempts[0].response == paid_reply
    assert batch.records[0].total_cost_usd == 0.05
    assert batch.records[1].reason == "budget_unavailable"
    assert batch.records[1].attempts == []
    assert batch.summary.budget_stops == [BudgetStopReason.UNAVAILABLE]
    assert batch.summary.dependency_stops == []
    assert not batch.summary.comparison_complete
    assert len(paid.requests) == len(local.requests) == 1
    assert len(snapshot.reservations) == 1
    assert settlement_calls == [(reservation.id, Decimal("0.05"))]
    assert snapshot.accounted_usd == Decimal("0.20")
    assert reservation.billed_usd is None
    assert not reservation.resolved


def test_zero_matrix_allocation_blocks_optional_work_but_allows_matrix(
    policy: ExecutionConfig, tmp_path: Path
) -> None:
    configured = policy.model_copy(update={"matrix_reserve_usd": 0.0})
    ledger = BudgetLedger(tmp_path, configured)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="No prior test spending")

    with pytest.raises(BudgetStop) as raised:
        ledger.reserve(
            amount_usd=Decimal("0.20"),
            stage=ExecutionStage.SMOKE,
            request_key="optional-smoke",
            pricing_evidence="Fictional test price bound",
        )

    assert raised.value.reason is BudgetStopReason.MATRIX_PROTECTED
    assert ledger.snapshot().reservations == []

    reservation = ledger.reserve(
        amount_usd=Decimal("0.20"),
        stage=ExecutionStage.MATRIX,
        request_key="required-matrix",
        pricing_evidence="Fictional test price bound",
    )
    snapshot = ledger.snapshot()

    assert snapshot.reservations == [reservation]
    assert snapshot.accounted_usd == Decimal("0.20")


def test_optional_holdback_rejection_still_allows_affordable_matrix_work(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    clock: FakeClock,
    tmp_path: Path,
) -> None:
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0.40"), evidence="Earlier test spending")
    reply = response(paid_identity, json.dumps(gold))
    adapter = ScriptedAdapter(paid_identity, clock, [reply])
    target = ExecutionTarget(adapter, "https://provider.test/api/v1")
    optional_job = job.model_copy(update={"stage": ExecutionStage.SMOKE})
    optional = ScheduledExtraction(optional_job, target, pricing)
    required = ScheduledExtraction(job, target, pricing)
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    batch = coordinator.execute_many([optional, required])
    snapshot = ledger.snapshot()

    assert [record.status for record in batch.records] == ["not_attempted", "succeeded"]
    assert batch.records[0].reason == "matrix_budget_protected"
    assert batch.records[0].attempts == []
    assert batch.records[1].attempts[0].response == reply
    assert batch.summary.budget_stops == [BudgetStopReason.MATRIX_PROTECTED]
    assert batch.summary.dependency_stops == []
    assert len(adapter.requests) == 1
    assert len(snapshot.reservations) == 1
    assert snapshot.reservations[0].stage is ExecutionStage.MATRIX
    assert snapshot.reservations[0].resolved
    assert snapshot.accounted_usd == Decimal("0.45")
