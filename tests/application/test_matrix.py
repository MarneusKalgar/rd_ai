"""Matrix admission and full-corpus aggregation through controlled HTTP only."""

import json
from decimal import Decimal

import pytest

from extraction_service.application.admission import ProviderCoverage
from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus

from .conftest import ControlledService
from .test_provider_context import ARGUMENTS, prepare_coverage


def test_full_corpus_matrix_preserves_scoring_and_budget_scope(service: ControlledService) -> None:
    coverage = prepare_coverage(service)
    coverage["provider"]["server_context_stages"] = ["matrix"]
    path = service.project / "config/coverage.json"
    path.write_text(json.dumps(coverage))
    initialized = service.invoke(
        "budget-init", "--opening-spend", "0.597166", "--evidence", "Fictional prior spend"
    )
    corpus = load_corpus(service.project)
    fallback = next(iter(corpus.gold.values()))
    service.responses = [
        json.dumps(corpus.gold.get(source.input_id, fallback)) for source in corpus.inputs
    ]

    planned = service.invoke("plan-run", *ARGUMENTS, "--stage", "matrix")
    completed = service.invoke("run", *ARGUMENTS, "--stage", "matrix", "--run-id", "matrix-v1")
    before_evaluation = len(service.requests)
    evaluated = service.invoke("evaluate", "matrix-v1")

    assert initialized.returncode == planned.returncode == completed.returncode == 0, (
        initialized.stdout + planned.stdout + completed.stdout + completed.stderr
    )
    assert evaluated.returncode == 0, evaluated.stdout + evaluated.stderr
    plan = json.loads(planned.stdout)
    assert plan["primary_requests"] == 30 and plan["maximum_physical_requests"] == 120
    manifest, records = reload_records(service.project / "results/runs/matrix-v1")
    assert manifest.state.value == "complete" and manifest.stage == "matrix"
    assert len(records) == 30
    assert {record.input_id for record in records} == {source.input_id for source in corpus.inputs}
    assert all(record.prompt_id == "v1" and record.sampling_id == "baseline" for record in records)
    completions = [
        payload for endpoint, payload, _ in service.requests if endpoint.endswith("/completions")
    ]
    assert len(completions) == 30

    for payload in completions:
        assert payload is not None
        assert payload["model"] == "google/gemini-3.5-flash-lite"
        assert payload["plugins"] == [{"id": "context-compression", "enabled": False}]
        assert payload["provider"]["allow_fallbacks"] is False
        assert payload["max_tokens"] == 4096

    variant = json.loads(evaluated.stdout)["variants"][0]
    assert variant["quality"]["gold_cases"] == variant["quality"]["exact_documents"] == 10
    assert variant["quality"]["missing_gold_inputs"] == []
    assert variant["operational"]["selected_inputs"] == 30
    assert variant["operational"]["attempted_inputs"] == 30
    assert variant["operational"]["physical_requests"] == 30
    assert len(service.requests) == before_evaluation
    ledger = json.loads((service.project / "results/budget-ledger.json").read_bytes())
    assert Decimal(ledger["opening_spend_usd"]) == Decimal("0.597166")
    assert len(ledger["reservations"]) == 30
    assert all(entry["stage"] == "matrix" for entry in ledger["reservations"])
    charges = sum(Decimal(entry["billed_usd"]) for entry in ledger["reservations"])
    assert charges == Decimal("0.00030")
    budget = service.invoke("budget-show")
    assert budget.returncode == 0
    snapshot = json.loads(budget.stdout)
    assert Decimal(snapshot["accounted_usd"]) == Decimal("0.597466")
    assert Decimal(snapshot["protected_matrix_usd"]) == Decimal("3.49970")


@pytest.mark.parametrize("defect", ["no-opt-in", "smoke-only", "screening-only", "repetition"])
def test_matrix_context_needs_approved_stage_and_opt_in(
    service: ControlledService, defect: str
) -> None:
    coverage = prepare_coverage(service)
    coverage["provider"]["server_context_stages"] = ["matrix"]
    arguments = [*ARGUMENTS, "--stage", "matrix", "--input", "B02-S003-PO01"]

    if defect == "no-opt-in":
        arguments.remove("--allow-server-context")
    elif defect == "smoke-only":
        coverage["provider"].pop("server_context_stages")
    elif defect == "screening-only":
        coverage["provider"]["server_context_stages"] = ["screening"]
    else:
        arguments[arguments.index("matrix")] = "repetition"

    (service.project / "config/coverage.json").write_text(json.dumps(coverage))

    result = service.invoke("run", *arguments)

    assert result.returncode == 2, result.stdout + result.stderr
    assert service.requests == []
    assert not (service.project / "results/budget-ledger.json").exists()


def test_repetition_cannot_be_added_to_operator_coverage(service: ControlledService) -> None:
    coverage = prepare_coverage(service)["provider"]
    coverage["server_context_stages"] = ["matrix", "repetition"]

    with pytest.raises(ValueError, match="Provider context stages"):
        ProviderCoverage.model_validate_json(json.dumps(coverage))


def test_later_config_additions_preserve_original_phase_observations(
    service: ControlledService,
) -> None:
    corpus = load_corpus(service.project)
    first_input, second_input = "B02-S003-PO01", "B02-S002-PO01"
    service.responses = [
        json.dumps(corpus.gold[first_input]),
        json.dumps(corpus.gold[second_input]),
    ]
    first = service.invoke("run", "--run-id", "phase-one", "--input", first_input)
    manifest_path = service.project / "results/runs/phase-one/manifest.json"
    original_manifest = manifest_path.read_bytes()
    config_path = service.project / "config/experiments.yaml"
    config = load_experiment(config_path)
    later_sampling = config.sampling[0].model_copy(
        update={"id": "later", "temperature": 0.2, "top_p": 0.9}
    )
    updated = config.model_copy(update={"sampling": [*config.sampling, later_sampling]})
    config_path.write_text(updated.model_dump_json())

    second = service.invoke("run", "--run-id", "phase-two", "--input", second_input)
    evaluated = service.invoke("evaluate", "phase-one", "phase-two")

    assert first.returncode == second.returncode == evaluated.returncode == 0, (
        first.stdout + second.stdout + evaluated.stdout + evaluated.stderr
    )
    assert manifest_path.read_bytes() == original_manifest
    report = json.loads(evaluated.stdout)
    assert report["runs"][0]["experiment_sha256"] != report["runs"][1]["experiment_sha256"]
    assert len(report["variants"]) == 1
    variant = report["variants"][0]
    assert variant["run_ids"] == ["phase-one", "phase-two"]
    assert set(variant["input_ids"]) == {first_input, second_input}
    assert variant["quality"]["gold_cases"] == variant["quality"]["exact_documents"] == 2
    assert variant["quality"]["overall"]["correct"] == 30
    assert variant["quality"]["overall"]["total"] == 30
    assert variant["operational"]["physical_requests"] == 2
