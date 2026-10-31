import json
from dataclasses import replace
from typing import Any

import pytest
from pydantic import ValidationError

from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime, RunStatus
from extraction_service.records import AttemptResult, RunRecord


@pytest.fixture
def run_data(contract: ExtractionContract, gold: JsonObject) -> dict[str, Any]:
    return {
        "run_id": "run-1",
        "input_id": "input-1",
        "input_sha256": "1" * 64,
        "experiment_sha256": "2" * 64,
        "model_id": "local",
        "model_name": "candidate-local",
        "runtime": ModelRuntime.OLLAMA_DOCKER,
        "prompt_id": "v1",
        "prompt_sha256": "3" * 64,
        "sampling_id": "baseline",
        "sampling": {
            "id": "baseline",
            "temperature": 0.0,
            "top_p": 1.0,
            "max_output_tokens": 4096,
        },
        "schema_sha256": contract.identity.sha256,
        "status": RunStatus.SUCCEEDED,
        "attempts": [
            {
                "number": 1,
                "kind": AttemptKind.EXTRACTION,
                "outcome": AttemptOutcome.VALID,
                "model_id": "local",
                "model_name": "candidate-local",
                "runtime": ModelRuntime.OLLAMA_DOCKER,
                "raw_response": json.dumps(gold),
                "error": None,
                "duration_ms": 12.0,
                "input_tokens": 10,
                "output_tokens": 20,
                "cost_usd": 0.0,
            }
        ],
        "extraction": gold,
        "reason": None,
        "duration_ms": 15.0,
        "total_input_tokens": 10,
        "total_output_tokens": 20,
        "total_cost_usd": 0.0,
    }


def test_successful_record_round_trips_without_redefining_po_fields(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    record = RunRecord.model_validate(run_data, context={"contract": contract})
    restored = RunRecord.model_validate_json(
        record.model_dump_json(), context={"contract": contract}
    )

    assert restored == record
    assert record.extraction == run_data["extraction"]
    assert record.total_cost_usd == 0.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", RunStatus.FAILED),
        ("extraction", None),
        ("reason", "unexpected"),
        ("schema_sha256", "0" * 64),
        ("duration_ms", 1.0),
        ("duration_ms", float("nan")),
        ("total_input_tokens", "10"),
        ("total_output_tokens", -1),
        ("total_cost_usd", 1.0),
        ("extra_metadata", "unexpected"),
    ],
)
def test_inconsistent_or_non_strict_run_values_are_rejected(
    run_data: dict[str, Any], contract: ExtractionContract, field: str, value: object
) -> None:
    run_data[field] = value

    with pytest.raises(ValidationError):
        RunRecord.model_validate(run_data, context={"contract": contract})


