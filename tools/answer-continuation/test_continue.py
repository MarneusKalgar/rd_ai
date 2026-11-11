"""Continuation membership, cost ownership and approval controls without inference."""

import json
import subprocess
import sys
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from typing import Any

import continue_run
import pytest
from pydantic import SecretStr
from test_recover import Adapter

from extraction_service.answering.cli import RUN_DIRECTORY
from extraction_service.answering.contract import AnswerJob, Arm, Context
from extraction_service.answering.protocol import load_profile
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.inference.openrouter.capabilities import (
    REQUIRED_OPENROUTER_PARAMETERS,
    OpenRouterEndpoint,
)
from extraction_service.record_types import ExecutionStage


def evidence() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[AnswerJob]]:
    context = Context(source_id="rule", revision="1", sha256="a" * 64, start=0, end=3, quote="one")
    jobs = [
        AnswerJob(
            case_id="fixture",
            arm=arm,
            scope="A",
            question="field meaning",
            context=[] if arm == Arm.NONE else [context],
            retrieval_status="evidence_found",
        )
        for arm in Arm
    ]
    rows: list[dict[str, Any]] = [
        dict(
            key=job.key,
            job=job.model_dump(mode="json"),
            physical_calls=1,
            outcome="structurally_valid",
            stop_reason=None,
        )
        for job in jobs
    ]
    original: list[dict[str, Any]] = [
        rows[0],
        *(
            dict(
                key=job.key,
                job=job.model_dump(mode="json"),
                physical_calls=0,
                outcome="not_attempted",
                reason="phase_allowance_insufficient",
            )
            for job in jobs[1:]
        ),
    ]
    return original, rows[1:], jobs


def test_joint_population_keeps_original_and_fills_unsent_only() -> None:
    original, recovered, jobs = evidence()
    result = continue_run.join_outcomes(original, recovered, jobs)
    assert set(result) == {job.key for job in jobs}
    assert result[jobs[0].key] is original[0]
    assert result[jobs[1].key] is recovered[0]
    assert original[1]["outcome"] == "not_attempted"


@pytest.mark.parametrize(
    "defect,reason",
    [
        ("duplicate", "duplicates"),
        ("missing", "incomplete"),
        ("not_sent", "incomplete"),
        ("question", "settings"),
        ("stop", "operational"),
        ("original_reason", "financial"),
        ("membership", "population"),
        ("physical", "physical evidence"),
    ],
)
def test_rejects_specific_joint_receipt_defects(defect: str, reason: str) -> None:
    original, recovered, jobs = evidence()
    if defect == "duplicate":
        recovered.append(original[0])
    elif defect == "missing":
        recovered.pop()
    elif defect == "not_sent":
        recovered[0]["outcome"] = "not_attempted"
    elif defect == "question":
        recovered[0]["job"]["question"] = "changed"
    elif defect == "stop":
        recovered[0]["stop_reason"] = "unknown_charge"
    elif defect == "original_reason":
        original[1]["reason"] = "upstream_failure"
    elif defect == "membership":
        original[0]["job"]["scope"] = "B"
    else:
        recovered[0]["physical_calls"] = 0
    with pytest.raises(ValueError, match=reason):
        continue_run.join_outcomes(original, recovered, jobs)


def test_observed_model_failure_does_not_get_filtered_for_convenient_quality() -> None:
    original, recovered, jobs = evidence()
    original[0]["outcome"] = "invalid_answer"
    result = continue_run.join_outcomes(original, recovered, jobs)
    assert result[jobs[0].key]["outcome"] == "invalid_answer"


