"""Independent stage ownership, actual request shape and existing failure policy."""

import json
from collections.abc import Sequence
from contextlib import closing
from copy import deepcopy
from typing import Any

import pytest

from extraction_service.application.local import prepare_local
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.admission import AdmissionEvidence
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import (
    GenerationRequest,
    ModelIdentity,
    ModelResponse,
    ResponseKind,
)
from extraction_service.record_types import ModelRuntime, RunStatus
from extraction_service.staged.contracts import SplitStage, assemble, stage_contract
from extraction_service.staged.extractor import SplitExtractor

from .conftest import ControlledService
from .test_identifier_correction import EXECUTION, SAMPLING, Adapter, Admission, TestClock


class QueueAdapter:
    identity = Adapter.identity

    def __init__(
        self, outputs: Sequence[str | ModelTransportError], clock: TestClock | None = None
    ) -> None:
        self.outputs = list(outputs)
        self.requests: list[GenerationRequest] = []
        self.clock = TestClock() if clock is None else clock
        self.kind = ResponseKind.COMPLETED

    def generate(self, request: GenerationRequest) -> ModelResponse:
        self.requests.append(request)
        self.clock.value += 0.01
        output = self.outputs.pop(0)
        if isinstance(output, ModelTransportError):
            raise output
        return ModelResponse(
            identity=self.identity,
            kind=self.kind,
            raw_response=output,
            raw_http_body=json.dumps({"content": output}),
            reported_model=self.identity.model_name,
            finish_reason="stop",
            duration_ms=10.0,
            input_tokens=12,
            output_tokens=4,
            cost_usd=0.0,
        )


