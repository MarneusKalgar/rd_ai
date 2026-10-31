"""Explicit cap raises preserve billing evidence and recover without resetting it."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import pytest

from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop
from extraction_service.record_types import ExecutionStage


def revised(ledger: BudgetLedger) -> BudgetLedger:
    policy = ledger.policy.model_copy(update={"api_budget_usd": 10.0})
    return BudgetLedger(ledger.path.parents[1], policy)


def test_raise_preserves_unknown_charges_and_exact_backup(ledger: BudgetLedger) -> None:
    entry = ledger.reserve(
        amount_usd=Decimal("0.2"),
        stage=ExecutionStage.MATRIX,
        request_key="prior/unknown",
        pricing_evidence="test bound",
    )
    ledger.settle(entry.id, None)
    original = ledger.path.read_bytes()
    before = ledger.snapshot()
    target = revised(ledger)

    with pytest.raises(BudgetStop):
        target.snapshot()

    after = target.raise_cap(expected_budget_usd=before.budget_usd, evidence="Test user approval")

    assert after.budget_usd == Decimal("10")
    assert after.accounted_usd == before.accounted_usd == Decimal("0.2")
    assert after.reservations == before.reservations
    assert after.opening_spend_usd == before.opening_spend_usd
    assert after.opening_evidence == before.opening_evidence
    assert after.matrix_reserve_usd == before.matrix_reserve_usd
    assert after.protected_matrix_usd == before.protected_matrix_usd
    digest = hashlib.sha256(original).hexdigest()
    assert (ledger.path.parent / "budget-policy" / f"{digest}.json").read_bytes() == original
    assert after.policy_revisions[0].previous_sha256 == digest
    assert after.policy_revisions[0].evidence == "Test user approval"
    assert target.snapshot() == after

    with pytest.raises(ValueError, match="expected previous cap"):
        target.raise_cap(expected_budget_usd=before.budget_usd, evidence="Replay")


@pytest.mark.parametrize("defect", ["expected-cap", "decrease", "reserve", "empty-evidence"])
def test_raise_rejects_invalid_policy_without_modification(
    ledger: BudgetLedger, defect: str
) -> None:
    original = ledger.path.read_bytes()
    target = revised(ledger)
    expected = ledger.snapshot().budget_usd
    evidence = "Test authorization"

    if defect == "expected-cap":
        expected = Decimal("0.1")
    elif defect == "decrease":
        target.policy = ledger.policy.model_copy(update={"api_budget_usd": 0.9})
    elif defect == "reserve":
        target.policy = target.policy.model_copy(update={"matrix_reserve_usd": 0.1})
    else:
        evidence = ""

    with pytest.raises(ValueError):
        target.raise_cap(expected_budget_usd=expected, evidence=evidence)

    assert ledger.path.read_bytes() == original
    assert not (ledger.path.parent / "budget-policy").exists()


@pytest.mark.parametrize("corrupt", [False, True])
def test_raise_never_initializes_missing_or_corrupt_ledger(
    ledger: BudgetLedger, corrupt: bool
) -> None:
    if corrupt:
        ledger.path.write_text("{broken")
    else:
        ledger.path.unlink()

    with pytest.raises(BudgetStop):
        revised(ledger).raise_cap(expected_budget_usd=Decimal("1"), evidence="Test approval")

    if corrupt:
        assert ledger.path.read_text() == "{broken"
    else:
        assert not ledger.path.exists()


def test_failed_replacement_can_retry_with_unchanged_backup(
    ledger: BudgetLedger, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = ledger.path.read_bytes()
    target = revised(ledger)
    expected = ledger.snapshot().budget_usd

    def fail_write(*_args: object) -> None:
        raise OSError("simulated replace failure")

    with monkeypatch.context() as patch:
        patch.setattr(target, "_write", fail_write)
        with pytest.raises(OSError, match="simulated replace failure"):
            target.raise_cap(expected_budget_usd=expected, evidence="Test approval")

    assert ledger.path.read_bytes() == original
    assert len(list((ledger.path.parent / "budget-policy").glob("*.json"))) == 1
    after = target.raise_cap(expected_budget_usd=expected, evidence="Test approval")
    assert after.budget_usd == Decimal("10")
    assert len(after.policy_revisions) == 1


def test_concurrent_raises_only_record_one_revision(ledger: BudgetLedger) -> None:
    expected = ledger.snapshot().budget_usd

    def raise_once(_index: int) -> bool:
        try:
            revised(ledger).raise_cap(expected_budget_usd=expected, evidence="Test approval")
        except ValueError as error:
            assert "expected previous cap" in str(error)
            return False
        return True

    with ThreadPoolExecutor(max_workers=2) as workers:
        outcomes = list(workers.map(raise_once, range(2)))

    assert sum(outcomes) == 1
    assert len(revised(ledger).snapshot().policy_revisions) == 1
