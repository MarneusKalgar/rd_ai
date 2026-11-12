"""Strict judge records; mechanical evidence checks do not establish entailment."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.runtime_types import NonEmptyText, StrictModel


class Decision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Proposition(StrictModel):
    index: int = Field(ge=0)
    verdict: Decision
    rationale: NonEmptyText


class Evidence(StrictModel):
    context_index: int = Field(ge=0)
    quote: NonEmptyText


class ClaimReview(StrictModel):
    claim_index: int = Field(ge=0)
    support: Decision
    evidence: list[Evidence]
    rationale: NonEmptyText


class Verdict(StrictModel):
    id: NonEmptyText
    correctness: Decision
    completeness: Decision
    abstention: Decision
    propositions: list[Proposition]
    claims: list[ClaimReview]
    summary_has_unsupported_additions: Decision
    rationale: NonEmptyText


def validate_verdict(raw: str, bundle: dict[str, Any]) -> Verdict:
    """Reject missing judgments, invented evidence and no-context grounding credit."""

    parse_json(raw)
    verdict = Verdict.model_validate_json(raw)
    if verdict.id != bundle["id"]:
        raise ValueError("Verdict identity differs")
    indexes = [item.index for item in verdict.propositions]
    if sorted(indexes) != list(range(len(bundle["expected_propositions"]))):
        raise ValueError("Proposition coverage differs")
    answer = bundle["answer"]
    claims = answer["claims"] if answer is not None else []
    if sorted(item.claim_index for item in verdict.claims) != list(range(len(claims))):
        raise ValueError("Claim coverage differs")
    context = bundle["evidence"]
    for claim in verdict.claims:
        if claim.support == Decision.PASS and not claim.evidence:
            raise ValueError("Supported claim requires exact evidence")
        for evidence in claim.evidence:
            if evidence.context_index >= len(context):
                raise ValueError("Evidence index differs")
            if evidence.quote not in context[evidence.context_index]["quote"]:
                raise ValueError("Evidence quote differs")
        if claim.support == Decision.PASS:
            cited = claims[claim.claim_index]["citations"]
            for evidence in claim.evidence:
                source = context[evidence.context_index]
                matches = any(
                    all(citation[key] == source[key] for key in citation) for citation in cited
                )
                if not matches:
                    raise ValueError("Supporting passage was not cited by this claim")
    if verdict.completeness == Decision.PASS and any(
        item.verdict != Decision.PASS for item in verdict.propositions
    ):
        raise ValueError("Complete verdict contradicts proposition decisions")
    if verdict.correctness == Decision.PASS and (
        verdict.summary_has_unsupported_additions == Decision.FAIL
        or any(item.verdict == Decision.FAIL for item in verdict.propositions)
    ):
        raise ValueError("Correct verdict contradicts detailed decisions")
    return verdict
