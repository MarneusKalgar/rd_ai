"""Non-generating request admission, separate from paid spending reservations."""

from enum import StrEnum
from typing import Protocol

from pydantic import model_validator

from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.runtime_types import NonEmptyText, PositiveInt, Sha256, StrictModel


class AdmissionReason(StrEnum):
    CONTEXT_IDENTITY_MISMATCH = "context_identity_mismatch"
    CONTEXT_CAPACITY_EXCEEDED = "context_capacity_exceeded"
    PROVIDER_IDENTITY_MISMATCH = "provider_coverage_identity_mismatch"
    PROVIDER_BOUND_UNAVAILABLE = "verified_provider_token_bound_unavailable"


class AdmissionRejected(ValueError):
    """A request cannot safely fit; no physical generation has occurred."""

    def __init__(self, reason: AdmissionReason) -> None:
        self.reason = reason

        super().__init__(reason.value)


class ContextEnforcement(StrEnum):
    COUNTED = "counted"
    PROVIDER = "provider"


class AdmissionEvidence(StrictModel):
    method: NonEmptyText
    request_sha256: Sha256
    context_enforcement: ContextEnforcement = ContextEnforcement.COUNTED
    counter_identity: NonEmptyText | None
    prompt_token_bound: PositiveInt | None
    output_allowance: PositiveInt
    context_length: PositiveInt

    @model_validator(mode="after")
    def check_counter_evidence(self) -> AdmissionEvidence:
        """Never serialize provider enforcement as a verified local token count."""

        if self.context_enforcement == ContextEnforcement.COUNTED:
            if self.counter_identity is None or self.prompt_token_bound is None:
                raise ValueError("Counted admission requires counter identity and token bound")
        elif self.counter_identity is not None or self.prompt_token_bound is not None:
            raise ValueError("Provider context enforcement has no verified counter or token bound")

        return self


class RequestAdmission(Protocol):
    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence: ...
