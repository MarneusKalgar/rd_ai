"""Independent arithmetic and real saved-run evaluation, without model services."""

import hashlib
import json
from copy import deepcopy

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.metrics import operational_metrics, percentile
from extraction_service.evaluation.scoring import FieldScore, combine_scores, score_extraction
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject

from .conftest import ControlledService

INPUT: str = "B02-S003-PO01"


def test_exact_scoring_counts(contract: ExtractionContract, gold: JsonObject) -> None:
    score = score_extraction(gold, deepcopy(gold), contract)

    assert score.exact and score.schema_valid
    assert score.overall.correct == score.overall.total == 15
    assert score.headers.total == 7 and score.lines.total == 8
    assert score.overall.present_total == score.overall.present_correct == 10
    assert score.overall.null_total == score.overall.null_correct == 5
    assert score.mismatched_paths == []


@pytest.mark.parametrize("actual", [None, {}, {"paymentTerms": None}])
def test_unusable_output_never_matches_expected_nulls(
    contract: ExtractionContract,
    gold: JsonObject,
    actual: JsonObject | None,
) -> None:
    score = score_extraction(gold, actual, contract)

    assert not score.schema_valid and not score.exact
    assert score.overall.total == 15 and score.overall.correct == 0
    assert score.overall.null_total == 5 and score.overall.null_correct == 0
    assert score.missing_lines == 1


@pytest.mark.parametrize(
    "defect", ["wrong-value", "decimal-format", "extra-line", "missing-line", "reordered"]
)
def test_field_and_order_errors_are_penalized(
    contract: ExtractionContract,
    gold: JsonObject,
    defect: str,
) -> None:
    expected = deepcopy(gold)
    actual = deepcopy(gold)
    rows = actual["lineItems"]
    assert isinstance(rows, list) and isinstance(rows[0], dict)
    expected_correct = 14
    expected_total = 15
    expected_missing = expected_extra = 0

    if defect == "wrong-value":
        actual["purchaseOrderNumber"] = "wrong"
    elif defect == "decimal-format":
        rows[0]["buyerProductQuantity"] = "159.0"
    elif defect == "extra-line":
        rows.append(deepcopy(rows[0]))
        expected_correct, expected_total, expected_extra = 15, 23, 1
    else:
        second = deepcopy(rows[0])
        second["buyerProductQuantity"] = "3"
        expected_rows = expected["lineItems"]
        assert isinstance(expected_rows, list)
        expected_rows.append(second)

        if defect == "missing-line":
            expected_correct, expected_total, expected_missing = 15, 23, 1
        else:
            rows.insert(0, second)
            expected_correct, expected_total = 21, 23

    score = score_extraction(expected, actual, contract)

    assert score.schema_valid and not score.exact
    assert (score.overall.correct, score.overall.total) == (expected_correct, expected_total)
    assert (score.missing_lines, score.extra_lines) == (expected_missing, expected_extra)
    assert score.mismatched_paths


def test_percentile_population_and_boundaries() -> None:
    assert percentile([], 0.95) is None
    assert percentile([30.0, 10.0, 20.0], 0.5) == 20.0
    assert percentile([30.0, 10.0, 20.0], 0.95) == 30.0
    assert percentile([5.0], 0.95) == 5.0

    with pytest.raises(ValueError, match="quantile"):
        percentile([1.0], 0)


def test_saved_correction_is_scored_offline(service: ControlledService, gold: JsonObject) -> None:
    service.responses = ["{}", json.dumps(gold)]
    completed = service.invoke("run", "--run-id", "scored", "--input", INPUT)
    before_requests = len(service.requests)

    result = service.invoke("evaluate", "scored")

    assert completed.returncode == result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert len(report["variants"]) == 1
    variant = report["variants"][0]
    quality = variant["quality"]
    assert quality["gold_cases"] == quality["exact_documents"] == 1
    assert quality["overall"]["correct"] == quality["overall"]["total"] == 15
    metrics = variant["operational"]
    assert metrics["physical_requests"] == 2
    assert metrics["first_valid_rate"] == 0.0 and metrics["final_valid_rate"] == 1.0
    assert metrics["correction_rate"] == 1.0
    assert metrics["total_api_cost_usd"] == "0"
    assert len(service.requests) == before_requests
    assert not (service.project / "results/budget-ledger.json").exists()


