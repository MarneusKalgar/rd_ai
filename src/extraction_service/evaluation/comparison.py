"""Failure-inclusive paired analysis; synthetic review anchors never become gold."""

from collections import Counter
from pathlib import Path
from typing import Any, Literal

from extraction_service.application.persistence import reload_records
from extraction_service.archiving.files import confined, digest
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.protocol import load_protocol, verify_sources
from extraction_service.evaluation.reporting import evaluate_runs
from extraction_service.evaluation.scoring import ExtractionScore, score_extraction
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject, JsonValue
from extraction_service.runtime_types import StrictModel


class ReviewAnchor(StrictModel):
    authority: Literal["synthetic", "human_reviewed"]
    reference: str
    correct_before: bool | None
    correct_after: bool | None
    changed: bool
    claimed_support: bool
    source_supported: bool | None
    claimed_acceptance: bool


def review_metrics(anchors: list[ReviewAnchor]) -> dict[str, Any]:
    """Keep source support separate from correctness; unknown anchors cannot certify."""

    result: dict[str, Any] = {}
    for authority in ("synthetic", "human_reviewed"):
        selected = [a for a in anchors if a.authority == authority]
        correct = [a for a in selected if a.correct_before is True]
        support = [a for a in selected if a.claimed_support and a.source_supported is not None]
        acceptance = [a for a in selected if a.claimed_acceptance and a.correct_after is not None]
        result[authority] = {
            "anchors": len(selected),
            "unnecessary_changes": sum(a.changed for a in correct),
            "correct_before_anchors": len(correct),
            "no_change_correct": sum(not a.changed for a in correct),
            "harmful_changes": sum(a.changed and a.correct_after is False for a in correct),
            "false_support": sum(a.source_supported is False for a in support),
            "support_claims_anchored": len(support),
            "false_acceptance": sum(a.correct_after is False for a in acceptance),
            "acceptance_claims_anchored": len(acceptance),
            "false_acceptance_rate": None
            if not acceptance
            else sum(a.correct_after is False for a in acceptance) / len(acceptance),
            "unknown_claims": sum(
                (a.claimed_support and a.source_supported is None)
                or (a.claimed_acceptance and a.correct_after is None)
                for a in selected
            ),
        }

    return result


def paired_score(
    expected: JsonObject,
    before: JsonObject | None,
    after: JsonObject | None,
    contract: ExtractionContract,
) -> dict[str, Any]:
    """Compare gold paths only; retain extra-row penalties in both primary scores."""

    left = score_extraction(expected, before, contract)
    right = score_extraction(expected, after, contract)
    gold_paths: set[str] = set()
    gold_paths.update(f"/{key}" for key in expected if key != "lineItems")
    rows = expected["lineItems"]
    assert isinstance(rows, list)
    for index, row in enumerate(rows):
        assert isinstance(row, dict)
        gold_paths.update(f"/lineItems/{index}/{key}" for key in row)
    transitions: Counter[str] = Counter()
    for path in gold_paths:
        was_correct = path not in left.mismatched_paths
        is_correct = path not in right.mismatched_paths
        label = (
            ("both_correct" if is_correct else "correct_to_wrong")
            if was_correct
            else ("wrong_to_correct" if is_correct else "both_wrong")
        )
        transitions[label] += 1

    nullability = {}
    expected_values = _gold_values(expected)
    for name, value, score in (("before", before, left), ("after", after, right)):
        actual_values = {} if not score.schema_valid or value is None else _gold_values(value)
        nullability[name] = [
            path
            for path, item in expected_values.items()
            if path in actual_values and (item is None) != (actual_values[path] is None)
        ]

    return {
        "before": left.model_dump(),
        "after": right.model_dump(),
        "gold_field_transitions": {
            k: transitions[k]
            for k in ("both_correct", "correct_to_wrong", "wrong_to_correct", "both_wrong")
        },
        "present_null_error_paths": nullability,
    }


def _gold_values(value: JsonObject) -> dict[str, JsonValue]:
    """Flatten contract-valid field paths without semantic row alignment."""

    fields = {f"/{key}": item for key, item in value.items() if key != "lineItems"}
    rows = value["lineItems"]
    assert isinstance(rows, list)
    for index, row in enumerate(rows):
        assert isinstance(row, dict)
        for key, item in row.items():
            fields[f"/lineItems/{index}/{key}"] = item

    return fields


