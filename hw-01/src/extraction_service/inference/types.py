"""Provider-neutral requests and response evidence, without a second PO model."""

from enum import StrEnum
from typing import Any, Protocol, Self

from pydantic import Field

from extraction_service.configuration.models import SamplingConfig
from extraction_service.extraction import ExtractionContract
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime_types import (
    Identifier,
    NonEmptyText,
    NonNegativeFloat,
    NonNegativeInt,
    PositiveFloat,
    Sha256,
    StrictModel,
)


class ResponseKind(StrEnum):
    """Internal generation states, separate from provider-supplied finish reasons."""

    COMPLETED = "completed"
    REFUSED = "refused"
    TRUNCATED = "truncated"
    MISSING_RESPONSE = "missing_response"
    INCOMPLETE = "incomplete"
    ERROR = "error"


class GenerationRequest(StrictModel):
    """Rendered instructions, neutral source and a private copy of the PO schema.

    Callers may render correction evidence into instructions in section 6.4.
    Adapters never create correction prompts or inspect expected gold values.
    """

    instructions: NonEmptyText
    source_text: NonEmptyText
    output_schema: dict[str, Any] = Field(repr=False)
    sampling: SamplingConfig
    timeout_seconds: PositiveFloat

    @classmethod
    def from_contract(
        cls,
        *,
        instructions: str,
        source_text: str,
        contract: ExtractionContract,
        sampling: SamplingConfig,
        timeout_seconds: float,
    ) -> Self:
        """Take an independent schema snapshot without exposing gold labels."""

        return cls(
            instructions=instructions,
            source_text=source_text,
            output_schema=contract.schema_for_provider(),
            sampling=sampling,
            timeout_seconds=timeout_seconds,
        )


class ModelIdentity(StrictModel):
    """Requested model/runtime identity, distinct from reported response identity."""

    model_id: Identifier
    model_name: Identifier
    runtime: ModelRuntime
    serving_provider: NonEmptyText | None = None
    runtime_version: NonEmptyText | None = None
    model_digest: Sha256 | None = None


class ModelResponse(StrictModel):
    """Exact returned content and transport evidence; completed does not mean valid PO."""

    identity: ModelIdentity
    kind: ResponseKind
    raw_response: str | None = Field(repr=False)
    raw_http_body: str = Field(repr=False)
    reported_model: NonEmptyText
    serving_provider: NonEmptyText | None = None
    request_id: NonEmptyText | None = None
    finish_reason: str | None = None
    native_finish_reason: str | None = None
    refusal: str | None = None
    error: str | None = None
    duration_ms: NonNegativeFloat
    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    cost_usd: NonNegativeFloat | None = None
    total_duration_ns: NonNegativeInt | None = None
    load_duration_ns: NonNegativeInt | None = None
    credentials_redacted: bool = False


class ModelAdapter(Protocol):
    """Shared synchronous interface for one physical inference request per call."""

    @property
    def identity(self) -> ModelIdentity: ...

    def generate(self, request: GenerationRequest) -> ModelResponse: ...

    def close(self) -> None: ...
