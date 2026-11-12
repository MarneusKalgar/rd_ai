"""Verify fixed denominators, paired membership and separation of safety controls."""

from typing import Any

import pytest
from improvement import improvement


def population() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    cases = {
        "Q01": {"expected_status": "evidence_found"},
        "Q02": {"expected_status": "insufficient_evidence"},
    }
    rows = []
    for arm in ("none", "bm25", "vector"):
        for case in cases:
            skip = arm == "bm25" and case == "Q02"
            rows.append(
                {
                    "key": f"{case}/{arm}",
                    "answer_status": "absent" if skip else "insufficient_evidence",
                    "operational_outcome": "skip" if skip else "valid",
                    "semantic_review": {"status": "unreviewed"}
                    if skip
                    else {
                        "status": "valid_provisional",
                        "verdict": {
                            "correctness": "pass" if arm != "none" else "unknown",
                            "completeness": "pass",
                        },
                    },
                }
            )
    return rows, cases


def test_fixed_denominators_and_negative_control_partition() -> None:
    rows, cases = population()

    result = improvement(rows, cases)["populations"]

    assert result["all"]["bm25"]["rubric_pass_yield_percent"] == 50
    assert result["all"]["vector"]["delta_vs_none_percentage_points"] == 100
    assert result["negative"]["bm25"]["jobs"] == 1
    assert result["negative"]["bm25"]["graded"] == 0
    assert result["answerable"]["none"]["rubric_passes"] == 0
    assert result["all"]["bm25"]["outcomes"] == {"valid": 1, "skip": 1}


def test_reject_changed_membership_and_duplicate_jobs() -> None:
    rows, cases = population()

    with pytest.raises(ValueError, match="each matched arm"):
        improvement(rows[:-1], cases)
    with pytest.raises(ValueError, match="Repeated comparison job"):
        improvement(rows + [rows[0]], cases)
