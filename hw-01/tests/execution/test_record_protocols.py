"""Check enum boundaries, legacy JSON records and explicit evidence comparisons."""

import json

import pytest
from pydantic import ValidationError

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.evidence import AttemptContext, response_attempt
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.types import ModelIdentity, ResponseKind
from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime, RunStatus
from extraction_service.records import AttemptResult, RunRecord

from .helpers import FakeClock, ScriptedAdapter, response


@pytest.fixture
def successful_record(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    local_identity: ModelIdentity,
    clock: FakeClock,
) -> RunRecord:
    adapter = ScriptedAdapter(local_identity, clock, [response(local_identity, json.dumps(gold))])
    coordinator = ExtractionCoordinator(contract, policy, clock=clock)

    return coordinator.execute(
        ScheduledExtraction(job, ExecutionTarget(adapter, "http://ollama:11434"))
    )


def test_record_enums_preserve_existing_serialized_values_and_restore_members(
    successful_record: RunRecord, contract: ExtractionContract
) -> None:
    serialized = successful_record.model_dump_json()
    payload = json.loads(serialized)
    restored = RunRecord.model_validate_json(serialized, context={"contract": contract})

    assert payload["runtime"] == "ollama-docker"
    assert payload["status"] == "succeeded"
    assert payload["attempts"][0]["kind"] == "extraction"
    assert payload["attempts"][0]["outcome"] == "valid"
    assert restored.runtime is ModelRuntime.OLLAMA_DOCKER
    assert restored.status is RunStatus.SUCCEEDED
    assert restored.attempts[0].kind is AttemptKind.EXTRACTION
    assert restored.attempts[0].outcome is AttemptOutcome.VALID
    assert restored == successful_record


def test_legacy_json_without_new_operational_fields_still_loads(
    successful_record: RunRecord, contract: ExtractionContract
) -> None:
    payload = json.loads(successful_record.model_dump_json())
    payload.pop("stage")
    payload.pop("dependency")
    attempt = payload["attempts"][0]

    for field in (
        "response",
        "failure",
        "request_timeout_seconds",
        "retry_delay_seconds",
        "budget_reservation_id",
        "budget_reserved_usd",
        "accounting_note",
    ):
        attempt.pop(field)

    restored = RunRecord.model_validate_json(json.dumps(payload), context={"contract": contract})

    assert restored.status is RunStatus.SUCCEEDED
    assert restored.runtime is ModelRuntime.OLLAMA_DOCKER
    assert restored.attempts[0].kind is AttemptKind.EXTRACTION
    assert restored.attempts[0].outcome is AttemptOutcome.VALID
    assert restored.extraction == successful_record.extraction
    assert restored.attempts[0].response is None


@pytest.mark.parametrize("field", ["runtime", "status"])
def test_strict_python_record_construction_requires_enum_members(
    successful_record: RunRecord, contract: ExtractionContract, field: str
) -> None:
    values = successful_record.model_dump()
    values[field] = values[field].value

    with pytest.raises(ValidationError) as raised:
        RunRecord.model_validate(values, context={"contract": contract})

    issue = raised.value.errors(include_input=False)[0]

    assert issue["loc"] == (field,)
    assert issue["type"] == "is_instance_of"


@pytest.mark.parametrize("field", ["kind", "outcome", "runtime"])
def test_strict_python_attempt_construction_requires_enum_members(
    successful_record: RunRecord, field: str
) -> None:
    values = successful_record.attempts[0].model_dump()
    values[field] = values[field].value

    with pytest.raises(ValidationError) as raised:
        AttemptResult.model_validate(values)

    issue = raised.value.errors(include_input=False)[0]

    assert issue["loc"] == (field,)
    assert issue["type"] == "is_instance_of"


@pytest.mark.parametrize("field", ["runtime", "status"])
def test_unknown_enum_values_are_rejected_in_json(
    successful_record: RunRecord, contract: ExtractionContract, field: str
) -> None:
    payload = json.loads(successful_record.model_dump_json())
    payload[field] = "unknown-category"

    with pytest.raises(ValidationError) as raised:
        RunRecord.model_validate_json(json.dumps(payload), context={"contract": contract})

    issue = raised.value.errors(include_input=False)[0]

    assert issue["loc"] == (field,)
    assert issue["type"] == "enum"


@pytest.mark.parametrize(
    "field,value",
    [
        ("model_id", "other"),
        ("model_name", "other-model"),
        ("runtime", ModelRuntime.OLLAMA_NATIVE),
        ("runtime_version", "other-version"),
        ("model_digest", "b" * 64),
        ("serving_provider", "other-provider"),
    ],
)
def test_each_response_identity_attribute_is_checked(
    successful_record: RunRecord, field: str, value: object
) -> None:
    values = successful_record.attempts[0].model_dump()
    values["response"]["identity"][field] = value

    with pytest.raises(ValidationError, match="Response identity differs from the attempt"):
        AttemptResult.model_validate(values)


@pytest.mark.parametrize(
    "field,value",
    [
        ("raw_response", "different text"),
        ("duration_ms", 11.0),
        ("input_tokens", 13),
        ("output_tokens", 5),
        ("cost_usd", 0.01),
    ],
)
def test_each_response_measurement_is_checked(
    successful_record: RunRecord, field: str, value: object
) -> None:
    values = successful_record.attempts[0].model_dump()
    values["response"][field] = value

    with pytest.raises(ValidationError, match="Response evidence differs from attempt accounting"):
        AttemptResult.model_validate(values)


@pytest.mark.parametrize(
    "kind,outcome",
    [
        (ResponseKind.REFUSED, AttemptOutcome.REFUSED),
        (ResponseKind.TRUNCATED, AttemptOutcome.TRUNCATED),
        (ResponseKind.MISSING_RESPONSE, AttemptOutcome.MISSING_RESPONSE),
        (ResponseKind.INCOMPLETE, AttemptOutcome.INCOMPLETE),
        (ResponseKind.ERROR, AttemptOutcome.MODEL_ERROR),
    ],
)
def test_response_classification_and_record_validation_share_the_same_mapping(
    successful_record: RunRecord,
    contract: ExtractionContract,
    kind: ResponseKind,
    outcome: AttemptOutcome,
) -> None:
    original = successful_record.attempts[0].response
    assert original is not None
    reply = original.model_copy(update={"kind": kind})
    context = AttemptContext(
        number=1,
        kind=AttemptKind.EXTRACTION,
        identity=reply.identity,
        timeout_seconds=5.0,
        reservation=None,
    )
    result = response_attempt(context, reply, contract, expired=False)

    assert result.outcome is outcome

    values = result.model_dump()
    values["outcome"] = (
        AttemptOutcome.INCOMPLETE
        if outcome != AttemptOutcome.INCOMPLETE
        else AttemptOutcome.REFUSED
    )

    with pytest.raises(ValidationError, match="Response kind differs from the attempt outcome"):
        AttemptResult.model_validate(values)
