"""Source-triggered correction is single-shot and cannot alter unrelated PO fields."""

import json
from copy import deepcopy
from datetime import UTC, datetime

import pytest

from extraction_service.application.admission import request_fingerprint
from extraction_service.configuration.models import ExecutionConfig, SamplingConfig
from extraction_service.corrections.identifiers import IdentifierCorrector
from extraction_service.corrections.types import CorrectionCase, CorrectionDecision
from extraction_service.execution.admission import (
    AdmissionEvidence,
    AdmissionReason,
    AdmissionRejected,
)
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.types import (
    GenerationRequest,
    ModelIdentity,
    ModelResponse,
    ResponseKind,
)
from extraction_service.record_types import ModelRuntime

SOURCE = (
    "ORDER!B2 Delivery date: 2026-09-30\n"
    "ORDER!A10 Article code: GEN-A | B10 Description: First | C10 Quantity: 2\n"
    "ORDER!A11 Article code: GEN-B | B11 Description: Second | C11 Quantity: 3 | "
    "D11 Buyer product code: 0007-X | E11 Delivery date: 2026-09-22\n"
)
SAMPLING = SamplingConfig(id="baseline", temperature=0.0, top_p=1.0, max_output_tokens=128)
EXECUTION = ExecutionConfig(
    request_timeout_seconds=5.0,
    input_timeout_seconds=20.0,
    transport_retries=1,
    api_budget_usd=10.0,
    matrix_reserve_usd=3.5,
    dependency_failure_limit=3,
    backoff_initial_seconds=1.0,
    backoff_max_seconds=30.0,
)


class TestClock:
    __test__ = False
    value = 0.0

    def monotonic(self) -> float:
        return self.value

    def now(self) -> datetime:
        return datetime.now(UTC)

    def sleep(self, seconds: float) -> None:
        self.value += seconds


class Admission:
    def __init__(self, clock: TestClock | None = None, *, reject: bool = False) -> None:
        self.clock = clock
        self.reject = reject

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        if self.reject:
            raise AdmissionRejected(AdmissionReason.CONTEXT_CAPACITY_EXCEEDED)
        if self.clock is not None:
            self.clock.value += 21.0
        return AdmissionEvidence(
            method="unit",
            request_sha256=request_fingerprint(request, thinking=False),
            counter_identity="unit",
            prompt_token_bound=100,
            output_allowance=request.sampling.max_output_tokens,
            context_length=49152,
            thinking=False,
        )


class Adapter:
    identity = ModelIdentity(
        model_id="local",
        model_name="test-native",
        runtime=ModelRuntime.OLLAMA_NATIVE,
        runtime_version="test",
        model_digest="a" * 64,
    )

    def __init__(
        self,
        response: str | ModelTransportError,
        *,
        kind: ResponseKind = ResponseKind.COMPLETED,
        clock: TestClock | None = None,
    ) -> None:
        self.response = response
        self.kind = kind
        self.clock = clock
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> ModelResponse:
        self.requests.append(request)
        if self.clock is not None:
            self.clock.value += 21.0
        if isinstance(self.response, ModelTransportError):
            raise self.response
        return ModelResponse(
            identity=self.identity,
            kind=self.kind,
            raw_response=self.response,
            raw_http_body=json.dumps({"content": self.response}),
            reported_model="test-native",
            duration_ms=5.0,
            cost_usd=0.0,
            input_tokens=100,
            output_tokens=50,
        )


@pytest.fixture
def prior(gold: JsonObject) -> JsonObject:
    result = deepcopy(gold)
    lines = result["lineItems"]
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    first = lines[0]
    first["buyerProductName"] = "First"
    first["buyerProductIdentifier"] = "GEN-A"
    second = deepcopy(first)
    second.update(
        buyerProductName="Second", buyerProductIdentifier="0007-X", buyerDeliveryDate="2026-09-22"
    )
    lines.append(second)
    return result


def fixed(prior: JsonObject) -> JsonObject:
    result = deepcopy(prior)
    lines = result["lineItems"]
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    lines[0]["buyerProductIdentifier"] = None
    return result


def run_case(
    contract: ExtractionContract,
    prior: JsonObject,
    adapter: Adapter,
    *,
    source: str = SOURCE,
    admission: Admission | None = None,
    clock: TestClock | None = None,
) -> CorrectionCase:
    corrector = IdentifierCorrector(
        contract, adapter, Admission() if admission is None else admission, EXECUTION, clock=clock
    )
    return corrector.correct(
        source=source,
        rendered_source=source,
        prior=prior,
        instructions="Frozen v2 instructions",
        sampling=SAMPLING,
    )


