"""Describe matched rubric-pass yield without requiring human endorsement."""

from typing import Any


def improvement(rows: list[dict[str, Any]], cases: dict[str, Any]) -> dict[str, Any]:
    """Retain every original job and separate authored answerability strata.

    Partitions use the frozen case expected status, never observed arm success.
    They describe task-level answerability with applicable evidence, not what a
    no-context model can know. Skips, errors and unknown grades earn no pass.
    """

    populations: dict[str, dict[str, Any]] = {}
    seen: set[str] = set()
    memberships: dict[str, set[str]] = {}
    for row in rows:
        key = row["key"]
        if key in seen:
            raise ValueError("Repeated comparison job")
        seen.add(key)
        case_id, arm = key.split("/")
        memberships.setdefault(arm, set()).add(case_id)
        case = cases[case_id]
        partition = "answerable" if case["expected_status"] == "evidence_found" else "negative"
        for name in ("all", partition):
            stats = populations.setdefault(name, {}).setdefault(
                arm,
                {"jobs": 0, "graded": 0, "rubric_passes": 0, "outcomes": {}, "answer_statuses": {}},
            )
            stats["jobs"] += 1
            outcome = row["operational_outcome"]
            stats["outcomes"][outcome] = stats["outcomes"].get(outcome, 0) + 1
            status = row["answer_status"]
            stats["answer_statuses"][status] = stats["answer_statuses"].get(status, 0) + 1
            grade = row["semantic_review"]
            if grade["status"] == "valid_provisional":
                stats["graded"] += 1
                verdict = grade["verdict"]
                stats["rubric_passes"] += (
                    verdict["correctness"] == "pass" and verdict["completeness"] == "pass"
                )
    if set(memberships) != {"none", "bm25", "vector"} or any(
        members != set(cases) for members in memberships.values()
    ):
        raise ValueError("Comparison requires all cases in each matched arm")
    for arms in populations.values():
        baseline = arms["none"]["rubric_passes"] / arms["none"]["jobs"]
        for stats in arms.values():
            rate = stats["rubric_passes"] / stats["jobs"]
            stats["rubric_pass_yield_percent"] = 100 * rate
            stats["delta_vs_none_percentage_points"] = 100 * (rate - baseline)
    return {
        "metric": "provisional judge-assessed rubric-pass yield",
        "populations": populations,
        "partition_rule": "Frozen expected_status=evidence_found vs other expected statuses",
        "human_review": "optional complementary evidence; not a prerequisite for this metric",
        "limitations": (
            "Development fixtures and uncalibrated judge; abstentions can pass. "
            "Not validated accuracy, causal generalization or human satisfaction."
        ),
    }
