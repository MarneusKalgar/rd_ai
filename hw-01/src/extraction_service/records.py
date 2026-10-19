"""Strict operational envelopes; evidence checks live in record_validation."""

from typing import Self

from pydantic import Field, ValidationInfo, model_validator

from extraction_service.configuration.models import SamplingConfig
from extraction_service.extraction.validation import JsonObject, ValidationIssue
from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime, RunStatus
from extraction_service.record_validation import (
    check_attempt_history,
    check_attempt_outcome,
    check_final_extraction,
    check_run_accounting,
    check_run_status,
    contract_from_context,
)
from extraction_service.runtime_types import (
    Identifier,
    NonEmptyText,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveInt,
    Sha256,
    StrictModel,
)


class AttemptResult(StrictModel):
    """One physical request, including unsuccessful transport and model outcomes."""

    number: PositiveInt
    kind: AttemptKind
    outcome: AttemptOutcome
    model_id: Identifier
    model_name: Identifier
    runtime: ModelRuntime
    runtime_version: NonEmptyText | None = None
    model_digest: NonEmptyText | None = None
    raw_response: str | None
    error: NonEmptyText | None
    issues: list[ValidationIssue] = Field(default_factory=list)
    duration_ms: NonNegativeFloat
    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    cost_usd: NonNegativeFloat | None = None
    request_id: NonEmptyText | None = None
    serving_provider: NonEmptyText | None = None

    @model_validator(mode="after")
    def check_outcome(self) -> Self:
        """Require evidence appropriate to the declared outcome."""

        check_attempt_outcome(self)

        return self


class RunRecord(StrictModel):
    """Final result with checked attempt history, accounting and PO consistency.

    Validate with model_validate(..., context={"contract": contract}). The
    context is operational and is never serialized into the PO or record.
    """

    run_id: Identifier
    input_id: Identifier
    input_sha256: Sha256
    experiment_sha256: Sha256
    model_id: Identifier
    model_name: Identifier
    runtime: ModelRuntime
    prompt_id: Identifier
    prompt_sha256: Sha256
    sampling_id: Identifier
    sampling: SamplingConfig
    schema_sha256: Sha256
    status: RunStatus
    attempts: list[AttemptResult]
    extraction: JsonObject | None
    reason: NonEmptyText | None
    duration_ms: NonNegativeFloat
    total_input_tokens: NonNegativeInt | None
    total_output_tokens: NonNegativeInt | None
    total_cost_usd: NonNegativeFloat | None

    @model_validator(mode="after")
    def check_run(self, info: ValidationInfo) -> Self:
        """Coordinate status, evidence and accounting checks for this record."""

        contract = contract_from_context(info)

        if self.schema_sha256 != contract.identity.sha256:
            raise ValueError("Run schema hash differs from the validation contract")

        if self.sampling_id != self.sampling.id:
            raise ValueError("Sampling identity differs from its recorded parameters")

        check_run_status(self)
        check_attempt_history(self, contract)
        check_final_extraction(self, contract)
        check_run_accounting(self)

        return self
