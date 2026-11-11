"""Isolated financial-recovery controls; no real model or production ledger."""

import json
from contextlib import nullcontext
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
import recover
from pydantic import SecretStr

from extraction_service.answering.cli import RUN_DIRECTORY
from extraction_service.answering.contract import AnswerJob, Arm
from extraction_service.answering.protocol import load_profile
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.inference.openrouter.capabilities import (
    REQUIRED_OPENROUTER_PARAMETERS,
    OpenRouterEndpoint,
)
from extraction_service.inference.types import (
    GenerationRequest,
    ModelIdentity,
    ModelResponse,
    ResponseKind,
)
from extraction_service.record_types import ExecutionStage, ModelRuntime


def jobs() -> list[AnswerJob]:
    return [
        AnswerJob(
            case_id="Q38",
            arm=arm,
            scope="A",
            question="dispatch marker",
            context=[],
            retrieval_status="evidence_found",
        )
        for arm in (Arm.NONE, Arm.BM25, Arm.VECTOR)
    ]


def parent() -> tuple[list[dict[str, Any]], list[AnswerJob]]:
    selected = jobs()
    # Nonempty eligible context for the two recovery jobs; raw values are synthetic.
    from extraction_service.answering.contract import Context

    context = Context(source_id="one", revision="1", sha256="a" * 64, start=0, end=3, quote="one")
    selected = [
        selected[0],
        *(job.model_copy(update={"context": [context]}) for job in selected[1:]),
    ]
    rows: list[dict[str, Any]] = [
        dict(event="start", jobs=[j.model_dump(mode="json") for j in selected]),
        dict(event="reserved", key=selected[0].key, reservation={"id": "original"}),
        dict(event="physical_result", key=selected[0].key, reservation_id="original"),
    ]
    rows.append(
        dict(
            event="outcome",
            job=selected[0].model_dump(mode="json"),
            physical_calls=1,
            outcome="structurally_valid",
        )
    )
    for job in selected[1:]:
        rows.append(
            dict(
                event="outcome",
                job=job.model_dump(mode="json"),
                physical_calls=0,
                outcome="not_attempted",
                reason="phase_allowance_insufficient",
            )
        )
    rows.append(
        dict(
            event="complete",
            physical_calls=1,
            accounted_usd="0.354399",
            stop_reason="phase_allowance_insufficient",
        )
    )
    return rows, selected


def test_selects_only_the_unsent_tail_in_original_order() -> None:
    events, selected = parent()
    tail, cost, ids = recover.parent_tail(events, selected, ["Q38/bm25", "Q38/vector"])
    assert tail == selected[1:]
    assert cost == Decimal("0.354399") and ids == {"original"}


@pytest.mark.parametrize(
    "defect", ["unknown", "partial", "membership", "sent", "wrong_tail", "accounting"]
)
def test_parent_corruption_never_schedules_a_recovery(defect: str) -> None:
    events, selected = parent()
    expected = ["Q38/bm25", "Q38/vector"]
    if defect == "unknown":
        events[-1]["stop_reason"] = "unknown_charge"
    elif defect == "partial":
        events.pop()
    elif defect == "membership":
        events[4]["job"]["question"] = "different"
    elif defect == "sent":
        events[1]["key"] = "Q38/bm25"
    elif defect == "wrong_tail":
        expected.reverse()
    else:
        events[-1]["physical_calls"] = 2
    with pytest.raises(ValueError):
        recover.parent_tail(events, selected, expected)


class Adapter:
    def __init__(self) -> None:
        self.calls: list[GenerationRequest] = []
        self.cost: float | None = 0.01

    @property
    def identity(self) -> ModelIdentity:
        return ModelIdentity(
            model_id="e03-flash",
            model_name="google/gemini-3.5-flash",
            runtime=ModelRuntime.OPENROUTER,
            serving_provider="google-ai-studio",
        )

    def generate(self, request: GenerationRequest) -> ModelResponse:
        self.calls.append(request)
        return ModelResponse(
            identity=self.identity,
            kind=ResponseKind.COMPLETED,
            reported_model=self.identity.model_name,
            serving_provider="Google AI Studio",
            raw_response='{"status":"insufficient_evidence","answer":null,"claims":[]}',
            raw_http_body="original response bytes",
            duration_ms=1.0,
            cost_usd=self.cost,
        )