def parts(gold: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    return {k: v for k, v in gold.items() if k != "lineItems"}, {"lineItems": gold["lineItems"]}


def unit_job() -> ExtractionJob:
    return ExtractionJob(
        run_id="split-unit",
        input_id="unit-input",
        input_sha256="1" * 64,
        experiment_sha256="2" * 64,
        prompt_id="v2",
        prompt_sha256="3" * 64,
        instructions="Extract supported values only.",
        source_text="Unchanged full source context.",
        sampling=SAMPLING,
    )


def test_projections_preserve_constraints_without_mutating_parent(
    contract: ExtractionContract,
) -> None:
    original = contract.schema_for_provider()
    headers = stage_contract(contract, SplitStage.HEADERS).schema_for_provider()
    lines = stage_contract(contract, SplitStage.LINES).schema_for_provider()

    assert set(headers["required"]) == {
        "purchaseOrderNumber",
        "purchaseOrderDateTime",
        "buyerName",
        "shipToInfo",
        "paymentTerms",
        "buyerCurrency",
        "totalValue",
    }
    assert lines["required"] == ["lineItems"]
    assert lines["properties"]["lineItems"] == original["properties"]["lineItems"]
    assert (
        headers["properties"]["purchaseOrderDateTime"]
        == original["properties"]["purchaseOrderDateTime"]
    )
    assert headers["additionalProperties"] is False
    assert lines["additionalProperties"] is False
    assert contract.schema_for_provider() == original


@pytest.mark.parametrize("defect", ["date", "extra-key", "empty-lines"])
def test_projection_validation_keeps_formats_and_ownership(
    contract: ExtractionContract, gold: dict[str, Any], defect: str
) -> None:
    headers, lines = deepcopy(parts(gold))
    assert assemble(contract, headers, lines) == gold
    if defect == "date":
        headers["purchaseOrderDateTime"] = "2026-02-31"
    elif defect == "extra-key":
        headers["lineItems"] = lines["lineItems"]
    else:
        lines["lineItems"] = []

    with pytest.raises(ValueError, match="Stage output"):
        assemble(contract, headers, lines)


def test_two_independent_calls_and_disjoint_assembly(
    contract: ExtractionContract, gold: dict[str, Any]
) -> None:
    headers, lines = deepcopy(parts(gold))
    headers["buyerName"] = "GENERATED-HEADER-SENTINEL"
    clock = TestClock()
    adapter = QueueAdapter([json.dumps(headers), json.dumps(lines)], clock)
    extractor = SplitExtractor(
        contract,
        ExecutionTarget(adapter, "http://native.test/"),
        Admission(),
        EXECUTION,
        clock=clock,
    )

    result = extractor.extract(unit_job())

    assert len(adapter.requests) == 2
    assert all(r.source_text == "Unchanged full source context." for r in adapter.requests)
    assert all(
        r.instructions.startswith("Extract supported values only.") for r in adapter.requests
    )
    assert "GENERATED-HEADER-SENTINEL" not in adapter.requests[1].instructions
    assert "GENERATED-HEADER-SENTINEL" not in adapter.requests[1].source_text
    assert set(adapter.requests[0].output_schema["required"]) == set(headers)
    assert adapter.requests[1].output_schema["required"] == ["lineItems"]
    assert result.extraction == {**headers, **lines}
    assert all(r.status == RunStatus.SUCCEEDED for r in result.records.values())
    assert result.duration_ms == pytest.approx(20.0)
    assert result.extraction is not None
    result.extraction["buyerName"] = "modified"
    assert result.records[SplitStage.HEADERS].extraction == headers


@pytest.mark.parametrize("failed_stage", list(SplitStage))
def test_failed_stage_keeps_partial_evidence_but_never_emits_po(
    contract: ExtractionContract, gold: dict[str, Any], failed_stage: SplitStage
) -> None:
    headers, lines = parts(gold)
    outputs = (
        ["{}", "{}", json.dumps(lines)]
        if failed_stage == SplitStage.HEADERS
        else [json.dumps(headers), "{}", "{}"]
    )
    adapter = QueueAdapter(outputs)
    extractor = SplitExtractor(
        contract,
        ExecutionTarget(adapter, "http://native.test/"),
        Admission(),
        EXECUTION,
        clock=adapter.clock,
    )

    result = extractor.extract(unit_job())

    assert result.extraction is None
    assert len(adapter.requests) == 3
    assert result.records[failed_stage].status == RunStatus.FAILED
    assert [a.kind.value for a in result.records[failed_stage].attempts] == [
        "extraction",
        "correction",
    ]
    other = SplitStage.LINES if failed_stage == SplitStage.HEADERS else SplitStage.HEADERS
    assert result.records[other].status == RunStatus.SUCCEEDED
    assert result.records[other].extraction is not None


def test_shared_dependency_stop_applies_across_stages_and_inputs(
    contract: ExtractionContract,
) -> None:
    failure = ModelTransportError(
        FailureEvidence(
            kind=FailureKind.SERVER_ERROR,
            retryable=True,
            duration_ms=10.0,
            message="unit server unavailable",
        )
    )
    adapter = QueueAdapter([failure])
    policy = EXECUTION.model_copy(update={"transport_retries": 0, "dependency_failure_limit": 1})
    extractor = SplitExtractor(
        contract,
        ExecutionTarget(adapter, "http://native.test/"),
        Admission(),
        policy,
        clock=adapter.clock,
    )

    first = extractor.extract(unit_job())
    second = extractor.extract(unit_job().model_copy(update={"input_id": "second-input"}))

    assert len(adapter.requests) == 1
    assert first.records[SplitStage.HEADERS].status == RunStatus.FAILED
    assert first.records[SplitStage.LINES].status == RunStatus.NOT_ATTEMPTED
    assert all(r.status == RunStatus.NOT_ATTEMPTED for r in second.records.values())
    assert first.extraction is second.extraction is None


def test_line_admission_cannot_reuse_header_certificate(
    contract: ExtractionContract, gold: dict[str, Any]
) -> None:
    headers, _ = parts(gold)

    class RejectLines(Admission):
        def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
            return Admission(reject=request.output_schema["required"] == ["lineItems"]).check(
                request, identity
            )

    adapter = QueueAdapter([json.dumps(headers)])
    extractor = SplitExtractor(
        contract,
        ExecutionTarget(adapter, "http://native.test/"),
        RejectLines(),
        EXECUTION,
        clock=adapter.clock,
    )

    result = extractor.extract(unit_job())

    assert len(adapter.requests) == 1
    assert result.records[SplitStage.HEADERS].status == RunStatus.SUCCEEDED
    assert result.records[SplitStage.LINES].attempts == []
    assert result.records[SplitStage.LINES].reason == "context_capacity_exceeded"
    assert result.extraction is None


def test_actual_http_receives_projected_formats_and_independent_full_sources(
    service: ControlledService,
    contract: ExtractionContract,
    gold: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service.native = True
    for key, value in service.environment().items():
        if key.startswith("DI_"):
            monkeypatch.setenv(key, value)
    headers, lines = parts(gold)
    service.responses = [json.dumps(headers), json.dumps(lines)]
    experiment = load_experiment(service.project / "config/gemma-scoped-roles.yaml")
    with closing(JsonHttpClient(service.base_url)) as client:
        target, admission, _ = prepare_local(
            service.project, experiment.models[0], ApplicationSettings.load(service.project), client
        )
        extractor = SplitExtractor(contract, target, admission, EXECUTION)
        result = extractor.extract(unit_job())

    assert result.extraction == gold
    requests = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(requests) == 4
    assert requests[0] is not None and requests[1] is not None
    assert requests[2] is not None and requests[3] is not None
    assert requests[0]["_debug_render_only"] is True
    assert requests[2]["_debug_render_only"] is True
    assert requests[0]["messages"] == requests[1]["messages"]
    assert requests[2]["messages"] == requests[3]["messages"]
    assert set(requests[1]["format"]["required"]) == set(headers)
    assert requests[3]["format"]["required"] == ["lineItems"]
    assert requests[1]["messages"][1] == requests[3]["messages"][1]


@pytest.mark.parametrize("runtime", [ModelRuntime.OPENROUTER, ModelRuntime.OLLAMA_DOCKER])
def test_split_rejects_paid_and_docker_adapters(
    contract: ExtractionContract, runtime: ModelRuntime
) -> None:
    adapter = QueueAdapter([])
    adapter.identity = ModelIdentity(
        model_id="other",
        model_name="other",
        runtime=runtime,
        serving_provider="provider" if runtime == ModelRuntime.OPENROUTER else None,
    )
    with pytest.raises(ValueError, match="native Ollama"):
        SplitExtractor(
            contract, ExecutionTarget(adapter, "http://native.test/"), Admission(), EXECUTION
        )