def error_tags(score: ExtractionScore) -> list[str]:
    """Mechanical overlapping tags do not assert semantic error causes."""

    tags = []
    if not score.schema_valid:
        tags.append("unusable")
    if score.headers.correct < score.headers.total:
        tags.append("wrong_header")
    if score.lines.correct < score.lines.total:
        tags.append("wrong_line_field")
    if score.extra_lines:
        tags.append("extra_row")
    if score.missing_lines:
        tags.append("missing_row")

    return tags


def compare_experiment(project: Path, filename: str, source: str) -> dict[str, Any]:
    """Verify both populations and reuse the original read-only aggregate evaluator."""

    protocol = load_protocol(project, filename)
    verify_sources(project, protocol, source)
    corpus = load_corpus(project)
    sides = {}
    records = {}
    for name, selection in protocol.selections.items():
        report = evaluate_runs(
            project,
            list(selection.runs),
            source_dir=source,
            budget_policy_file=protocol.public_budget_policy.path,
        )
        if len(report["variants"]) != 1:
            raise ValueError("Side contains multiple execution variants")
        variant = report["variants"][0]
        if variant["identity"] != selection.identity or set(variant["input_ids"]) != set(
            protocol.input_ids
        ):
            raise ValueError("Observed variant differs from protocol")
        sides[name] = variant
        records[name] = {
            record.input_id: record
            for run in selection.runs
            for record in reload_records(confined(project, f"{source}/{run}"))[1]
        }
    cases = []
    outcomes: dict[str, Counter[str]] = {"v1": Counter(), "v2": Counter()}
    for identifier in protocol.input_ids:
        left, right = records["v1"][identifier], records["v2"][identifier]
        expected = corpus.gold.get(identifier)
        pair = (
            None
            if expected is None
            else paired_score(expected, left.extraction, right.extraction, corpus.contract)
        )
        tags = None
        if pair is not None:
            tags = {
                name: error_tags(ExtractionScore.model_validate(pair[name]))
                for name in ("before", "after")
            }
            for name in ("before", "after"):
                if pair["present_null_error_paths"][name]:
                    tags[name].append("present_null_error")
            for name, status, score_name in (
                ("v1", left.status.value, "before"),
                ("v2", right.status.value, "after"),
            ):
                score = pair[score_name]
                outcome = (
                    "not_attempted"
                    if status == "not_attempted"
                    else (
                        "unusable"
                        if not score["schema_valid"]
                        else ("valid_exact" if score["exact"] else "valid_inexact")
                    )
                )
                outcomes[name][outcome] += 1
        cases.append(
            {
                "input_id": identifier,
                "gold": expected is not None,
                "before_status": left.status.value,
                "after_status": right.status.value,
                "paired": pair,
                "semantic_cause": "unreviewed",
                "error_tags": tags,
            }
        )
    accuracy = [sides[name]["quality"]["overall"]["accuracy"] for name in ("v1", "v2")]
    return {
        "version": "paired-evaluation-v1",
        "experiment_id": protocol.experiment_id,
        "protocol_sha256": digest(confined(project, filename)),
        "implementation": {
            name: digest(Path(__file__).parent / name)
            for name in (
                "protocol.py",
                "comparison.py",
                "experiment.py",
                "scoring.py",
                "reporting.py",
                "metrics.py",
                "budget_policy.py",
            )
        },
        "bindings": {
            key: getattr(protocol, key).model_dump()
            for key in ("exposure", "rubric", "controls", "public_budget_policy")
        },
        "claim_scope": protocol.claim_scope,
        "model_calls": 0,
        "inference_performed": False,
        "selected_inputs": len(cases),
        "gold_inputs": len(corpus.gold),
        "sides": sides,
        "accuracy_delta_percentage_points": (accuracy[1] - accuracy[0]) * 100,
        "cases": cases,
        "primary_outcomes_gold_only": {name: dict(counts) for name, counts in outcomes.items()},
        "review": review_metrics([]),
        "human_semantic_review": "unavailable; no new reviewed anchors",
        "transition_population": "gold field paths only; extra rows remain in primary scores",
    }
