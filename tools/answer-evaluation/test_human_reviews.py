"""Generic feedback, altered populations and unknown human labels cannot become a pass."""

import json
from pathlib import Path
from typing import Any

import pytest
from human_reviews import HumanReview, compare, load_review


def test_explicit_review_retains_unknown(tmp_path: Path) -> None:
    identity = "a" * 16
    (tmp_path / "private-mapping.json").write_text(json.dumps({identity: {"phase": "audit"}}))
    (tmp_path / "bundles.json").write_text(json.dumps([{"id": identity, "answer": None}]))
    raw: dict[str, Any] = {
        "authority": "human-reviewed",
        "reviewer": "fixture reviewer",
        "reviewed_without_judge_grades": True,
        "decisions": [
            {
                "id": identity,
                "phase": "audit",
                "correctness": "unknown",
                "completeness": "unknown",
                "claim_support": [],
                "abstention_or_conflict": "unknown",
                "evidence_and_rationale": "Cannot resolve",
                "expected_propositions_approved": False,
            }
        ],
    }

    result = load_review(tmp_path, json.dumps(raw))

    assert result.decisions[0].correctness == "unknown"
    assert result.decisions[0].expected_propositions_approved is False
    raw["decisions"][0]["phase"] = "calibration"
    with pytest.raises(ValueError, match="phase differs"):
        load_review(tmp_path, json.dumps(raw))


def test_general_endorsement_is_not_an_anchor(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        load_review(tmp_path, json.dumps({"feedback": "looks good to me"}))


def test_claim_comparison_uses_identity_not_array_position(tmp_path: Path) -> None:
    identity = "a" * 16
    (tmp_path / "private-mapping.json").write_text(json.dumps({identity: {"phase": "calibration"}}))
    (tmp_path / "bundles.json").write_text(
        json.dumps([{"id": identity, "answer": {"status": "grounded", "claims": [{}, {}]}}])
    )
    (tmp_path / "judge-v1").mkdir()
    (tmp_path / "judge-v1/provisional-summary-R01.json").write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "id": identity,
                        "status": "valid_provisional",
                        "verdict": {
                            "correctness": "pass",
                            "completeness": "pass",
                            "abstention": "unknown",
                            "claims": [
                                {"claim_index": 1, "support": "fail"},
                                {"claim_index": 0, "support": "pass"},
                            ],
                        },
                    }
                ]
            }
        )
    )
    review = HumanReview.model_validate_json(
        json.dumps(
            {
                "authority": "human-reviewed",
                "reviewer": "fixture reviewer",
                "reviewed_without_judge_grades": True,
                "decisions": [
                    {
                        "id": identity,
                        "phase": "calibration",
                        "correctness": "pass",
                        "completeness": "pass",
                        "claim_support": ["pass", "fail"],
                        "abstention_or_conflict": "unknown",
                        "evidence_and_rationale": "Reviewed exact claims",
                        "expected_propositions_approved": True,
                    }
                ],
            }
        )
    )

    result = compare(tmp_path, review)

    assert result["phases"]["calibration"]["exact_agreement"] == 1.0
    assert result["phases"]["calibration"]["false_acceptances"] == 0
    assert result["phases"]["audit"]["admission"] == "unresolved_or_failed"
