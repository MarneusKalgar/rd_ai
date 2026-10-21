"""Non-generating request admission, separate from paid spending reservations."""

from enum import StrEnum
from typing import Protocol

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


class AdmissionEvidence(StrictModel):
    method: NonEmptyText
    request_sha256: Sha256
    counter_identity: NonEmptyText
    prompt_token_bound: PositiveInt
    output_allowance: PositiveInt
    context_length: PositiveInt


class RequestAdmission(Protocol):
    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence: ...
