import json
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from pathlib import Path

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop, BudgetStopReason
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.types import GenerationRequest, ModelIdentity, ModelResponse
from extraction_service.record_types import ExecutionStage

from .helpers import FakeClock, ScriptedAdapter, failure, response


def test_ledger_reserves_before_request_reconciles_and_reopens(
    ledger: BudgetLedger, policy: ExecutionConfig, tmp_path: Path
) -> None:
    entry = ledger.reserve(
        amount_usd=Decimal("0.20"),
        stage=ExecutionStage.SMOKE,
        request_key="smoke/1",
        pricing_evidence="test upper bound",
    )
    assert ledger.snapshot().accounted_usd == Decimal("0.20")

    ledger.settle(entry.id, Decimal("0.05"))
    reopened = BudgetLedger(tmp_path, policy)
    snapshot = reopened.snapshot()

    assert snapshot.accounted_usd == Decimal("0.05")
    assert snapshot.reservations[0].billed_usd == Decimal("0.05")
    assert snapshot.reservations[0].reserved_usd == Decimal("0.20")

    with pytest.raises(FileExistsError):
        reopened.initialize(opening_spend_usd=Decimal("0"), evidence="attempted reset")

    with pytest.raises(ValueError, match="already settled"):
        reopened.settle(entry.id, Decimal("0"))


@pytest.mark.parametrize("resolved", [False, True])
def test_unknown_billing_and_crash_reservations_are_not_released(
    ledger: BudgetLedger, policy: ExecutionConfig, tmp_path: Path, resolved: bool
) -> None:
    entry = ledger.reserve(
        amount_usd=Decimal("0.80"),
        stage=ExecutionStage.MATRIX,
        request_key="matrix/1",
        pricing_evidence="test upper bound",
    )

    if resolved:
        ledger.settle(entry.id, None)

    reopened = BudgetLedger(tmp_path, policy)
    snapshot = reopened.snapshot()

    assert snapshot.accounted_usd == Decimal("0.80")
    assert snapshot.reservations[0].resolved is resolved

    with pytest.raises(BudgetStop) as raised:
        reopened.reserve(
            amount_usd=Decimal("0.21"),
            stage=ExecutionStage.MATRIX,
            request_key="other-model/2",
            pricing_evidence="another test bound",
        )

    assert raised.value.reason == BudgetStopReason.INSUFFICIENT
    assert len(reopened.snapshot().reservations) == 1


def test_prior_spend_and_matrix_holdback_apply_across_models_and_stages(
    tmp_path: Path, policy: ExecutionConfig
) -> None:
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0.10"), evidence="Earlier external smoke")
    first = ledger.reserve(
        amount_usd=Decimal("0.20"),
        stage=ExecutionStage.SCREENING,
        request_key="candidate-a/1",
        pricing_evidence="test prices",
    )
    ledger.settle(first.id, Decimal("0.20"))

    with pytest.raises(BudgetStop) as raised:
        ledger.reserve(
            amount_usd=Decimal("0.21"),
            stage=ExecutionStage.REPETITION,
            request_key="candidate-b/1",
            pricing_evidence="test prices",
        )

    assert raised.value.reason == BudgetStopReason.MATRIX_PROTECTED

    matrix = ledger.reserve(
        amount_usd=Decimal("0.50"),
        stage=ExecutionStage.MATRIX,
        request_key="required-model/1",
        pricing_evidence="test prices",
    )
    ledger.settle(matrix.id, Decimal("0.40"))
    snapshot = ledger.snapshot()

    assert snapshot.accounted_usd == Decimal("0.70")
    assert snapshot.protected_matrix_usd == Decimal("0.10")


def test_concurrent_reservations_cannot_overspend(ledger: BudgetLedger) -> None:
    def reserve(index: int) -> bool:
        try:
            ledger.reserve(
                amount_usd=Decimal("0.20"),
                stage=ExecutionStage.MATRIX,
                request_key=f"matrix/{index}",
                pricing_evidence="test prices",
            )
        except BudgetStop as error:
            assert error.reason == BudgetStopReason.INSUFFICIENT

            return False

        return True

    with ThreadPoolExecutor(max_workers=8) as workers:
        outcomes = list(workers.map(reserve, range(12)))

    assert sum(outcomes) == 5
    assert ledger.snapshot().accounted_usd == Decimal("1.00")
    assert len(ledger.snapshot().reservations) == 5


@pytest.mark.parametrize("defect", ["missing", "corrupt", "changed-policy"])
def test_ledger_failures_stop_before_paid_inference(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    clock: FakeClock,
    tmp_path: Path,
    defect: str,
) -> None:
    ledger = BudgetLedger(tmp_path, policy)

    if defect != "missing":
        ledger.initialize(opening_spend_usd=Decimal("0"), evidence="test opening")

        if defect == "corrupt":
            ledger.path.write_text("{broken ledger")
        else:
            data = json.loads(ledger.path.read_text())
            data["budget_usd"] = "4.99"
            ledger.path.write_text(json.dumps(data))

    adapter = ScriptedAdapter(paid_identity, clock, [])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)
    task = ScheduledExtraction(
        job, ExecutionTarget(adapter, "https://provider.test/api/v1"), pricing
    )

    batch = coordinator.execute_many([task, task])

    assert [record.status for record in batch.records] == ["not_attempted", "not_attempted"]
    assert batch.records[0].reason == "budget_unavailable"
    assert batch.records[0].attempts == []
    assert adapter.requests == []
    assert batch.summary.dependency_stops == []
    assert batch.summary.budget_stops == ["budget_unavailable"]