def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Adapter, BudgetLedger]:
    profile = load_profile(Path.cwd())
    prompt = tmp_path / profile.prompt
    prompt.parent.mkdir(parents=True)
    prompt.write_bytes((Path.cwd() / profile.prompt).read_bytes())
    _, _, jobs = evidence()
    jobs.append(
        AnswerJob(
            case_id="skip-fixture",
            arm=Arm.BM25,
            scope="A",
            question="none",
            context=[],
            retrieval_status="insufficient_evidence",
        )
    )
    config = continue_run.Continuation(
        id="P03-E03-C01",
        joint_receipt_sha256="a" * 64,
        recovery_journal_sha256="b" * 64,
        phase_allowance_usd=Decimal("3"),
        purpose="isolated unit fixture; no real ledger or model",
    )
    policy = ExecutionConfig(
        request_timeout_seconds=180.0,
        input_timeout_seconds=180.0,
        transport_retries=0,
        api_budget_usd=10.0,
        matrix_reserve_usd=3.5,
    )
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="isolated test ledger")
    entry = ledger.reserve(
        amount_usd=Decimal("1.646592"),
        stage=ExecutionStage.MATRIX,
        request_key="prior-pilot",
        pricing_evidence="test",
    )
    ledger.settle(entry.id, Decimal("0.3655965"))
    monkeypatch.setattr(
        continue_run,
        "prepare",
        lambda *args, **kwargs: (config, profile, jobs, {entry.id}, Decimal("0.3655965")),
    )
    endpoint = OpenRouterEndpoint(
        model_name=profile.model.model,
        provider_slug="google-ai-studio",
        provider_name=profile.reported_provider,
        supported_parameters=REQUIRED_OPENROUTER_PARAMETERS,
        context_length=1048576,
        max_output_tokens=65536,
        pricing={},
    )
    monkeypatch.setattr(continue_run, "metadata", lambda *args: endpoint.model_dump(mode="json"))
    monkeypatch.setattr(
        ApplicationSettings,
        "load",
        lambda *args: ApplicationSettings(openrouter_api_key=SecretStr("test-only")),
    )
    adapter = Adapter()
    monkeypatch.setattr(continue_run, "openrouter_client", lambda *args: nullcontext(None))
    monkeypatch.setattr(continue_run, "OpenRouterAdapter", lambda *args, **kwargs: adapter)
    (tmp_path / RUN_DIRECTORY).mkdir(parents=True)
    return adapter, ledger


def test_new_phase_counts_only_new_spend_and_cannot_repeat_paid_jobs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, ledger = configured(tmp_path, monkeypatch)
    result = continue_run.run(tmp_path)
    assert result["physical_calls"] == 3 and result["stop_reason"] is None
    assert Decimal(result["accounted_usd"]) == Decimal("0.03")
    assert ledger.snapshot().accounted_usd == Decimal("0.3955965")
    assert len(adapter.calls) == 3
    assert result["outcomes"] == {"structurally_valid": 3, "deterministic_non_answer": 1}
    (tmp_path / continue_run.JOURNAL).unlink()
    with pytest.raises(ValueError, match="already has paid reservations"):
        continue_run.run(tmp_path)
    assert len(adapter.calls) == 3


def test_unknown_charge_stops_calls_but_retains_all_job_outcomes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, ledger = configured(tmp_path, monkeypatch)
    adapter.cost = None
    result = continue_run.run(tmp_path)
    assert result["physical_calls"] == 1 and result["stop_reason"] == "unknown_charge"
    assert len(adapter.calls) == 1
    assert ledger.snapshot().accounted_usd == Decimal("2.0121885")
    events = [
        json.loads(line) for line in (tmp_path / continue_run.JOURNAL).read_text().splitlines()
    ]
    outcomes = [row for row in events if row["event"] == "outcome"]
    assert len(outcomes) == 4
    assert [row["outcome"] for row in outcomes] == [
        "structurally_valid",
        "not_attempted",
        "not_attempted",
        "deterministic_non_answer",
    ]


def test_real_cli_rejects_missing_concrete_paid_approval() -> None:
    result = subprocess.run(
        [sys.executable, "tools/answer-continuation/continue_run.py", "run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "separate paid/context approval" in result.stderr
    assert result.stdout == ""
