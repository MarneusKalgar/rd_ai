"""Reject contradictions between transport evidence and its attempt envelope."""

import pytest
from pydantic import ValidationError

from extraction_service.execution.evidence import AttemptContext, failure_attempt
from extraction_service.inference.errors import FailureEvidence, FailureKind
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import AttemptKind
from extraction_service.records import AttemptResult


@pytest.fixture
def paid_failure_attempt(paid_identity: ModelIdentity) -> AttemptResult:
    context = AttemptContext(
        number=1,
        kind=AttemptKind.EXTRACTION,
        identity=paid_identity,
        timeout_seconds=5.0,
        reservation=None,
    )
    evidence = FailureEvidence(
        kind=FailureKind.TIMEOUT,
        retryable=True,
        message="Timeout after billable work",
        duration_ms=10.0,
        input_tokens=2,
        output_tokens=3,
        cost_usd=0.01,
    )

    return failure_attempt(context, evidence)


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("duration_ms", 11.0, "Transport timing differs from the attempt"),
        ("input_tokens", 3, "Transport usage differs from the attempt"),
        ("output_tokens", 4, "Transport usage differs from the attempt"),
        ("cost_usd", 0.02, "Transport billed cost differs from the attempt"),
    ],
)
def test_failure_measurement_cannot_disagree_with_attempt(
    paid_failure_attempt: AttemptResult,
    field: str,
    value: int | float,
    message: str,
) -> None:
    values = paid_failure_attempt.model_dump()
    baseline = AttemptResult.model_validate(values)

    assert baseline == paid_failure_attempt

    values[field] = value

    with pytest.raises(ValidationError, match=message) as raised:
        AttemptResult.model_validate(values)

    issue = raised.value.errors(include_input=False)[0]

    assert issue["loc"] == ()
    assert issue["type"] == "value_error"
