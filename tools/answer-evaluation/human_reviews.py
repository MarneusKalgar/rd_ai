"""Validate explicit human decisions without promoting casual endorsements to anchors."""

import json
from pathlib import Path
from typing import Annotated, Any, Literal

from prepare import OUTPUT
from pydantic import Field
from verdicts import Decision

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.runtime_types import NonEmptyText, StrictModel


class HumanDecision(StrictModel):
    id: Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")]
    phase: Literal["calibration", "audit"]
    correctness: Decision
    completeness: Decision
    claim_support: list[Decision]
    abstention_or_conflict: Decision
    evidence_and_rationale: NonEmptyText
    expected_propositions_approved: bool


class HumanReview(StrictModel):
    authority: Literal["human-reviewed"]
    reviewer: NonEmptyText
    reviewed_without_judge_grades: Literal[True]
    decisions: list[HumanDecision]


def load_review(output: Path, raw: str) -> HumanReview:
    """Reject fabricated coverage, duplicate IDs, phase swaps and missing claim judgments."""

    parse_json(raw)
    review = HumanReview.model_validate_json(raw)
    mapping = json.loads((output / "private-mapping.json").read_bytes())
    bundles = {item["id"]: item for item in json.loads((output / "bundles.json").read_bytes())}
    seen = set()
    for decision in review.decisions:
        if decision.id not in mapping or decision.id in seen:
            raise ValueError("Unknown or repeated human review identity")
        seen.add(decision.id)
        if mapping[decision.id]["phase"] != decision.phase:
            raise ValueError("Human review phase differs")
        answer = bundles[decision.id]["answer"]
        expected = len(answer["claims"]) if answer is not None else 0
        if len(decision.claim_support) != expected:
            raise ValueError("Human claim coverage differs")
    return review


def compare(output: Path, review: HumanReview) -> dict[str, Any]:
    """Keep calibration/audit comparisons distinct and require real negative anchors."""

    summary = json.loads((output / "judge-v1/provisional-summary-R01.json").read_bytes())
    grades = {item["id"]: item for item in summary["rows"] if item["status"] == "valid_provisional"}
    mapping = json.loads((output / "private-mapping.json").read_bytes())
    bundles = {item["id"]: item for item in json.loads((output / "bundles.json").read_bytes())}
    phases: dict[str, Any] = {}
    for phase in ("calibration", "audit"):
        planned = {key for key, value in mapping.items() if value["phase"] == phase}
        applicable = {identity for identity in planned if bundles[identity]["answer"] is not None}
        decisions = [decision for decision in review.decisions if decision.phase == phase]
        compared = agreement = false_accepts = negative = unknown = 0
        ready = set()
        for decision in decisions:
            if not decision.expected_propositions_approved or decision.id not in grades:
                continue
            actual = grades[decision.id]["verdict"]
            support_by_index = {
                claim["claim_index"]: claim["support"] for claim in actual["claims"]
            }
            pairs = [
                (decision.correctness, actual["correctness"]),
                (decision.completeness, actual["completeness"]),
            ]
            pairs.extend(
                (label, support_by_index[index])
                for index, label in enumerate(decision.claim_support)
            )
            answer = bundles[decision.id]["answer"]
            if answer["status"] in ("insufficient_evidence", "conflicting_evidence"):
                pairs.append((decision.abstention_or_conflict, actual["abstention"]))
            if all(label != Decision.UNKNOWN for label, _ in pairs):
                ready.add(decision.id)
            for label, prediction in pairs:
                if label == Decision.UNKNOWN:
                    unknown += 1
                    continue
                compared += 1
                agreement += label == prediction
                negative += label == Decision.FAIL
                false_accepts += label == Decision.FAIL and prediction == "pass"
        exact = agreement / compared if compared else None
        phases[phase] = {
            "planned_jobs": len(planned),
            "applicable_judge_jobs": len(applicable),
            "human_records": len(decisions),
            "fully_anchored_graded_jobs": len(ready),
            "compared_verdicts": compared,
            "exact_agreement": exact,
            "negative_anchors": negative,
            "false_acceptances": false_accepts,
            "unknown_human_dimensions": unknown,
            "admission": "pass"
            if ready == applicable
            and negative > 0
            and exact is not None
            and exact >= 0.9
            and false_accepts == 0
            else "unresolved_or_failed",
        }
    return {
        "reviewer": review.reviewer,
        "authority": "human/model comparison, not adoption",
        "phases": phases,
        "audit_labels_used_in_prompt": False,
    }


if __name__ == "__main__":
    review = load_review(OUTPUT, (OUTPUT / "human-review.json").read_text())
    result = compare(OUTPUT, review)
    (OUTPUT / "human-comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