def test_actual_whole_object_is_retained_only_after_target_and_edit_guards(
    contract: ExtractionContract,
    prior: JsonObject,
) -> None:
    candidate = fixed(prior)
    before = deepcopy(prior)
    adapter = Adapter(json.dumps(candidate))

    result = run_case(contract, prior, adapter)

    assert result.decision == CorrectionDecision.APPLIED
    assert len(adapter.requests) == 1 and len(result.targets) == 1
    assert result.retained == result.candidate == candidate
    assert prior == before
    assert adapter.requests[0].source_text == SOURCE
    assert adapter.requests[0].instructions.startswith("Frozen v2 instructions")
    assert "0007-X" in adapter.requests[0].instructions


@pytest.mark.parametrize("defect", ["header", "quantity", "date", "rows", "legitimate_id"])
def test_any_off_target_edit_rejects_whole_candidate_without_partial_merging(
    contract: ExtractionContract,
    prior: JsonObject,
    defect: str,
) -> None:
    candidate = fixed(prior)
    lines = candidate["lineItems"]
    assert isinstance(lines, list) and isinstance(lines[0], dict) and isinstance(lines[1], dict)
    if defect == "header":
        candidate["buyerName"] = "Changed buyer"
    elif defect == "quantity":
        lines[0]["buyerProductQuantity"] = "99"
    elif defect == "date":
        lines[1]["buyerDeliveryDate"] = "2027-01-01"
    elif defect == "rows":
        lines.append(deepcopy(lines[0]))
    else:
        lines[1]["buyerProductIdentifier"] = None
    adapter = Adapter(json.dumps(candidate))

    result = run_case(contract, prior, adapter)

    assert result.decision == CorrectionDecision.OFF_TARGET
    assert result.retained == prior and result.candidate == candidate
    assert len(adapter.requests) == 1


def test_schema_valid_unresolved_identifier_cannot_pass(
    contract: ExtractionContract,
    prior: JsonObject,
) -> None:
    adapter = Adapter(json.dumps(prior))
    result = run_case(contract, prior, adapter)

    assert result.decision == CorrectionDecision.UNRESOLVED
    assert result.retained == prior
    assert len(adapter.requests) == 1


def test_supported_identifier_values_need_no_call(
    contract: ExtractionContract, prior: JsonObject
) -> None:
    supported = fixed(prior)
    adapter = Adapter("must not be used")

    result = run_case(contract, supported, adapter)

    assert result.decision == CorrectionDecision.NOT_NEEDED
    assert result.retained == supported and adapter.requests == []


@pytest.mark.parametrize("defect", ["unknown_label", "paraphrase", "duplicate"])
def test_ambiguous_source_matching_abstains_without_model_call(
    contract: ExtractionContract,
    prior: JsonObject,
    defect: str,
) -> None:
    source = SOURCE
    value = deepcopy(prior)
    lines = value["lineItems"]
    assert isinstance(lines, list) and isinstance(lines[0], dict)
    if defect == "unknown_label":
        source += "ORDER!B3 Ownership mapping: our code is buyer-owned\n"
    elif defect == "paraphrase":
        lines[0]["buyerProductName"] = "Paraphrased name"
    else:
        lines.append(deepcopy(lines[0]))
    adapter = Adapter("must not be used")

    result = run_case(contract, value, adapter, source=source)

    assert result.decision == CorrectionDecision.ABSTAINED
    assert adapter.requests == [] and result.retained == value


@pytest.mark.parametrize(
    "kind,body",
    [
        (ResponseKind.COMPLETED, "{}"),
        (ResponseKind.TRUNCATED, "{}"),
        (ResponseKind.REFUSED, "refused"),
    ],
)
def test_invalid_incomplete_and_refused_responses_do_not_get_another_attempt(
    contract: ExtractionContract,
    prior: JsonObject,
    kind: ResponseKind,
    body: str,
) -> None:
    adapter = Adapter(body, kind=kind)
    result = run_case(contract, prior, adapter)

    assert result.decision == CorrectionDecision.INVALID
    assert result.retained == prior and len(adapter.requests) == 1


