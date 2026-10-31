"""Real CLI budget administration and opt-in compatible saved-run aggregation."""

import json
from decimal import Decimal

import pytest

from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.evaluation.reporting import evaluate_runs
from extraction_service.execution.budget.ledger import BudgetLedger

from .conftest import ControlledService


@pytest.mark.parametrize("overlap", [False, True])
def test_cli_raise_and_compatible_aggregation(service: ControlledService, overlap: bool) -> None:
    corpus = load_corpus(service.project)
    first_id = "B02-S003-PO01"
    second_id = first_id if overlap else "B02-S002-PO01"
    service.responses = [json.dumps(corpus.gold[first_id]), json.dumps(corpus.gold[second_id])]
    initialized = service.invoke("budget-init", "--opening-spend", "0.1", "--evidence", "Test")
    first = service.invoke("run", "--run-id", "old-cap", "--input", first_id)
    old_path = service.project / "results/runs/old-cap/manifest.json"
    original = old_path.read_bytes()

    with pytest.raises(ValueError, match="audited cap raise"):
        evaluate_runs(service.project, ["old-cap"], allow_budget_revision=True)

    path = service.project / "config/experiments.yaml"
    config = load_experiment(path)
    config = config.model_copy(
        update={"execution": config.execution.model_copy(update={"api_budget_usd": 10.0})}
    )
    path.write_text(config.model_dump_json())
    mismatch = service.invoke("budget-show")
    raised = service.invoke(
        "budget-raise", "--expected-budget", "4.5", "--evidence", "Test user approval"
    )
    second = service.invoke("run", "--run-id", "new-cap", "--input", second_id)

    assert (
        initialized.returncode == first.returncode == raised.returncode == second.returncode == 0
    ), initialized.stderr + first.stderr + raised.stderr + second.stderr
    assert mismatch.returncode != 0
    assert old_path.read_bytes() == original
    assert len(evaluate_runs(service.project, ["old-cap", "new-cap"])["variants"]) == 2

    if overlap:
        with pytest.raises(ValueError, match="Duplicate input observation"):
            evaluate_runs(service.project, ["old-cap", "new-cap"], allow_budget_revision=True)
        return

    before_evaluation = len(service.requests)
    evaluated = service.invoke("evaluate", "old-cap", "new-cap", "--allow-budget-revision")

    assert evaluated.returncode == 0, evaluated.stderr
    report = json.loads(evaluated.stdout)
    assert len(report["variants"]) == 1
    assert report["variants"][0]["quality"]["exact_documents"] == 2
    assert {r["original_execution_policy"]["api_budget_usd"] for r in report["runs"]} == {4.5, 10.0}
    assert len(service.requests) == before_evaluation

    config = config.model_copy(
        update={
            "execution": config.execution.model_copy(update={"request_timeout_seconds": 1810.0})
        }
    )
    path.write_text(config.model_dump_json())
    service.responses.append(json.dumps(corpus.gold["B02-S012-PO01"]))
    changed = service.invoke("run", "--run-id", "changed-deadline", "--input", "B02-S012-PO01")
    assert changed.returncode == 0
    different = evaluate_runs(
        service.project, ["old-cap", "new-cap", "changed-deadline"], allow_budget_revision=True
    )
    assert len(different["variants"]) == 2

    snapshot = BudgetLedger(service.project, config.execution).snapshot()
    backup = (
        service.project
        / "results/budget-policy"
        / f"{snapshot.policy_revisions[0].previous_sha256}.json"
    )
    backup.write_text("{tampered}")
    with pytest.raises(ValueError, match="backup hash"):
        evaluate_runs(service.project, ["old-cap", "new-cap"], allow_budget_revision=True)

    assert snapshot.accounted_usd == Decimal("0.1")


def test_revised_native_profile_forwards_context_and_output_through_correction(
    service: ControlledService, monkeypatch: pytest.MonkeyPatch
) -> None:
    service.native = True
    monkeypatch.setenv("HW01_SETUP_CONTEXT_LENGTH", "49152")
    _, processes = service.reply("/api/ps", None)
    processes["models"][0]["context_length"] = 49152
    service.replacements["/api/ps"] = processes
    corpus = load_corpus(service.project)
    service.responses = ["{}", json.dumps(corpus.gold["B02-S003-PO01"])]

    result = service.invoke(
        "run",
        "--config",
        "config/matrix.yaml",
        "--model",
        "local",
        "--input",
        "B02-S003-PO01",
        "--run-id",
        "revised-native",
    )

    assert result.returncode == 0, result.stderr
    generations = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload and not payload.get("_debug_render_only")
    ]
    assert len(generations) == 2
    assert all(payload["think"] is False for payload in generations)
    assert all(payload["options"]["num_ctx"] == 49152 for payload in generations)
    assert all(payload["options"]["num_predict"] == 16384 for payload in generations)
    assert not any("completions" in path for path, _, _ in service.requests)
