"""Strict answers and application-owned citation checks; no semantic grading."""

from enum import StrEnum
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from extraction_service.configuration.models import SamplingConfig
from extraction_service.extraction.json_parsing import parse_json
from extraction_service.inference.types import GenerationRequest
from extraction_service.retrieval.core import MAX_CONTEXT_BYTES, canonical
from extraction_service.runtime_types import NonEmptyText, Sha256, StrictModel


class Arm(StrEnum):
    NONE = "none"
    BM25 = "bm25"
    VECTOR = "vector"


class AnswerStatus(StrEnum):
    GROUNDED = "grounded"
    UNVERIFIED = "unverified"
    INSUFFICIENT = "insufficient_evidence"
    CONFLICTING = "conflicting_evidence"


class Citation(StrictModel):
    """An exact supplied source span; identity is never inferred from generated prose."""

    source_id: NonEmptyText
    revision: NonEmptyText
    sha256: Sha256
    start: Annotated[int, Field(ge=0)]
    end: Annotated[int, Field(gt=0)]

    @model_validator(mode="after")
    def check_span(self) -> Self:
        if self.end <= self.start:
            raise ValueError("Empty or reversed citation span")
        return self


class Context(Citation):
    quote: NonEmptyText


class Claim(StrictModel):
    text: NonEmptyText
    citations: Annotated[list[Citation], Field(max_length=3)]


class Answer(StrictModel):
    """Independent explanation schema; outputs grant no editing authority."""

    status: AnswerStatus
    answer: NonEmptyText | None
    claims: Annotated[list[Claim], Field(max_length=8)]

    @model_validator(mode="after")
    def check_status(self) -> Self:
        abstained = self.status in (AnswerStatus.INSUFFICIENT, AnswerStatus.CONFLICTING)
        if abstained and (self.answer is not None or self.claims):
            raise ValueError("Non-answer must have null answer and no claims")
        if not abstained and (self.answer is None or not self.claims):
            raise ValueError("Answer requires text and explicit claims")
        if self.status == AnswerStatus.GROUNDED and any(not c.citations for c in self.claims):
            raise ValueError("Every grounded claim requires a citation")
        return self


class AnswerJob(StrictModel):
    """Authorized question/context only; rubric and expected answers never enter requests."""

    case_id: NonEmptyText
    arm: Arm
    scope: Literal["A", "B"]
    question: NonEmptyText
    context: Annotated[list[Context], Field(max_length=3)]
    retrieval_status: Literal["evidence_found", "insufficient_evidence", "conflicting_evidence"]

    @property
    def key(self) -> str:
        return f"{self.case_id}/{self.arm.value}"

    @property
    def skip_reason(self) -> str | None:
        if self.arm == Arm.NONE:
            if self.context:
                raise ValueError("No-context arm cannot receive references")
            return None
        if self.retrieval_status == "conflicting_evidence":
            return "conflicting_evidence"
        return None if self.context else "insufficient_evidence"

    def request(
        self, instructions: str, sampling: SamplingConfig, timeout: float
    ) -> GenerationRequest:
        """Render matched prompts without leaking arm labels, relevance labels or scope names."""

        if self.skip_reason is not None:
            raise ValueError("Deterministic non-answer must not call the generator")
        if self.scope not in ("A", "B") or len(self.question.encode()) > 4096:
            raise ValueError("Invalid trusted question context")
        if sum(len(item.quote.encode()) for item in self.context) > MAX_CONTEXT_BYTES:
            raise ValueError("Context byte limit exceeded")
        return GenerationRequest(
            instructions=instructions,
            source_text=canonical(
                {"question": self.question, "evidence": [c.model_dump() for c in self.context]}
            ).decode(),
            output_schema=Answer.model_json_schema(),
            sampling=sampling,
            timeout_seconds=timeout,
        )


def validate_answer(raw: str, job: AnswerJob) -> Answer:
    """Check syntax and citation eligibility only; entailment remains unreviewed."""

    # Reject duplicate keys before Pydantic's JSON decoder can discard them.
    parse_json(raw)
    answer = Answer.model_validate_json(raw)
    allowed = {
        canonical(Citation.model_validate(c.model_dump(exclude={"quote"})).model_dump())
        for c in job.context
    }
    for claim in answer.claims:
        for citation in claim.citations:
            if canonical(citation.model_dump()) not in allowed:
                raise ValueError("Citation identity/version/span was not supplied")
    return answer
