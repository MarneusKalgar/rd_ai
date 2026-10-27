"""Portable grouping never needs a private ledger or changes generation controls."""

import hashlib
import json
from copy import deepcopy
from typing import Any

import pytest

from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.budget_policy import EvaluationBudgetPolicy
from extraction_service.evaluation.reporting import evaluate_runs
from extraction_service.evaluation.reproduce import check_report_tables
from extraction_service.execution.budget.ledger import BudgetLedger

from .conftest import ControlledService


def test_public_policy_reproduces_original_aggregation_without_ledger(
    service: ControlledService,
) -> None:
    corpus = load_corpus(service.project)
    first_id, second_id = "B02-S003-PO01", "B02-S002-PO01"
    service.responses = [json.dumps(corpus.gold[first_id]), json.dumps(corpus.gold[second_id])]
    initialized = service.invoke("budget-init", "--opening-spend", "0", "--evidence", "Test")
    first = service.invoke("run", "--run-id", "old-cap", "--input", first_id)
    path = service.project / "config/experiments.yaml"
    config = load_experiment(path)
    config = config.model_copy(
        update={"execution": config.execution.model_copy(update={"api_budget_usd": 10.0})}
    )
    path.write_text(config.model_dump_json())
    raised = service.invoke("budget-raise", "--expected-budget", "4.5", "--evidence", "Test")
    second = service.invoke("run", "--run-id", "new-cap", "--input", second_id)

    assert initialized.returncode == first.returncode == raised.returncode == second.returncode == 0
    expected = evaluate_runs(service.project, ["old-cap", "new-cap"], allow_budget_revision=True)
    snapshot = BudgetLedger(service.project, config.execution).snapshot()
    policy = EvaluationBudgetPolicy(
        source_archive_sha256="a" * 64,
        evidence_bundle="test-evidence",
        budget_usd=snapshot.budget_usd,
        matrix_reserve_usd=snapshot.matrix_reserve_usd,
        policy_revisions=snapshot.policy_revisions,
        manifests={run["run_id"]: run["manifest_sha256"] for run in expected["runs"]},
    )
    policy_path = service.project / "config/evaluation-policy.json"
    policy_path.write_text(policy.model_dump_json())
    ledger = service.project / "results/budget-ledger.json"
    ledger.unlink()
    backup = (
        service.project
        / "results/budget-policy"
        / f"{snapshot.policy_revisions[0].previous_sha256}.json"
    )
    backup.unlink()
    requests_before = len(service.requests)

    result = service.invoke(
        "evaluate", "old-cap", "new-cap", "--budget-policy", "config/evaluation-policy.json"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    actual = json.loads(result.stdout)
    assert (
        actual.pop("public_budget_policy_sha256")
        == hashlib.sha256(policy_path.read_bytes()).hexdigest()
    )
    assert actual == expected
    assert actual["variants"][0]["quality"]["overall"]["correct"] == 30
    assert not ledger.exists() and not backup.exists()
    assert len(service.requests) == requests_before

    with pytest.raises(ValueError, match="Choose local ledger audit"):
        evaluate_runs(
            service.project,
            ["old-cap"],
            allow_budget_revision=True,
            budget_policy_file="config/evaluation-policy.json",
        )

    changed = policy.model_copy(update={"manifests": {"old-cap": "b" * 64}})
    policy_path.write_text(changed.model_dump_json())

    with pytest.raises(ValueError, match="manifest is outside"):
        evaluate_runs(
            service.project, ["old-cap"], budget_policy_file="config/evaluation-policy.json"
        )


@pytest.mark.parametrize("defect", ["decrease", "gap", "final-cap", "reserve"])
def test_public_policy_rejects_invalid_revision_chain(defect: str) -> None:
    policy: dict[str, Any] = {
        "source_archive_sha256": "a" * 64,
        "evidence_bundle": "evidence",
        "budget_usd": "10",
        "matrix_reserve_usd": "3.5",
        "manifests": {"run": "b" * 64},
        "policy_revisions": [
            {
                "previous_budget_usd": "4.5",
                "budget_usd": "10",
                "previous_sha256": "c" * 64,
                "evidence": "Approval",
                "observed_at": "2026-10-23",
            }
        ],
    }
    assert EvaluationBudgetPolicy.model_validate_json(json.dumps(policy)).budget_usd == 10

    if defect == "decrease":
        policy["policy_revisions"][0]["budget_usd"] = "4"
    elif defect == "gap":
        next_revision = deepcopy(policy["policy_revisions"][0])
        next_revision.update(previous_budget_usd="9", budget_usd="12")
        policy["policy_revisions"].append(next_revision)
        policy["budget_usd"] = "12"
    elif defect == "final-cap":
        policy["budget_usd"] = "11"
    else:
        policy["matrix_reserve_usd"] = "4.5"

    with pytest.raises(ValueError, match="Evaluation"):
        EvaluationBudgetPolicy.model_validate_json(json.dumps(policy))


@pytest.mark.parametrize("defect", [None, "quality", "latency", "cost", "usage", "field"])
def test_report_checker_detects_changed_matrix_claims(defect: str | None) -> None:
    score = {"correct": 2, "total": 3, "accuracy": 2 / 3, "present_correct": 1, "null_correct": 1}
    row = {
        "model": "local",
        "prompt": "v2",
        "sampling": "baseline-16384",
        "quality": {
            "overall": score,
            "headers": score,
            "lines": score,
            "exact_documents": 0,
            "extra_lines": 0,
            "missing_lines": 1,
            "per_field": {"buyerName": {"correct": 1, "total": 2}},
        },
        "operational": {
            "first_valid": 1,
            "final_valid": 1,
            "latency_p50_ms": 1000,
            "latency_p95_ms": 2000,
            "total_api_cost_usd": "0",
            "api_cost_per_1000_attempted_inputs_usd": "0",
        },
        "processing_seconds": 3.0,
        "usage": {"input_tokens": {"known_sum": 20}, "output_tokens": {"known_sum": 10}},
    }
    report = (
        "| G v2 B | 2/3 | 66.67% | 0 | 2/3 | 2/3 | 1 | 1 | 0 / 1 |\n"
        "| G v2 B | 1/1 | 1.000 / 2.000 | 3.000 | $0 | $0 |\n"
        "| G v2 B | 20 | 10 |\n| buyerName | 1/2 |"
    )
    mutations = {
        "quality": ("66.67%", "100.00%"),
        "latency": ("1.000", "0.000"),
        "cost": ("$0 | $0", "$1 | $0"),
        "usage": ("20 | 10", "21 | 10"),
        "field": ("buyerName | 1/2", "buyerName | 2/2"),
    }

    if defect is None:
        check_report_tables(report, [row])
    else:
        changed = report.replace(*mutations[defect])

        with pytest.raises(ValueError, match="Report"):
            check_report_tables(changed, [row])