def test_retryable_transport_failure_still_has_no_retry(
    contract: ExtractionContract, prior: JsonObject
) -> None:
    error = ModelTransportError(
        FailureEvidence(
            kind=FailureKind.TIMEOUT, retryable=True, message="unit timeout", duration_ms=5.0
        )
    )
    adapter = Adapter(error)
    result = run_case(contract, prior, adapter)

    assert result.decision == CorrectionDecision.TRANSPORT_FAILED
    assert result.retained == prior and len(adapter.requests) == 1


def test_admission_rejection_and_deadline_prevent_generation(
    contract: ExtractionContract,
    prior: JsonObject,
) -> None:
    adapter = Adapter(json.dumps(fixed(prior)))
    rejected = run_case(contract, prior, adapter, admission=Admission(reject=True))
    clock = TestClock()
    expired = run_case(contract, prior, adapter, admission=Admission(clock), clock=clock)

    assert rejected.decision == expired.decision == CorrectionDecision.ADMISSION_FAILED
    assert adapter.requests == []


def test_response_after_deadline_is_preserved_but_not_applied(
    contract: ExtractionContract,
    prior: JsonObject,
) -> None:
    clock = TestClock()
    adapter = Adapter(json.dumps(fixed(prior)), clock=clock)
    result = run_case(contract, prior, adapter, clock=clock)

    assert result.decision == CorrectionDecision.INVALID
    assert result.candidate == fixed(prior) and result.retained == prior


def test_provider_or_docker_adapter_is_rejected_before_generation(
    contract: ExtractionContract,
) -> None:
    for runtime in (ModelRuntime.OPENROUTER, ModelRuntime.OLLAMA_DOCKER):
        adapter = Adapter("unused")
        adapter.identity = adapter.identity.model_copy(update={"runtime": runtime})
        with pytest.raises(ValueError, match="native-only"):
            IdentifierCorrector(contract, adapter, Admission(), EXECUTION)
        assert adapter.requests == []


@pytest.mark.parametrize("complete", [False, True])
def test_all_targets_must_resolve_including_wrong_explicit_buyer_code(
    contract: ExtractionContract,
    prior: JsonObject,
    complete: bool,
) -> None:
    original = deepcopy(prior)
    lines = original["lineItems"]
    assert isinstance(lines, list) and isinstance(lines[1], dict)
    lines[1]["buyerProductIdentifier"] = "WRONG"
    candidate = fixed(original)
    proposed = candidate["lineItems"]
    assert isinstance(proposed, list) and isinstance(proposed[1], dict)
    if complete:
        proposed[1]["buyerProductIdentifier"] = "0007-X"
    adapter = Adapter(json.dumps(candidate))

    result = run_case(contract, original, adapter)

    assert len(result.targets) == 2
    assert result.decision == (
        CorrectionDecision.APPLIED if complete else CorrectionDecision.UNRESOLVED
    )
    assert result.retained == (candidate if complete else original)


def test_checkpoint_time_is_part_of_the_deadline(
    contract: ExtractionContract, prior: JsonObject
) -> None:
    clock = TestClock()
    adapter = Adapter(json.dumps(fixed(prior)))
    corrector = IdentifierCorrector(contract, adapter, Admission(), EXECUTION, clock=clock)

    def slow_checkpoint(request: GenerationRequest) -> None:
        clock.sleep(21.0)

    result = corrector.correct(
        source=SOURCE,
        rendered_source=SOURCE,
        prior=prior,
        instructions="Frozen v2 instructions",
        sampling=SAMPLING,
        on_request=slow_checkpoint,
    )

    assert result.decision == CorrectionDecision.ADMISSION_FAILED
    assert adapter.requests == []


def test_checkpoint_observer_cannot_mutate_the_admitted_schema(
    contract: ExtractionContract, prior: JsonObject
) -> None:
    adapter = Adapter(json.dumps(fixed(prior)))
    corrector = IdentifierCorrector(contract, adapter, Admission(), EXECUTION)

    def observer(request: GenerationRequest) -> None:
        request.output_schema.clear()

    result = corrector.correct(
        source=SOURCE,
        rendered_source=SOURCE,
        prior=prior,
        instructions="Frozen v2 instructions",
        sampling=SAMPLING,
        on_request=observer,
    )

    assert result.decision == CorrectionDecision.APPLIED
    assert adapter.requests[0].output_schema == contract.schema_for_provider()
