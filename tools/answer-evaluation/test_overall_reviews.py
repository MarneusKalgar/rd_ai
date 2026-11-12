"""Overall feedback must retain uncertainty and never manufacture granular labels."""

import json
from pathlib import Path

import pytest
from overall_reviews import JUDGES, LABELS, finalize


def fixture(output: Path) -> None:
    identities = ["a" * 16, "b" * 16, "c" * 16, "d" * 16]
    labels = ["pass", "partly_correct_missing_details", "not_pass_no_answer", "pass"]
    mapping = {
        key: {"phase": "calibration" if index < 2 else "audit"}
        for index, key in enumerate(identities)
    }
    (output / LABELS).write_text(
        json.dumps(
            {
                "items": {
                    key: {"phase": mapping[key]["phase"], "label": label, "origin": "User decision"}
                    for key, label in zip(identities, labels, strict=True)
                },
                "counts": {"pass": 2, "partly_correct_missing_details": 1, "not_pass_no_answer": 1},
            }
        )
    )
    (output / "private-mapping.json").write_text(json.dumps(mapping))
    (output / "bundles.json").write_text(
        json.dumps(
            [
                {"id": key, "answer": None if index == 2 else {}, "operational_outcome": "saved"}
                for index, key in enumerate(identities)
            ]
        )
    )
    (output / "judge-v1").mkdir()
    (output / JUDGES).write_text(
        json.dumps(
            {
                "rows": [
                    {
                        "id": key,
                        "status": "valid_provisional",
                        "verdict": {
                            "correctness": "unknown" if index == 0 else "pass",
                            "completeness": "pass",
                        },
                    }
                    for index, key in enumerate(identities)
                    if index != 2
                ]
            }
        )
    )


def test_overall_review_preserves_unknown_ungraded_and_disagreement(tmp_path: Path) -> None:
    fixture(tmp_path)

    result = finalize(tmp_path)

    assert result["coverage"] == 4
    assert [row["comparison"] for row in result["rows"]] == [
        "unknown",
        "disagreement",
        "ungraded",
        "agreement",
    ]
    assert result["phases"]["calibration"]["judge_accepted_human_not_accepted"] == 1
    assert result["phases"]["audit"]["human_items"] == 2
    assert all(row["granular_dimensions"] == "unassessed" for row in result["rows"])
    assert result["semantic_adoption"] == "unresolved"


@pytest.mark.parametrize("defect", ["missing", "phase", "counts", "label"])
def test_overall_review_rejects_changed_population_or_labels(tmp_path: Path, defect: str) -> None:
    fixture(tmp_path)
    path = tmp_path / LABELS
    raw = json.loads(path.read_text())
    if defect == "missing":
        del raw["items"]["a" * 16]
    elif defect == "phase":
        raw["items"]["a" * 16]["phase"] = "audit"
    elif defect == "counts":
        raw["counts"]["pass"] = 3
    else:
        raw["items"]["a" * 16]["label"] = "looks fine"
    path.write_text(json.dumps(raw))

    with pytest.raises(
        ValueError,
        match={
            "missing": "exact sampled population",
            "phase": "phase differs",
            "counts": "counts differ",
            "label": "Input should be",
        }[defect],
    ):
        finalize(tmp_path)
