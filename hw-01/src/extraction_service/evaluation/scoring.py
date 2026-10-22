"""Exact field comparison; ordered lines remain positional, including duplicates."""

import json
from typing import Final

from pydantic import Field

from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject, JsonValue
from extraction_service.runtime_types import NonNegativeInt, StrictModel

LINE_ITEMS_FIELD: Final[str] = "lineItems"


class FieldScore(StrictModel):
    correct: NonNegativeInt = 0
    total: NonNegativeInt = 0
    present_correct: NonNegativeInt = 0
    present_total: NonNegativeInt = 0
    null_correct: NonNegativeInt = 0
    null_total: NonNegativeInt = 0

    @property
    def accuracy(self) -> float | None:
        return None if self.total == 0 else self.correct / self.total


class ExtractionScore(StrictModel):
    exact: bool
    schema_valid: bool
    overall: FieldScore
    headers: FieldScore
    lines: FieldScore
    fields: dict[str, FieldScore]
    expected_lines: NonNegativeInt
    missing_lines: NonNegativeInt
    extra_lines: NonNegativeInt
    mismatched_paths: list[str] = Field(default_factory=list)


def combine_scores(scores: list[FieldScore]) -> FieldScore:
    """Add counts before dividing; never average documents with unequal field counts."""

    return FieldScore(
        correct=sum(score.correct for score in scores),
        total=sum(score.total for score in scores),
        present_correct=sum(score.present_correct for score in scores),
        present_total=sum(score.present_total for score in scores),
        null_correct=sum(score.null_correct for score in scores),
        null_total=sum(score.null_total for score in scores),
    )


def _field_score(expected: JsonValue, actual: JsonValue, *, exists: bool) -> FieldScore:
    matches = exists and expected == actual
    present = expected is not None

    return FieldScore(
        correct=int(matches),
        total=1,
        present_correct=int(matches and present),
        present_total=int(present),
        null_correct=int(matches and not present),
        null_total=int(not present),
    )


def score_extraction(
    expected: JsonObject, actual: JsonObject | None, contract: ExtractionContract
) -> ExtractionScore:
    """Compare contract-valid values exactly, penalizing absent/extra ordered rows.

    Invalid output earns zero matches, even on expected-null fields. Extra rows
    add one wrong unit for every schema line field. No stripping, case folding,
    decimal coercion, product deduplication or content repair is performed.
    """

    if not contract.validate_json(json.dumps(expected)).is_valid:
        raise ValueError("Scoring requires contract-valid gold")

    valid = actual is not None and contract.validate_json(json.dumps(actual)).is_valid
    prediction = actual if valid and actual is not None else {}
    schema = contract.schema_for_provider()
    header_fields = [name for name in schema["required"] if name != LINE_ITEMS_FIELD]
    line_fields = schema["properties"][LINE_ITEMS_FIELD]["items"]["required"]
    expected_lines = expected[LINE_ITEMS_FIELD]
    actual_lines = prediction.get(LINE_ITEMS_FIELD, [])
    assert isinstance(expected_lines, list) and isinstance(actual_lines, list)
    fields: dict[str, list[FieldScore]] = {}
    mismatches = []
    header_scores = []
    line_scores = []

    for name in header_fields:
        score = _field_score(expected[name], prediction.get(name), exists=name in prediction)
        fields[name] = [score]
        header_scores.append(score)

        if not score.correct:
            mismatches.append(f"/{name}")

    for index in range(max(len(expected_lines), len(actual_lines))):
        gold_row = expected_lines[index] if index < len(expected_lines) else None
        actual_row = actual_lines[index] if index < len(actual_lines) else None

        for name in line_fields:
            if isinstance(gold_row, dict):
                score = _field_score(
                    gold_row[name],
                    actual_row.get(name) if isinstance(actual_row, dict) else None,
                    exists=isinstance(actual_row, dict) and name in actual_row,
                )
            else:
                score = FieldScore(total=1)

            fields.setdefault(f"{LINE_ITEMS_FIELD}/*/{name}", []).append(score)
            line_scores.append(score)

            if not score.correct:
                mismatches.append(f"/{LINE_ITEMS_FIELD}/{index}/{name}")

    headers = combine_scores(header_scores)
    lines = combine_scores(line_scores)

    return ExtractionScore(
        exact=valid and expected == actual,
        schema_valid=valid,
        overall=combine_scores([headers, lines]),
        headers=headers,
        lines=lines,
        fields={name: combine_scores(values) for name, values in fields.items()},
        expected_lines=len(expected_lines),
        missing_lines=max(0, len(expected_lines) - len(actual_lines)),
        extra_lines=max(0, len(actual_lines) - len(expected_lines)),
        mismatched_paths=mismatches,
    )
