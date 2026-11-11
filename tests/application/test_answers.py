"""Answer-boundary, one-call accounting and phase controls without live inference."""

import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import pytest

from extraction_service.answering.cli import export_phase, main, verify_pilot
from extraction_service.answering.contract import (
    AnswerJob,
    AnswerStatus,
    Arm,
    Context,
    validate_answer,
)
from extraction_service.answering.execution import AnswerRunner, Journal, Outcome
from extraction_service.answering.protocol import (
    INHERITED,
    build_jobs,
    freeze,
    load_profile,
    select_phase,
    verified_jobs,
)
from extraction_service.application.admission import ProviderAdmission
from extraction_service.application.composition import PreparedTarget
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop, BudgetStopReason
from extraction_service.execution.types import ExecutionTarget
from extraction_service.inference.errors import (
    FailureEvidence,
    FailureKind,
    ModelConfigurationError,
    ModelTransportError,
)
from extraction_service.inference.openrouter.adapter import OpenRouterAdapter
from extraction_service.inference.openrouter.capabilities import (
    REQUIRED_OPENROUTER_PARAMETERS,
    OpenRouterEndpoint,
)
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import (
    GenerationRequest,
    ModelIdentity,
    ModelResponse,
    ResponseKind,
)
from extraction_service.record_types import ExecutionStage, ModelRuntime
from extraction_service.retrieval.core import canonical, digest

ROOT = Path.cwd()


def job(arm: Arm = Arm.NONE) -> AnswerJob:
    context = Context(source_id="rule", revision="1", sha256="a" * 64, start=0, end=3, quote="one")
    return AnswerJob(
        case_id="Q01",
        arm=arm,
        scope="A",
        question="Explain a field",
        context=[] if arm == Arm.NONE else [context],
        retrieval_status="evidence_found",
    )


def reply(job: AnswerJob, *, status: str = "unverified") -> str:
    citations = [] if status != "grounded" else [job.context[0].model_dump(exclude={"quote"})]
    return json.dumps(
        dict(
            status=status,
            answer="An explanation",
            claims=[dict(text="An explanation", citations=citations)],
        )
    )


class FakeClock:
    def __init__(self) -> None:
        self.ticks = 0.0

    def monotonic(self) -> float:
        return self.ticks

    def now(self) -> datetime:
        return datetime(2026, 11, 10, tzinfo=UTC)

    def sleep(self, seconds: float) -> None:
        self.ticks += seconds


class FakeAdapter:
    def __init__(self) -> None:
        self.calls: list[GenerationRequest] = []
        self.cost: float | None = 0.01
        self.kind = ResponseKind.COMPLETED
        self.raw = reply(job())
        self.error: Exception | None = None
        self.provider = "Google AI Studio"
        self.on_call: Any = None

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
        if self.on_call is not None:
            self.on_call()
        if self.error is not None:
            raise self.error
        return ModelResponse(
            identity=self.identity,
            reported_model=self.identity.model_name,
            serving_provider=self.provider,
            kind=self.kind,
            raw_response=self.raw,
            raw_http_body="EXACT_HTTP_BYTES",
            duration_ms=12.5,
            input_tokens=20,
            output_tokens=10,
            cost_usd=self.cost,
        )


def runner(
    tmp_path: Path,
    adapter: FakeAdapter,
    clock: FakeClock | None = None,
    allowance: Decimal = Decimal("2"),
) -> AnswerRunner:
    profile = load_profile(ROOT)
    policy = ExecutionConfig(
        request_timeout_seconds=180.0,
        input_timeout_seconds=180.0,
        transport_retries=0,
        api_budget_usd=10.0,
        matrix_reserve_usd=3.5,
    )
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="isolated test ledger")
    target = ExecutionTarget(adapter=adapter, endpoint="https://openrouter.ai/api/v1/")
    return AnswerRunner(
        prepared=PreparedTarget(
            target=target,
            admission=ProviderAdmission(profile.coverage),
            pricing=profile.coverage.pricing,
        ),
        ledger=ledger,
        journal=Journal(tmp_path / "phase.jsonl"),
        clock=clock or FakeClock(),
        allowance=allowance,
        deadline_seconds=180.0,
        reported_provider=profile.reported_provider,
    )


def run(value: AnswerRunner, item: AnswerJob | None = None) -> dict[str, Any]:
    profile = load_profile(ROOT)
    return value.run(
        item or job(),
        instructions="Fixed instructions",
        sampling=profile.sampling,
        timeout=180.0,
        request_key="test/Q01/none",
        revalidate=lambda: None,
    )