def test_paid_retries_and_correction_each_reserve_before_call_and_reconcile_all_costs(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
) -> None:
    class CheckingAdapter(ScriptedAdapter):
        def generate(self, request: GenerationRequest) -> ModelResponse:
            snapshot = ledger.snapshot()

            assert len(snapshot.reservations) == len(self.requests) + 1
            assert not snapshot.reservations[-1].resolved

            return super().generate(request)

    adapter = CheckingAdapter(
        paid_identity,
        clock,
        [
            failure(),
            response(paid_identity, "{}"),
            response(paid_identity, json.dumps(gold)),
        ],
    )
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(
            job,
            ExecutionTarget(adapter, "https://provider.test/api/v1"),
            pricing,
        )
    )
    snapshot = ledger.snapshot()

    assert record.status == "succeeded"
    assert len(snapshot.reservations) == len(adapter.requests) == 3
    assert [entry.reserved_usd for entry in snapshot.reservations] == [Decimal("0.20")] * 3
    assert [entry.billed_usd for entry in snapshot.reservations] == [
        None,
        Decimal("0.05"),
        Decimal("0.05"),
    ]
    assert snapshot.accounted_usd == Decimal("0.30")
    assert record.total_cost_usd is None
    assert record.attempts[0].accounting_note is not None
    assert record.attempts[0].budget_reserved_usd == 0.2
    assert all(attempt.budget_reservation_id for attempt in record.attempts)


def test_budget_blocks_correction_without_relabeling_attempt_as_unattempted(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    clock: FakeClock,
    tmp_path: Path,
) -> None:
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0.79"), evidence="Previous homework requests")
    reply = response(paid_identity, "{}").model_copy(update={"cost_usd": None})
    adapter = ScriptedAdapter(paid_identity, clock, [reply])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)
    task = ScheduledExtraction(
        job, ExecutionTarget(adapter, "https://provider.test/api/v1"), pricing
    )

    batch = coordinator.execute_many([task, task])

    assert [record.status for record in batch.records] == ["failed", "not_attempted"]
    assert batch.records[0].reason == "budget_insufficient"
    assert len(batch.records[0].attempts) == 1
    assert batch.records[0].attempts[0].outcome == "invalid"
    assert batch.records[1].attempts == []
    assert batch.summary.dependency_stops == []
    assert ledger.snapshot().accounted_usd == Decimal("0.99")


def test_unexpected_paid_defect_retains_reservation(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
) -> None:
    adapter = ScriptedAdapter(paid_identity, clock, [RuntimeError("defect")])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    with pytest.raises(RuntimeError, match="defect"):
        coordinator.execute(
            ScheduledExtraction(
                job,
                ExecutionTarget(adapter, "https://provider.test/api/v1"),
                pricing,
            )
        )

    snapshot = ledger.snapshot()

    assert snapshot.accounted_usd == Decimal("0.20")
    assert not snapshot.reservations[0].resolved
    assert len(adapter.requests) == 1


def test_unsafe_pricing_stops_paid_route_and_independent_local_work_continues(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    local_identity: ModelIdentity,
    ledger: BudgetLedger,
    clock: FakeClock,
    pricing: VerifiedPricing,
) -> None:
    paid = ScriptedAdapter(paid_identity, clock, [])
    local = ScriptedAdapter(local_identity, clock, [response(local_identity, json.dumps(gold))])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    batch = coordinator.execute_many(
        [
            ScheduledExtraction(job, ExecutionTarget(paid, "https://provider.test/api/v1")),
            ScheduledExtraction(job, ExecutionTarget(local, "http://ollama:11434")),
            ScheduledExtraction(
                job, ExecutionTarget(paid, "https://provider.test/api/v1"), pricing
            ),
        ]
    )

    assert [record.status for record in batch.records] == [
        "not_attempted",
        "succeeded",
        "not_attempted",
    ]
    assert batch.records[0].reason == "unsafe_pricing"
    assert paid.requests == []
    assert ledger.snapshot().reservations == []


@pytest.mark.parametrize("billed_cost", [0.25, 1.25])
def test_reported_cost_above_reservation_is_preserved_and_stops_next_request(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
    billed_cost: float,
) -> None:
    reply = response(paid_identity, json.dumps(gold)).model_copy(update={"cost_usd": billed_cost})
    adapter = ScriptedAdapter(paid_identity, clock, [reply])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)
    task = ScheduledExtraction(
        job, ExecutionTarget(adapter, "https://provider.test/api/v1"), pricing
    )

    batch = coordinator.execute_many([task, task])

    assert [record.status for record in batch.records] == ["succeeded", "not_attempted"]
    assert ledger.snapshot().accounted_usd == Decimal(str(billed_cost))
    assert batch.records[0].total_cost_usd == billed_cost
    assert batch.records[1].reason == "unsafe_pricing"