def configured(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Adapter, BudgetLedger]:
    profile = load_profile(Path.cwd())
    prompt = tmp_path / profile.prompt
    prompt.parent.mkdir(parents=True)
    prompt.write_bytes((Path.cwd() / profile.prompt).read_bytes())
    _, selected = parent()
    recovery = recover.Recovery(
        id="P03-E03-R01",
        parent_manifest_sha256="a" * 64,
        parent_journal_sha256="b" * 64,
        tail_keys=[j.key for j in selected[1:]],
        total_pilot_exposure_usd=Decimal("2.10"),
        purpose="isolated test",
    )
    policy = ExecutionConfig(
        request_timeout_seconds=180.0,
        input_timeout_seconds=180.0,
        transport_retries=0,
        api_budget_usd=10.0,
        matrix_reserve_usd=3.5,
    )
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="isolated test only")
    reservation = ledger.reserve(
        amount_usd=Decimal("1.646592"),
        stage=ExecutionStage.MATRIX,
        request_key="original",
        pricing_evidence="test",
    )
    ledger.settle(reservation.id, Decimal("0.354399"))
    monkeypatch.setattr(
        recover,
        "prepare",
        lambda *args, **kwargs: (
            recovery,
            profile,
            selected[1:],
            Decimal("0.354399"),
            {reservation.id},
        ),
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
    monkeypatch.setattr(recover, "metadata", lambda *args: endpoint.model_dump(mode="json"))
    monkeypatch.setattr(
        ApplicationSettings,
        "load",
        lambda *args: ApplicationSettings(openrouter_api_key=SecretStr("isolated-test-only")),
    )
    adapter = Adapter()
    monkeypatch.setattr(recover, "openrouter_client", lambda *args: nullcontext(None))
    monkeypatch.setattr(recover, "OpenRouterAdapter", lambda *args, **kwargs: adapter)
    (tmp_path / RUN_DIRECTORY).mkdir(parents=True)
    return adapter, ledger


def test_recovery_counts_original_cost_and_does_not_repeat_original_request(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, ledger = configured(tmp_path, monkeypatch)
    result = recover.run(tmp_path)
    assert result["physical_calls"] == 2 and result["stop_reason"] is None
    assert result["recovery_cost_usd"] == "0.020000"
    assert Decimal(result["total_pilot_cost_usd"]) == Decimal("0.374399")
    assert len(adapter.calls) == 2
    assert ledger.snapshot().accounted_usd == Decimal("0.374399")
    assert len(ledger.snapshot().reservations) == 3
    # Removing the output cannot make already charged jobs runnable again.
    (tmp_path / recover.JOURNAL).unlink()
    with pytest.raises(ValueError, match="already has paid reservations"):
        recover.run(tmp_path)
    assert len(adapter.calls) == 2


def test_unknown_recovery_charge_retains_hold_and_does_not_send_second_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter, ledger = configured(tmp_path, monkeypatch)
    adapter.cost = None
    result = recover.run(tmp_path)
    assert result["physical_calls"] == 1 and result["stop_reason"] == "unknown_charge"
    assert len(adapter.calls) == 1 and ledger.snapshot().accounted_usd == Decimal("2.000991")
    events = [json.loads(line) for line in (tmp_path / recover.JOURNAL).read_text().splitlines()]
    outcomes = [row for row in events if row["event"] == "outcome"]
    assert outcomes[1]["outcome"] == "not_attempted"


def test_cli_requires_new_concrete_paid_approval(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["recover", "run", "--allow-provider"])
    with pytest.raises(SystemExit) as error:
        recover.main()
    assert error.value.code == 2 and "separate paid/context approval" in capsys.readouterr().err
