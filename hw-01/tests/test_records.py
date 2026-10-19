import json
from typing import Any

import pytest
from pydantic import ValidationError

from hw01.extraction import ExtractionContract
from hw01.extraction.validation import JsonObject
from hw01.records import AttemptResult, RunRecord


@pytest.fixture
def run_data(contract: ExtractionContract, gold: JsonObject) -> dict[str, Any]:
    return {
        "run_id": "run-1",
        "input_id": "input-1",
        "input_sha256": "1" * 64,
        "experiment_sha256": "2" * 64,
        "model_id": "local",
        "model_name": "candidate-local",
        "runtime": "ollama-docker",
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
        "status": "succeeded",
        "attempts": [
            {
                "number": 1,
                "kind": "extraction",
                "outcome": "valid",
                "model_id": "local",
                "model_name": "candidate-local",
                "runtime": "ollama-docker",
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
        ("status", "failed"),
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
        "kind": "extraction",
        "outcome": "transport_error",
        "model_id": "local",
        "model_name": "candidate-local",
        "runtime": "ollama-docker",
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
        kind="extraction",
        outcome="invalid",
        model_id="local",
        model_name="candidate-local",
        runtime="ollama-docker",
        raw_response="{}",
        error=None,
        issues=list(invalid.issues),
        duration_ms=1.0,
        input_tokens=1,
        output_tokens=1,
        cost_usd=0.0,
    )
    run_data["attempts"][0]["number"] = 2
    run_data["attempts"][0]["kind"] = "correction"
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
        status="not_attempted",
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
        ("kind", "correction"),
        ("model_id", "other-model"),
        ("model_name", "other-model"),
        ("runtime", "openrouter"),
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
        kind="extraction",
        outcome="invalid",
        model_id="local",
        model_name="candidate-local",
        runtime="ollama-docker",
        raw_response="{}",
        error=None,
        issues=list(invalid.issues),
        duration_ms=1.0,
    )
    run_data.update(
        status="failed",
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