def test_no_context_can_answer_without_fabricated_grounding() -> None:
    item = job()
    answer = validate_answer(reply(item), item)
    assert answer.status == AnswerStatus.UNVERIFIED
    profile = load_profile(ROOT)
    request = item.request("fixed", profile.sampling, 30.0)
    assert json.loads(request.source_text) == dict(question=item.question, evidence=[])
    assert "cases" not in request.source_text
    assert "scope" not in request.source_text


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_id", "not-supplied"),
        ("revision", "2"),
        ("sha256", "b" * 64),
        ("start", 1),
        ("end", 4),
    ],
)
def test_citation_checks_each_identity_coordinate(field: str, value: object) -> None:
    item = job(Arm.BM25)
    raw = reply(item, status="grounded")
    assert validate_answer(raw, item).status == AnswerStatus.GROUNDED
    forged = json.loads(raw)
    forged["claims"][0]["citations"][0][field] = value
    with pytest.raises(ValueError, match="not supplied"):
        validate_answer(json.dumps(forged), item)


@pytest.mark.parametrize(
    "raw",
    [
        '{"status":"unverified","status":"grounded","answer":null,"claims":[]}',
        '{"status":"unverified","answer":null,"claims":[]}',
        '{"status":"grounded","answer":"x","claims":[{"text":"x","citations":[]}]}',
        '{"status":"insufficient_evidence","answer":"x","claims":[]}',
        '{"status":"unverified","answer":"x","claims":[],"extra":1}',
        "```json\n{}\n```",
    ],
)
def test_invalid_outputs_are_never_repaired(raw: str) -> None:
    with pytest.raises(ValueError):
        validate_answer(raw, job())


def test_byte_valid_citation_is_not_semantic_scoring() -> None:
    item = job(Arm.VECTOR)
    raw = reply(item, status="grounded").replace("An explanation", "A false claim")
    # Deliberately false prose still passes the *mechanical* check. S08 must review it.
    answer = validate_answer(raw, item)
    assert answer.claims[0].text == "A false claim"


@pytest.mark.parametrize("reason", ["insufficient_evidence", "conflicting_evidence"])
def test_deterministic_non_answers_do_not_admit_reserve_or_generate(
    tmp_path: Path, reason: str
) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)
    item = job(Arm.BM25).model_copy(
        update={
            "retrieval_status": reason,
            "context": [] if reason == "insufficient_evidence" else job(Arm.BM25).context,
        }
    )
    result = run(value, item)
    assert result["outcome"] == Outcome.SKIPPED
    assert result["reason"] == reason
    assert adapter.calls == []
    assert value.ledger.snapshot().reservations == []


def test_durable_reservation_precedes_send_and_raw_precedes_settlement(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)

    def check_at_send() -> None:
        entries = value.ledger.snapshot().reservations
        assert len(entries) == 1 and entries[0].resolved is False
        events = [json.loads(line) for line in value.journal.path.read_text().splitlines()]
        assert events[-1]["event"] == "reserved"
        assert events[-1]["admission"]["prompt_token_bound"] is None

    adapter.on_call = check_at_send
    result = run(value)
    assert result["outcome"] == Outcome.VALID
    assert result["response"]["raw_http_body"] == "EXACT_HTTP_BYTES"
    assert result["semantic_review"] == "unreviewed"
    assert len(adapter.calls) == 1
    entry = value.ledger.snapshot().reservations[0]
    assert entry.billed_usd == Decimal("0.01") and entry.resolved
    events = [json.loads(line) for line in value.journal.path.read_text().splitlines()]
    assert [row["event"] for row in events] == ["reserved", "physical_result", "outcome"]


@pytest.mark.parametrize("kind", list(ResponseKind))
def test_all_response_kinds_remain_one_physical_observation(
    tmp_path: Path, kind: ResponseKind
) -> None:
    adapter = FakeAdapter()
    adapter.kind = kind
    value = runner(tmp_path, adapter)
    result = run(value)
    assert result["physical_calls"] == 1
    assert len(adapter.calls) == 1
    assert result["response"]["kind"] == kind.value
    assert result["outcome"] == (
        Outcome.VALID if kind == ResponseKind.COMPLETED else Outcome.RESPONSE_FAILURE
    )


@pytest.mark.parametrize("cost,stop", [(None, "unknown_charge"), (2.0, "unsafe_pricing")])
def test_unknown_or_excess_charge_stops_and_preserves_accounting(
    tmp_path: Path, cost: float | None, stop: str
) -> None:
    adapter = FakeAdapter()
    adapter.cost = cost
    value = runner(tmp_path, adapter, allowance=Decimal("5"))
    first = run(value)
    second = run(value)
    assert first["stop_reason"] == stop
    assert second["outcome"] == Outcome.NOT_ATTEMPTED
    assert len(adapter.calls) == 1
    assert value.ledger.snapshot().accounted_usd == (
        Decimal("1.646592") if cost is None else Decimal("2")
    )


