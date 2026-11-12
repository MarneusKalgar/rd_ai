"""Finalize explicit overall human labels without inventing granular anchors."""

import json
from collections import Counter
from pathlib import Path
from typing import Annotated, Any, Literal

from prepare import OUTPUT
from pydantic import Field

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.retrieval.core import digest
from extraction_service.runtime_types import NonEmptyText, StrictModel

LABELS = "human-item-labels-20261112-R01.json"
JUDGES = "judge-v1/provisional-summary-R01.json"
Label = Literal[
    "pass",
    "partly_correct_missing_details",
    "not_pass_no_answer",
    "not_pass_no_answer_question_flagged_fake",
]


class ItemLabel(StrictModel):
    label: Label
    origin: NonEmptyText
    phase: Literal["calibration", "audit"]


class ItemLabels(StrictModel):
    items: dict[Annotated[str, Field(pattern=r"^[0-9a-f]{16}$")], ItemLabel]


def finalize(output: Path) -> dict[str, Any]:
    """Bind all sampled labels and report descriptive, criterion-limited agreement.

    Overall pass maps to accepted; partial and no-answer labels map to not
    accepted. Judge acceptance uses its existing correctness/completeness rule.
    This comparison neither evaluates human claim support nor admits the judge.
    """

    sources = {
        name: (output / name).read_bytes()
        for name in (LABELS, JUDGES, "private-mapping.json", "bundles.json")
    }
    raw = parse_json(sources[LABELS].decode())
    labels = ItemLabels.model_validate({"items": raw["items"]}).items
    mapping = json.loads(sources["private-mapping.json"])
    bundles = {item["id"]: item for item in json.loads(sources["bundles.json"])}
    if set(labels) != set(mapping):
        raise ValueError("Overall review does not cover the exact sampled population")
    counts = dict(Counter(item.label for item in labels.values()))
    if counts != raw["counts"]:
        raise ValueError("Declared human label counts differ")
    grades = {}
    for row in json.loads(sources[JUDGES])["rows"]:
        if row["id"] in grades:
            raise ValueError("Duplicate judge identity")
        grades[row["id"]] = row
    rows = []
    phases = {}
    for phase in ("calibration", "audit"):
        stats: Counter[str] = Counter()
        for identity, item in labels.items():
            if item.phase != mapping[identity]["phase"]:
                raise ValueError("Overall human review phase differs")
            if item.phase != phase:
                continue
            bundle = bundles[identity]
            grade = grades.get(identity)
            judgment = "ungraded"
            if grade and grade["status"] == "valid_provisional":
                if bundle["answer"] is None:
                    raise ValueError("Absent answer unexpectedly has a judge grade")
                verdict = grade["verdict"]
                decisions = (verdict["correctness"], verdict["completeness"])
                judgment = (
                    "accepted"
                    if decisions == ("pass", "pass")
                    else "not_accepted"
                    if "fail" in decisions
                    else "unknown"
                )
            human = "accepted" if item.label == "pass" else "not_accepted"
            stats["human_items"] += 1
            stats[item.label] += 1
            stats[f"judge_{judgment}"] += 1
            comparison = "ungraded"
            if judgment != "ungraded":
                comparison = (
                    "unknown"
                    if judgment == "unknown"
                    else ("agreement" if judgment == human else "disagreement")
                )
                stats[comparison] += 1
                if comparison == "disagreement":
                    stats[
                        "judge_accepted_human_not_accepted"
                        if judgment == "accepted"
                        else "judge_not_accepted_human_accepted"
                    ] += 1
            rows.append(
                {
                    "id": identity,
                    "phase": phase,
                    "human_label": item.label,
                    "human_reason": item.origin,
                    "overall_acceptance": human,
                    "operational_outcome": bundle["operational_outcome"],
                    "judge_acceptance": judgment,
                    "comparison": comparison,
                    "granular_dimensions": "unassessed",
                }
            )
        phases[phase] = dict(stats)
    return {
        "status": "complete overall human review of sampled items",
        "reviewer": "user in project chat",
        "coverage": len(rows),
        "counts": counts,
        "phases": phases,
        "source_sha256": {name: digest(data) for name, data in sources.items()},
        "criteria": "Acceptability vs judge correctness AND completeness; descriptive only",
        "review_independence": "not blind; aggregates and selected examples previously discussed",
        "granular_calibration": (
            "unresolved; claim support, abstention appropriateness and rubric approval unassessed"
        ),
        "semantic_adoption": "unresolved",
        "rows": rows,
    }


if __name__ == "__main__":
    result = finalize(OUTPUT)
    path = OUTPUT / "human-overall-review.json"
    content = json.dumps(result, indent=2) + "\n"
    if path.exists() and path.read_text() != content:
        raise ValueError("Refusing to replace a different finalized overall review")
    path.write_text(content)
    print(json.dumps({key: value for key, value in result.items() if key != "rows"}, indent=2))