def test_success_cannot_hide_schema_invalid_po_or_different_final_values(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    run_data["extraction"]["model"] = "outside-schema"

    with pytest.raises(ValidationError, match="authoritative schema"):
        RunRecord.model_validate(run_data, context={"contract": contract})

    del run_data["extraction"]["model"]
    run_data["extraction"]["buyerName"] = "A different buyer"

    with pytest.raises(ValidationError, match="differs from the final"):
        RunRecord.model_validate(run_data, context={"contract": contract})


def test_declared_valid_attempt_is_checked_against_its_raw_response(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    run_data["attempts"][0]["raw_response"] = "{}"

    with pytest.raises(ValidationError, match="outcome disagrees"):
        RunRecord.model_validate(run_data, context={"contract": contract})


def test_unknown_usage_stays_unknown_and_failed_requests_contribute_to_totals(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    retry = {
        "number": 1,
        "kind": AttemptKind.EXTRACTION,
        "outcome": AttemptOutcome.TRANSPORT_ERROR,
        "model_id": "local",
        "model_name": "candidate-local",
        "runtime": ModelRuntime.OLLAMA_DOCKER,
        "raw_response": None,
        "error": "timeout; billing unavailable",
        "duration_ms": 2.0,
    }
    run_data["attempts"][0]["number"] = 2
    run_data["attempts"].insert(0, retry)
    run_data["total_input_tokens"] = None
    run_data["total_output_tokens"] = None
    run_data["total_cost_usd"] = None

    result = RunRecord.model_validate(run_data, context={"contract": contract})

    assert result.total_cost_usd is None
    assert len(result.attempts) == 2

    run_data["total_cost_usd"] = 0.0

    with pytest.raises(ValidationError, match="must remain unknown"):
        RunRecord.model_validate(run_data, context={"contract": contract})


def test_invalid_then_corrected_attempt_preserves_original_issues_and_accounting(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    invalid = contract.validate_json("{}")
    first = AttemptResult(
        number=1,
        kind=AttemptKind.EXTRACTION,
        outcome=AttemptOutcome.INVALID,
        model_id="local",
        model_name="candidate-local",
        runtime=ModelRuntime.OLLAMA_DOCKER,
        raw_response="{}",
        error=None,
        issues=list(invalid.issues),
        duration_ms=1.0,
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
    )
    run_data["attempts"][0]["number"] = 2
    run_data["attempts"][0]["kind"] = AttemptKind.CORRECTION
    run_data["attempts"].insert(0, first)
    run_data["total_input_tokens"] = 11
    run_data["total_output_tokens"] = 21

    record = RunRecord.model_validate(run_data, context={"contract": contract})
    restored = RunRecord.model_validate_json(
        record.model_dump_json(), context={"contract": contract}
    )

    assert restored.attempts[0].issues == list(invalid.issues)
    assert restored.attempts[1].kind == "correction"


def test_not_attempted_records_are_distinct_from_attempted_failures(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    run_data.update(
        status=RunStatus.NOT_ATTEMPTED,
        attempts=[],
        extraction=None,
        reason="budget exhausted",
        duration_ms=0.0,
        total_input_tokens=0,
        total_output_tokens=0,
        total_cost_usd=0.0,
    )

    record = RunRecord.model_validate(run_data, context={"contract": contract})

    assert record.status == "not_attempted"
    assert record.attempts == []


def test_record_requires_contract_context(run_data: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="requires extraction contract context"):
        RunRecord.model_validate(run_data)


@pytest.mark.parametrize(
    "field,value",
    [
        ("number", 2),
        ("kind", AttemptKind.CORRECTION),
        ("model_id", "other-model"),
        ("model_name", "other-model"),
        ("runtime", ModelRuntime.OPENROUTER),
        ("duration_ms", -1.0),
        ("input_tokens", True),
        ("raw_response", None),
        ("error", "unexpected failure"),
        ("cost_usd", -1.0),
        ("extra", "unknown"),
    ],
)
def test_invalid_attempt_metadata_cannot_create_a_successful_run(
    run_data: dict[str, Any], contract: ExtractionContract, field: str, value: object
) -> None:
    run_data["attempts"][0][field] = value

    with pytest.raises(ValidationError):
        RunRecord.model_validate(run_data, context={"contract": contract})


def test_failed_extraction_record_retains_invalid_response_and_can_be_reloaded(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    invalid = contract.validate_json("{}")
    attempt = AttemptResult(
        number=1,
        kind=AttemptKind.EXTRACTION,
        outcome=AttemptOutcome.INVALID,
        model_id="local",
        model_name="candidate-local",
        runtime=ModelRuntime.OLLAMA_DOCKER,
        raw_response="{}",
        error=None,
        issues=list(invalid.issues),
        duration_ms=1.0,
    )
    run_data.update(
        status=RunStatus.FAILED,
        attempts=[attempt],
        extraction=None,
        reason="invalid output",
        total_input_tokens=None,
        total_output_tokens=None,
        total_cost_usd=None,
    )

    record = RunRecord.model_validate(run_data, context={"contract": contract})
    restored = RunRecord.model_validate_json(
        record.model_dump_json(), context={"contract": contract}
    )

    assert restored.status == "failed"
    assert restored.attempts[0].raw_response == "{}"
    assert restored.attempts[0].issues == list(invalid.issues)


def test_sampling_id_cannot_disagree_with_recorded_parameters(
    run_data: dict[str, Any], contract: ExtractionContract
) -> None:
    run_data["sampling_id"] = "other-config"

    with pytest.raises(ValidationError, match="Sampling identity differs"):
        RunRecord.model_validate(run_data, context={"contract": contract})


@pytest.mark.parametrize(
    "status,expected_error",
    [
        (RunStatus.FAILED, "Failed runs require a failed final attempt"),
        (RunStatus.NOT_ATTEMPTED, "Not-attempted runs require a reason and no attempts"),
    ],
)
def test_unsuccessful_status_cannot_hide_a_valid_request(
    run_data: dict[str, Any],
    contract: ExtractionContract,
    status: RunStatus,
    expected_error: str,
) -> None:
    baseline = RunRecord.model_validate(run_data, context={"contract": contract})

    assert baseline.status == "succeeded"

    run_data.update(status=status, extraction=None, reason="Contradictory status")

    with pytest.raises(ValidationError, match=expected_error):
        RunRecord.model_validate(run_data, context={"contract": contract})


@pytest.mark.parametrize("outcome", ["valid", "invalid"])
def test_attempt_validation_issues_must_match_its_outcome(
    run_data: dict[str, Any], contract: ExtractionContract, outcome: str
) -> None:
    attempt = run_data["attempts"][0]
    invalid = contract.validate_json("{}")

    if outcome == "valid":
        attempt["issues"] = list(invalid.issues)
    else:
        attempt.update(outcome=AttemptOutcome.INVALID, raw_response="{}", issues=[])

    with pytest.raises(ValidationError, match="Validation issues must agree"):
        AttemptResult.model_validate(attempt)


@pytest.mark.parametrize("field", ["message", "keyword", "instance_path"])
def test_invalid_attempt_cannot_store_fabricated_validation_evidence(
    run_data: dict[str, Any], contract: ExtractionContract, field: str
) -> None:
    invalid = contract.validate_json("{}")
    run_data["attempts"][0].update(
        outcome=AttemptOutcome.INVALID,
        raw_response="{}",
        issues=list(invalid.issues),
    )
    run_data.update(status=RunStatus.FAILED, extraction=None, reason="Invalid output")

    baseline = RunRecord.model_validate(run_data, context={"contract": contract})

    assert baseline.attempts[0].issues == list(invalid.issues)

    original_issue = invalid.issues[0]

    if field == "message":
        fabricated_issue = replace(original_issue, message="Fabricated evidence")
    elif field == "keyword":
        fabricated_issue = replace(original_issue, keyword="fabricated_keyword")
    else:
        fabricated_issue = replace(original_issue, instance_path="/fabricated/path")

    run_data["attempts"][0]["issues"][0] = fabricated_issue

    with pytest.raises(ValidationError, match="Attempt issues disagree"):
        RunRecord.model_validate(run_data, context={"contract": contract})


@pytest.mark.parametrize(
    "total_field,incomplete_total",
    [
        ("total_input_tokens", 10),
        ("total_output_tokens", 20),
        ("total_cost_usd", 0.5),
    ],
)
def test_known_accounting_includes_failed_requests(
    run_data: dict[str, Any],
    contract: ExtractionContract,
    total_field: str,
    incomplete_total: int | float,
) -> None:
    run_data.update(
        model_id="provider", model_name="candidate-provider", runtime=ModelRuntime.OPENROUTER
    )
    final_attempt = run_data["attempts"][0]
    final_attempt.update(
        model_id="provider",
        model_name="candidate-provider",
        runtime=ModelRuntime.OPENROUTER,
        cost_usd=0.5,
    )
    failed_attempt = final_attempt.copy()
    failed_attempt.update(
        outcome=AttemptOutcome.TRANSPORT_ERROR,
        raw_response=None,
        error="Timeout with known usage",
        duration_ms=1.0,
        input_tokens=1,
        output_tokens=2,
        cost_usd=0.25,
    )
    final_attempt["number"] = 2
    run_data["attempts"].insert(0, failed_attempt)
    run_data.update(total_input_tokens=11, total_output_tokens=22, total_cost_usd=0.75)

    baseline = RunRecord.model_validate(run_data, context={"contract": contract})

    assert baseline.total_input_tokens == 11
    assert baseline.total_output_tokens == 22
    assert baseline.total_cost_usd == 0.75

    run_data[total_field] = incomplete_total

    with pytest.raises(ValidationError, match="Run totals must include all physical requests"):
        RunRecord.model_validate(run_data, context={"contract": contract})
