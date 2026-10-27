"""Operational correction evidence; the existing JSON Schema still owns PO values."""

from enum import StrEnum
from typing import Any, Final

from pydantic import Field

from extraction_service.execution.admission import AdmissionEvidence
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.types import GenerationRequest
from extraction_service.records import AttemptResult
from extraction_service.runtime_types import (
    Identifier,
    NonEmptyText,
    NonNegativeFloat,
    Sha256,
    StrictModel,
)

POLICY_VERSION: Final[str] = "buyer-id-single-correction-v1"
CONFIG_SNAPSHOT: Final[str] = "experiment-source.yaml"
POLICY_RULES: Final[dict[str, bool | int | str]] = {
    "max_new_physical_requests_per_input": 1,
    "transport_retries": 0,
    "new_primaries": 0,
    "target_field": "buyerProductIdentifier",
    "preserve_all_other_fields": True,
    "all_targets_must_resolve": True,
    "retain_original_on_rejection": True,
    "whole_po_certified": False,
}


class CorrectionDecision(StrEnum):
    NOT_NEEDED = "no_identifier_contradiction"
    ABSTAINED = "unknown_identifier_evidence"
    APPLIED = "guarded_correction_applied"
    OFF_TARGET = "rejected_off_target_changes"
    UNRESOLVED = "rejected_unresolved_identifiers"
    INVALID = "rejected_invalid_or_incomplete_response"
    TRANSPORT_FAILED = "transport_failed_no_retry"
    ADMISSION_FAILED = "admission_failed_no_request"
    SETUP_FAILED = "setup_failed_no_request"
    BASE_UNUSABLE = "base_extraction_unusable"


class IdentifierTarget(StrictModel):
    path: str = Field(pattern=r"^/lineItems/(0|[1-9][0-9]*)/buyerProductIdentifier$")
    product_name: str
    source_resolution: dict[str, Any]


class CorrectionCase(StrictModel):
    decision: CorrectionDecision
    targets: list[IdentifierTarget] = Field(default_factory=list)
    prior: JsonObject | None
    candidate: JsonObject | None = None
    retained: JsonObject | None
    before: dict[str, Any]
    after: dict[str, Any]
    request: GenerationRequest | None = None
    admission: AdmissionEvidence | None = None
    attempt: AttemptResult | None = None
    duration_ms: NonNegativeFloat = 0.0
    reason: str | None = None


class SavedCorrectionCase(StrictModel):
    input_id: Identifier
    base_record_sha256: Sha256
    original_source: NonEmptyText
    base_instructions: NonEmptyText
    result: CorrectionCase