def test_paid_unknown_cost_and_stopped_inputs_remain_visible(service: ControlledService) -> None:
    service.coverage([INPUT])
    initialized = service.invoke("budget-init", "--opening-spend", "0", "--evidence", "Test")
    service.generation_status = 400
    second = next(
        identifier for identifier in load_corpus(service.project).gold if identifier != INPUT
    )
    completed = service.invoke(
        "run",
        "--run-id",
        "failed-cost",
        "--model",
        "provider",
        "--input",
        INPUT,
        "--input",
        second,
        "--allow-provider",
        "--coverage",
        "config/coverage.json",
    )

    result = service.invoke("evaluate", "failed-cost")

    assert initialized.returncode == 0 and completed.returncode == 3
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["runs"][0]["state"] == "incomplete"
    metrics = report["variants"][0]["operational"]
    assert metrics["selected_inputs"] == 2
    assert metrics["attempted_inputs"] == metrics["not_attempted_inputs"] == 1
    assert metrics["latency_sample_count"] == 1
    assert metrics["unknown_cost_requests"] == 1
    assert metrics["known_api_cost_usd"] == "0"
    assert metrics["total_api_cost_usd"] is None
    assert metrics["api_cost_per_1000_attempted_inputs_usd"] is None
    assert metrics["final_valid_rate"] == 0.0
    quality = report["variants"][0]["quality"]
    assert quality["gold_cases"] == 2 and quality["overall"]["correct"] == 0


def test_duplicate_observations_are_not_counted_twice(
    service: ControlledService, gold: JsonObject
) -> None:
    service.responses = [json.dumps(gold), json.dumps(gold)]
    first = service.invoke("run", "--run-id", "one", "--input", INPUT)
    second = service.invoke("run", "--run-id", "two", "--input", INPUT)

    duplicate = service.invoke("evaluate", "one", "two")

    assert first.returncode == second.returncode == 0
    assert duplicate.returncode == 2 and json.loads(duplicate.stdout) == {
        "setup_error": "ValueError"
    }


def test_empty_metrics_have_no_fabricated_latency() -> None:
    result = operational_metrics([])

    assert result["first_valid_rate"] is None
    assert result["latency_p50_ms"] is result["latency_p95_ms"] is None
    assert result["api_cost_per_1000_attempted_inputs_usd"] is None


def test_scoring_aggregates_field_counts_not_document_percentages() -> None:
    result = combine_scores([FieldScore(correct=1, total=1), FieldScore(correct=1, total=9)])

    assert result.correct == 2 and result.total == 10
    assert result.accuracy == 0.2


@pytest.mark.parametrize("defect", ["saved-byte-corruption", "different-approved-input"])
def test_evaluation_rejects_corrupted_or_mismatched_evidence(
    service: ControlledService,
    gold: JsonObject,
    defect: str,
) -> None:
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "tampered", "--input", INPUT)
    assert result.returncode == 0
    directory = service.project / "results/runs/tampered"
    manifest_path = directory / "manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    key = manifest["jobs"][0]["key"]
    record_path = directory / manifest["records"][key]

    if defect == "saved-byte-corruption":
        record_path.write_bytes(record_path.read_bytes() + b" ")
        expected = "Saved record hash mismatch"
    else:
        record = json.loads(record_path.read_bytes())
        record["input_sha256"] = "a" * 64
        manifest["jobs"][0]["input_sha256"] = "a" * 64
        record_path.write_text(json.dumps(record))
        manifest["record_sha256"][key] = hashlib.sha256(record_path.read_bytes()).hexdigest()
        manifest_path.write_text(json.dumps(manifest))
        reload_records(directory)
        expected = "Evaluation input differs from the approved corpus"

    from extraction_service.evaluation.reporting import evaluate_runs

    with pytest.raises(ValueError, match=expected):
        evaluate_runs(service.project, ["tampered"])
