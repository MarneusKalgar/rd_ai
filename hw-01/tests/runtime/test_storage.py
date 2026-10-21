import json
from decimal import Decimal
from pathlib import Path

import pytest

from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.preflight import preflight
from extraction_service.record_types import ExecutionStage
from extraction_service.runtime.storage import setup_lock, verify_storage, write_report


def test_storage_reuses_identity_and_exercises_atomic_replacement(tmp_path: Path) -> None:
    first = verify_storage(tmp_path)
    repeated = verify_storage(tmp_path)

    assert first["storage_id"] == repeated["storage_id"]
    assert first["reused"] is False
    assert repeated["reused"] is True
    assert list(tmp_path.glob(".storage-probe-*")) == []


def test_setup_lock_rejects_concurrent_operation_and_releases_after_failure(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="simulated"):
        with setup_lock(tmp_path):
            with pytest.raises(ValueError, match="Another setup operation"):
                with setup_lock(tmp_path):
                    raise AssertionError("Concurrent setup entered its critical section")

            raise RuntimeError("simulated")

    with setup_lock(tmp_path) as directory:
        assert directory.is_dir()


def test_failed_serialization_retains_prior_evidence(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    write_report(path, {"version": 1})

    with pytest.raises(ValueError):
        write_report(path, {"measurement": float("nan")})

    assert json.loads(path.read_text()) == {"version": 1}


def test_setup_preserves_real_ledger_accounting_and_unresolved_reservations(
    project_copy: Path,
) -> None:
    policy = preflight(project_copy).experiment.execution
    ledger = BudgetLedger(project_copy, policy)
    ledger.initialize(opening_spend_usd=Decimal("0.25"), evidence="test-only prior spend")
    reservation = ledger.reserve(
        amount_usd=Decimal("0.10"),
        stage=ExecutionStage.MATRIX,
        request_key="test-only-unknown-charge",
        pricing_evidence="test-only evidence",
    )
    before = ledger.path.read_bytes()
    lock_inode = ledger.path.with_suffix(".lock").stat().st_ino

    verify_storage(project_copy / "results")
    verify_storage(project_copy / "results")
    reopened = BudgetLedger(project_copy, policy).snapshot()

    assert ledger.path.read_bytes() == before
    assert ledger.path.with_suffix(".lock").stat().st_ino == lock_inode
    assert reopened.accounted_usd == Decimal("0.35")
    assert reopened.reservations[0].id == reservation.id
    assert reopened.reservations[0].resolved is False
