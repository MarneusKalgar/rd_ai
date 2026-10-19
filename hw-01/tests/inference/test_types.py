"""Strict enum construction and stable string values across persisted JSON boundaries."""

import json

import pytest
from pydantic import ValidationError

from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.types import ModelIdentity, ModelResponse, ResponseKind


@pytest.fixture
def response() -> ModelResponse:
    identity = ModelIdentity(model_id="provider", model_name="test/model", runtime="openrouter")

    return ModelResponse(
        identity=identity,
        kind=ResponseKind.COMPLETED,
        raw_response="  {invalid PO}\n",
        raw_http_body='{"original":"envelope"}',
        reported_model="test/model",
        duration_ms=1.0,
    )


@pytest.fixture
def failure_evidence() -> FailureEvidence:
    return FailureEvidence(
        kind=FailureKind.CONNECTION,
        retryable=True,
        message="connection failed",
        duration_ms=1.0,
    )


@pytest.mark.parametrize(
    "kind,serialized_kind",
    [
        (ResponseKind.COMPLETED, "completed"),
        (ResponseKind.REFUSED, "refused"),
        (ResponseKind.TRUNCATED, "truncated"),
        (ResponseKind.MISSING_RESPONSE, "missing_response"),
        (ResponseKind.INCOMPLETE, "incomplete"),
        (ResponseKind.ERROR, "error"),
    ],
)
def test_response_enum_round_trip(
    kind: ResponseKind, serialized_kind: str, response: ModelResponse
) -> None:
    values = response.model_dump()
    values["kind"] = kind
    result = ModelResponse.model_validate(values)

    serialized = result.model_dump_json()
    payload = json.loads(serialized)
    restored = ModelResponse.model_validate_json(serialized)

    assert result.kind is kind
    assert result.model_dump()["kind"] is kind
    assert payload["kind"] == serialized_kind
    assert restored.kind is kind
    assert restored.raw_response == "  {invalid PO}\n"
    assert restored.raw_http_body == '{"original":"envelope"}'


@pytest.mark.parametrize(
    "kind,serialized_kind",
    [
        (FailureKind.TIMEOUT, "timeout"),
        (FailureKind.CONNECTION, "connection"),
        (FailureKind.RATE_LIMIT, "rate_limit"),
        (FailureKind.AUTHENTICATION, "authentication"),
        (FailureKind.QUOTA, "quota"),
        (FailureKind.UNSUPPORTED_REQUEST, "unsupported_request"),
        (FailureKind.SERVER_ERROR, "server_error"),
        (FailureKind.PROTOCOL_ERROR, "protocol_error"),
        (FailureKind.HTTP_ERROR, "http_error"),
    ],
)
def test_failure_enum_round_trip_and_exception_text(
    kind: FailureKind, serialized_kind: str, failure_evidence: FailureEvidence
) -> None:
    values = failure_evidence.model_dump()
    values["kind"] = kind
    result = FailureEvidence.model_validate(values)

    serialized = result.model_dump_json()
    payload = json.loads(serialized)
    restored = FailureEvidence.model_validate_json(serialized)
    exception = ModelTransportError(result)

    assert result.kind is kind
    assert result.model_dump()["kind"] is kind
    assert payload["kind"] == serialized_kind
    assert restored.kind is kind
    assert str(exception) == f"{serialized_kind}: connection failed"


@pytest.mark.parametrize("model", ["response", "failure"])
def test_strict_python_construction_requires_enum_member(
    model: str, response: ModelResponse, failure_evidence: FailureEvidence
) -> None:
    baseline = response if model == "response" else failure_evidence
    values = baseline.model_dump()
    values["kind"] = baseline.kind.value

    with pytest.raises(ValidationError) as failure:
        type(baseline).model_validate(values)

    issue = failure.value.errors()[0]
    assert issue["loc"] == ("kind",)
    assert issue["type"] == "is_instance_of"


@pytest.mark.parametrize("model", ["response", "failure"])
def test_unknown_internal_category_in_json_is_rejected(
    model: str, response: ModelResponse, failure_evidence: FailureEvidence
) -> None:
    baseline = response if model == "response" else failure_evidence
    payload = baseline.model_dump(mode="json")
    payload["kind"] = "future_internal_category"

    with pytest.raises(ValidationError) as failure:
        type(baseline).model_validate_json(json.dumps(payload))

    issue = failure.value.errors()[0]
    assert issue["loc"] == ("kind",)
    assert issue["type"] == "enum"
