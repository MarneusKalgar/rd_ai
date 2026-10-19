"""Check record evidence and accounting without defining purchase-order fields."""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Final

from pydantic import ValidationInfo

from extraction_service.extraction import ExtractionContract
from extraction_service.record_types import (
    CONTRACT_CONTEXT_KEY,
    EXTRACTION_ATTEMPT,
    FIRST_ATTEMPT_NUMBER,
    INVALID_OUTCOME,
    NOT_ATTEMPTED_STATUS,
    SUCCEEDED_STATUS,
    TRANSPORT_ERROR_OUTCOME,
    TRUNCATED_OUTCOME,
    VALID_OUTCOME,
    VALIDATED_OUTCOMES,
)

if TYPE_CHECKING:
    from extraction_service.records import AttemptResult, RunRecord

ACCOUNTING_RELATIVE_TOLERANCE: Final[float] = 1e-9
ACCOUNTING_ABSOLUTE_TOLERANCE: Final[float] = 1e-12
INCOMPLETE_TOTAL_MESSAGE: Final[str] = "Run totals must include all physical requests"


def check_total(values: Sequence[int | float | None], total: int | float | None) -> None:
    """Preserve unknown accounting and compare complete totals without coercion."""

    known_total: int | float = 0

    for value in values:
        if value is None:
            if total is not None:
                raise ValueError("Unknown attempt accounting must remain unknown in totals")

            return

        known_total += value

    if total is None:
        raise ValueError(INCOMPLETE_TOTAL_MESSAGE)

    if isinstance(total, int) and isinstance(known_total, int):
        matches = total == known_total
    else:
        matches = math.isclose(
            total,
            known_total,
            rel_tol=ACCOUNTING_RELATIVE_TOLERANCE,
            abs_tol=ACCOUNTING_ABSOLUTE_TOLERANCE,
        )

    if not matches:
        raise ValueError(INCOMPLETE_TOTAL_MESSAGE)


def check_attempt_outcome(attempt: AttemptResult) -> None:
    """Require response, error and issue evidence appropriate to an outcome."""

    if attempt.outcome in VALIDATED_OUTCOMES:
        if attempt.raw_response is None or attempt.error is not None:
            raise ValueError("Validated attempts require raw response and no transport error")

        if (attempt.outcome == INVALID_OUTCOME) != bool(attempt.issues):
            raise ValueError("Validation issues must agree with attempt outcome")

        return

    if attempt.error is None:
        raise ValueError("Failed transport/model outcomes require an error")

    if attempt.outcome == TRANSPORT_ERROR_OUTCOME and attempt.raw_response is not None:
        raise ValueError("Transport failure cannot claim a model response")

    if attempt.outcome != TRUNCATED_OUTCOME and attempt.issues:
        raise ValueError("Only a returned response can carry validation issues")


def contract_from_context(info: ValidationInfo) -> ExtractionContract:
    """Require the approved contract supplied by the run-record caller."""

    context = info.context
    contract = context.get(CONTRACT_CONTEXT_KEY) if isinstance(context, dict) else None

    if not isinstance(contract, ExtractionContract):
        raise ValueError("RunRecord validation requires extraction contract context")

    return contract


def check_run_status(record: RunRecord) -> None:
    """Keep succeeded, failed and not-attempted evidence mutually consistent."""

    if record.status == NOT_ATTEMPTED_STATUS:
        if record.attempts or record.extraction is not None or record.reason is None:
            raise ValueError("Not-attempted runs require a reason and no attempts/extraction")

        return

    if not record.attempts:
        raise ValueError("Attempted runs require attempt history")

    final_attempt = record.attempts[-1]

    if record.status == SUCCEEDED_STATUS:
        if (
            record.extraction is None
            or record.reason is not None
            or final_attempt.outcome != VALID_OUTCOME
        ):
            raise ValueError("Successful runs require a valid final attempt and extraction")
    elif (
        record.extraction is not None
        or record.reason is None
        or final_attempt.outcome == VALID_OUTCOME
    ):
        raise ValueError("Failed runs require a failed final attempt, reason and no extraction")


def check_attempt_identity(record: RunRecord, attempt: AttemptResult, expected_number: int) -> None:
    """Check physical request sequence and its model/runtime identity."""

    if attempt.number != expected_number or attempt.model_id != record.model_id:
        raise ValueError("Attempt numbering/model identity is inconsistent")

    if attempt.model_name != record.model_name or attempt.runtime != record.runtime:
        raise ValueError("Attempt model/runtime differs from the run variant")

    if expected_number == FIRST_ATTEMPT_NUMBER and attempt.kind != EXTRACTION_ATTEMPT:
        raise ValueError("First attempt must be an extraction")


def check_attempt_response(attempt: AttemptResult, contract: ExtractionContract) -> None:
    """Compare reported validation evidence with the authoritative validator."""

    if attempt.outcome not in VALIDATED_OUTCOMES:
        return

    if attempt.raw_response is None:
        raise ValueError("Validated attempts require a raw response")

    outcome = contract.validate_json(attempt.raw_response)

    if outcome.is_valid != (attempt.outcome == VALID_OUTCOME):
        raise ValueError("Attempt outcome disagrees with authoritative validation")

    if tuple(attempt.issues) != outcome.issues:
        raise ValueError("Attempt issues disagree with authoritative validation")


def check_attempt_history(record: RunRecord, contract: ExtractionContract) -> None:
    """Check every physical request independently of the final extraction."""

    for expected_number, attempt in enumerate(record.attempts, start=FIRST_ATTEMPT_NUMBER):
        check_attempt_identity(record, attempt, expected_number)
        check_attempt_response(attempt, contract)


def check_final_extraction(record: RunRecord, contract: ExtractionContract) -> None:
    """Require a final PO to match both the schema and the final response."""

    if record.extraction is None:
        return

    raw_extraction = json.dumps(record.extraction, ensure_ascii=False, allow_nan=False)
    outcome = contract.validate_json(raw_extraction)
    final_response = record.attempts[-1].raw_response

    if not outcome.is_valid or final_response is None:
        raise ValueError("Final extraction must satisfy the authoritative schema")

    final_outcome = contract.validate_json(final_response)

    if final_outcome.value != record.extraction:
        raise ValueError("Final extraction differs from the final validated response")


def check_run_accounting(record: RunRecord) -> None:
    """Include every physical request in known duration, token and cost totals."""

    measured_duration = sum(attempt.duration_ms for attempt in record.attempts)

    if record.duration_ms < measured_duration:
        raise ValueError("Run duration cannot be shorter than its physical requests")

    check_total([attempt.input_tokens for attempt in record.attempts], record.total_input_tokens)
    check_total([attempt.output_tokens for attempt in record.attempts], record.total_output_tokens)
    check_total([attempt.cost_usd for attempt in record.attempts], record.total_cost_usd)