def test_no_retry_after_transport_failure_and_unknown_hold(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.error = ModelTransportError(
        FailureEvidence(
            kind=FailureKind.RATE_LIMIT,
            retryable=True,
            message="429 fixture",
            duration_ms=1.0,
            status_code=429,
        )
    )
    value = runner(tmp_path, adapter)
    result = run(value)
    assert result["failure"]["status_code"] == 429
    assert result["outcome"] == Outcome.TRANSPORT_FAILURE
    assert value.stop_reason == "unknown_charge"
    assert len(adapter.calls) == 1


def test_unsent_configuration_error_settles_zero(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.error = ModelConfigurationError("before I/O")
    value = runner(tmp_path, adapter)
    result = run(value)
    assert result["physical_calls"] == 0 and value.physical_calls == 0
    assert value.ledger.snapshot().accounted_usd == Decimal("0")


def test_programming_error_leaves_unresolved_reservation_and_no_completion(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.error = RuntimeError("unexpected")
    value = runner(tmp_path, adapter)
    with pytest.raises(RuntimeError, match="unexpected"):
        run(value)
    reservation = value.ledger.snapshot().reservations[0]
    assert not reservation.resolved
    assert reservation.accounted_usd == Decimal("1.646592")


def test_phase_allowance_and_deadline_block_without_spend(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    clock = FakeClock()
    value = runner(tmp_path, adapter, clock, allowance=Decimal("1"))
    assert run(value)["reason"] == "phase_allowance_insufficient"
    assert adapter.calls == [] and value.ledger.snapshot().reservations == []
    value.stop_reason = None
    clock.ticks = 181.0
    assert run(value)["reason"] == "phase_deadline"
    assert adapter.calls == []


def test_wrong_reported_route_stops_without_discarding_bill(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    adapter.provider = "different route"
    value = runner(tmp_path, adapter)
    result = run(value)
    assert result["reason"] == "response_identity_mismatch"
    assert value.ledger.snapshot().accounted_usd == Decimal("0.01")


def test_phase_file_cannot_be_overwritten(tmp_path: Path) -> None:
    path = tmp_path / "pilot.jsonl"
    Journal(path).append({"original": True})
    with pytest.raises(FileExistsError):
        Journal(path)
    assert json.loads(path.read_text()) == {"original": True}


def test_fixed_matched_population_and_no_label_leak(monkeypatch: pytest.MonkeyPatch) -> None:
    # Isolated planning fixture; real saved Qdrant contexts are checked by answer-plan.
    cases = json.loads((ROOT / "config/evaluation/P03-cases-v1.json").read_text())["cases"]
    contexts = {case["id"]: dict(status="insufficient_evidence", hits=[]) for case in cases}
    monkeypatch.setattr("extraction_service.answering.protocol._saved_contexts", lambda _: contexts)
    profile = load_profile(ROOT)
    jobs = build_jobs(ROOT, profile)
    pilot = select_phase(jobs, profile, "pilot")
    remaining = select_phase(jobs, profile, "remaining")
    assert len(jobs) == 120 and len(pilot) == 36 and len(remaining) == 84
    assert {j.key for j in pilot}.isdisjoint(j.key for j in remaining)
    for item in jobs:
        if item.skip_reason is None:
            request = item.request("same fixed prompt", profile.sampling, 180.0)
            assert set(json.loads(request.source_text)) == {"question", "evidence"}
            assert request.instructions == "same fixed prompt"
            assert request.sampling == profile.sampling


def test_partial_pilot_cannot_unlock_continuation(tmp_path: Path) -> None:
    directory = tmp_path / "results/answer-runs/P03-E03-v1"
    directory.mkdir(parents=True)
    raw = canonical(dict(event="start", manifest="frozen", phase="pilot")) + b"\n"
    (directory / "pilot.jsonl").write_bytes(raw)
    with pytest.raises(ValueError, match="blocks continuation"):
        verify_pilot(tmp_path, [job()], digest(raw), "frozen")


def test_cli_refuses_live_without_both_approval_flags(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["answers", "run", "--allow-provider"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "separately approved" in capsys.readouterr().err


def test_response_is_durable_before_settlement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)
    settle = value.ledger.settle

    def checked_settle(identity: str, amount: Decimal | None) -> None:
        events = [json.loads(line) for line in value.journal.path.read_text().splitlines()]
        assert events[-1]["event"] == "physical_result"
        assert events[-1]["response"]["raw_http_body"] == "EXACT_HTTP_BYTES"
        settle(identity, amount)

    monkeypatch.setattr(value.ledger, "settle", checked_settle)
    assert run(value)["physical_calls"] == 1


def test_settlement_failure_is_not_reported_as_unsent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)

    def fail_settle(identity: str, amount: Decimal | None) -> None:
        raise BudgetStop(BudgetStopReason.UNAVAILABLE)

    monkeypatch.setattr(value.ledger, "settle", fail_settle)
    with pytest.raises(BudgetStop):
        run(value)
    assert len(adapter.calls) == 1
    assert not value.ledger.snapshot().reservations[0].resolved
    events = [json.loads(line) for line in value.journal.path.read_text().splitlines()]
    assert events[-1]["event"] == "physical_result"
    assert not any(row["event"] == "outcome" for row in events)


def test_cumulative_budget_stop_is_not_a_generation_failure(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)
    value.ledger.reserve(
        amount_usd=Decimal("9"),
        stage=ExecutionStage.MATRIX,
        request_key="prior-unknown",
        pricing_evidence="prior hold",
    )
    result = run(value)
    assert result["reason"] == "budget_insufficient"
    assert adapter.calls == []
    assert value.ledger.snapshot().accounted_usd == Decimal("9")


def test_changed_authority_stops_before_reservation(tmp_path: Path) -> None:
    adapter = FakeAdapter()
    value = runner(tmp_path, adapter)
    profile = load_profile(ROOT)

    def fail_integrity() -> None:
        raise ValueError("changed reference bytes")

    with pytest.raises(ValueError, match="changed reference"):
        value.run(
            job(),
            instructions="fixed",
            sampling=profile.sampling,
            timeout=180.0,
            request_key="no-send",
            revalidate=fail_integrity,
        )
    assert adapter.calls == []
    assert value.ledger.snapshot().reservations == []


@pytest.mark.parametrize("defect", ["hash", "membership", "physical", "stop"])
def test_completed_pilot_positive_and_specific_corruption(tmp_path: Path, defect: str) -> None:
    directory = tmp_path / "results/answer-runs/P03-E03-v1"
    directory.mkdir(parents=True)
    item = job()
    events: list[dict[str, Any]] = [
        dict(event="start", phase="pilot", manifest="frozen", jobs=[item.model_dump(mode="json")]),
        dict(event="reserved", reservation={"id": "one"}),
        dict(event="physical_result", reservation_id="one"),
        dict(
            event="outcome",
            job=item.model_dump(mode="json"),
            outcome="structurally_valid",
            physical_calls=1,
            stop_reason=None,
        ),
        dict(event="complete", stop_reason=None, physical_calls=1),
    ]
    path = directory / "pilot.jsonl"
    raw = b"\n".join(canonical(row) for row in events) + b"\n"
    path.write_bytes(raw)
    assert verify_pilot(tmp_path, [item], digest(raw), "frozen") == {"one"}
    if defect == "membership":
        events[3]["job"]["case_id"] = "Q02"
    elif defect == "physical":
        events[2]["reservation_id"] = "different"
    elif defect == "stop":
        events[3]["stop_reason"] = "unknown_charge"
    changed = b"\n".join(canonical(row) for row in events) + b"\n"
    path.write_bytes(changed)
    expected_hash = "0" * 64 if defect == "hash" else digest(changed)
    with pytest.raises(ValueError, match="receipt hash|membership|accounting"):
        verify_pilot(tmp_path, [item], expected_hash, "frozen")


def test_ineligible_reference_rejected_before_request(monkeypatch: pytest.MonkeyPatch) -> None:
    cases = json.loads((ROOT / "config/evaluation/P03-cases-v1.json").read_text())["cases"]
    contexts: dict[str, Any] = {
        case["id"]: dict(status="insufficient_evidence", hits=[]) for case in cases
    }
    contexts["Q01"] = dict(
        status="evidence_found", hits=[job(Arm.BM25).context[0].model_dump() | {"score": 1.0}]
    )
    monkeypatch.setattr("extraction_service.answering.protocol._saved_contexts", lambda _: contexts)
    with pytest.raises(ValueError, match="Ineligible or modified"):
        build_jobs(ROOT, load_profile(ROOT))


def test_freeze_positive_then_changed_prompt_and_new_source_rejected(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No real retrieval/model observation: this fixture isolates frozen-byte guards.
    for directory in ("src", "config", "data", "schemas", "prompts", "docs/reference"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    # A checkout may already contain the real frozen protocol. This disposable
    # fixture must create its own identity rather than overwrite the real one.
    (tmp_path / "config/retrieval/P03-E03-v1.json").unlink(missing_ok=True)
    for filename in ("pyproject.toml", "uv.lock"):
        shutil.copyfile(ROOT / filename, tmp_path / filename)
    for filename in ("Dockerfile", "compose.e03.yaml"):
        (tmp_path / filename).write_text("isolated runtime fixture")
    inherited = tmp_path / INHERITED
    inherited.parent.mkdir(parents=True)
    inherited.write_text("isolated saved context fixture")
    cases = json.loads((ROOT / "config/evaluation/P03-cases-v1.json").read_text())["cases"]
    contexts = {case["id"]: dict(status="insufficient_evidence", hits=[]) for case in cases}
    monkeypatch.setattr("extraction_service.answering.protocol._saved_contexts", lambda _: contexts)
    frozen = freeze(tmp_path)
    profile, jobs, manifest = verified_jobs(tmp_path)
    assert frozen["id"] == profile.id and len(jobs) == 120 and len(manifest) == 64
    with pytest.raises(FileExistsError):
        freeze(tmp_path)
    prompt = tmp_path / profile.prompt
    original = prompt.read_bytes()
    prompt.write_bytes(original + b"changed")
    with pytest.raises(ValueError, match="bindings changed"):
        verified_jobs(tmp_path)
    prompt.write_bytes(original)
    (tmp_path / "src/extraction_service/answering/new_code.py").write_text("# extra code")
    with pytest.raises(ValueError, match="bindings changed"):
        verified_jobs(tmp_path)


def test_export_preserves_exact_journal_and_refuses_changed_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = load_profile(ROOT)
    monkeypatch.setattr(
        "extraction_service.answering.cli.verified_jobs", lambda _: (profile, [job()], "frozen")
    )
    directory = tmp_path / "results/answer-runs/P03-E03-v1"
    directory.mkdir(parents=True)
    raw = b'{"event":"start", "manifest":"frozen"}\n{"event":"complete"}\n'
    (directory / "pilot.jsonl").write_bytes(raw)
    destination = tmp_path / "export"
    destination.mkdir()
    receipt = export_phase(tmp_path, "pilot", destination)
    assert receipt["journal_sha256"] == digest(raw)
    assert receipt["generation_calls"] == 0
    assert (destination / "pilot.jsonl").read_bytes() == raw
    assert export_phase(tmp_path, "pilot", destination) == receipt
    (destination / "pilot.jsonl").write_bytes(b"different")
    with pytest.raises(ValueError, match="refusing overwrite"):
        export_phase(tmp_path, "pilot", destination)


def test_real_cli_process_rejects_unapproved_inference() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "extraction_service.answering.cli", "run"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2
    assert "separately approved" in result.stderr
    assert result.stdout == ""


def test_real_adapter_sends_answer_schema_and_preserves_matched_controls() -> None:
    profile = load_profile(ROOT)
    captured: list[dict[str, Any]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/chat/completions"
        captured.append(json.loads(request.content))
        return httpx.Response(
            200,
            json=dict(
                model=profile.model.model,
                provider=profile.reported_provider,
                choices=[
                    dict(finish_reason="stop", message=dict(role="assistant", content=reply(job())))
                ],
                usage=dict(prompt_tokens=20, completion_tokens=10, cost=0.01),
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
    client = JsonHttpClient("https://openrouter.ai/api/v1/", transport=httpx.MockTransport(respond))
    try:
        adapter = OpenRouterAdapter(
            profile.model, endpoint, http_client=client, server_context=True
        )
        for arm in Arm:
            item = job(arm)
            request = item.request("same instructions", profile.sampling, 30.0)
            response = adapter.generate(request)
            assert response.kind == ResponseKind.COMPLETED
            payload = captured[-1]
            assert payload["response_format"]["json_schema"]["schema"] == request.output_schema
            assert "claims" in payload["response_format"]["json_schema"]["schema"]["properties"]
            assert payload["max_tokens"] == 8192
            assert payload["temperature"] == 0.0 and payload["top_p"] == 1.0
            assert "reasoning" not in payload
            assert payload["provider"] == dict(
                only=["google-ai-studio"], allow_fallbacks=False, require_parameters=True
            )
            assert payload["plugins"] == [dict(id="context-compression", enabled=False)]
        # With identical supplied contexts BM25/vector differ only in local bookkeeping.
        assert captured[1] == captured[2]
        assert len(captured) == 3
    finally:
        client.close()
