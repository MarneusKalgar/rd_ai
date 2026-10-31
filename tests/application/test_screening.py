"""The real screening entrypoint selects gold inputs and preserves stage accounting."""

import json
from copy import deepcopy
from decimal import Decimal

import pytest

from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus

from .conftest import ControlledService
from .test_provider_context import initialize_budget, prepare_coverage

BASE: tuple[str, ...] = (
    "--config",
    "config/screening.yaml",
    "--stage",
    "screening",
    "--model",
    "provider",
    "--coverage",
    "config/coverage.json",
    "--allow-server-context",
    "--allow-provider",
)


def screening_coverage(service: ControlledService) -> None:
    coverage = prepare_coverage(service)
    template = coverage["provider"]
    template["server_context_stages"] = ["screening"]
    config = load_experiment(service.project / "config/screening.yaml")

    for model in config.models:
        if model.backend != "openrouter":
            continue

        entry = deepcopy(template)
        entry["pricing"]["dependency"].update(
            model_name=model.model, serving_provider=model.serving_provider
        )
        coverage[model.id] = entry
        path = f"/api/v1/models/{model.model}/endpoints"
        _, catalog = service.reply(path, None)
        catalog["data"]["endpoints"][0]["context_length"] = 1048576
        service.replacements[path] = catalog

    (service.project / "config/coverage.json").write_text(json.dumps(coverage))


def test_three_candidate_screening_and_evaluation(service: ControlledService) -> None:
    screening_coverage(service)
    initialize_budget(service)
    corpus = load_corpus(service.project)
    gold_ids = [source.input_id for source in corpus.inputs if source.is_gold]
    service.responses = [json.dumps(corpus.gold[identifier]) for identifier in gold_ids] * 3
    arguments = [*BASE, "--model", "provider-35", "--model", "provider-mistral"]

    planned = service.invoke("plan-run", *arguments)
    completed = service.invoke("run", *arguments, "--run-id", "screened")
    before_evaluation = len(service.requests)
    evaluated = service.invoke("evaluate", "screened")

    assert planned.returncode == completed.returncode == evaluated.returncode == 0, (
        planned.stdout + completed.stdout + completed.stderr + evaluated.stdout
    )
    plan = json.loads(planned.stdout)
    assert plan["primary_requests"] == 30 and plan["maximum_physical_requests"] == 120
    manifest, records = reload_records(service.project / "results/runs/screened")
    assert manifest.stage == "screening" and len(records) == 30
    assert {record.input_id for record in records} == set(gold_ids)
    assert all(record.stage.value == "screening" and record.prompt_id == "v1" for record in records)
    completions = [
        payload for path, payload, _ in service.requests if path.endswith("/completions")
    ]
    assert len(completions) == 30
    assert {payload["model"] for payload in completions if payload} == {
        "google/gemini-3.1-flash-lite",
        "google/gemini-3.5-flash-lite",
        "mistralai/mistral-small-2603",
    }
    assert all(
        payload and payload["temperature"] == 0.0 and payload["top_p"] == 1.0
        for payload in completions
    )
    report = json.loads(evaluated.stdout)
    assert len(report["variants"]) == 3
    assert all(variant["quality"]["exact_documents"] == 10 for variant in report["variants"])
    assert all(variant["quality"]["missing_gold_inputs"] == [] for variant in report["variants"])
    assert all(
        Decimal(variant["operational"]["total_api_cost_usd"]) == Decimal("0.00010")
        for variant in report["variants"]
    )
    assert len(service.requests) == before_evaluation
    assert all(
        Decimal(variant["operational"]["api_cost_per_1000_attempted_inputs_usd"]) == Decimal("0.01")
        for variant in report["variants"]
    )
    budget = service.invoke("budget-show", "--config", "config/screening.yaml")
    assert budget.returncode == 0
    assert Decimal(json.loads(budget.stdout)["accounted_usd"]) == Decimal("0.00030")
    assert Decimal(json.loads(budget.stdout)["protected_matrix_usd"]) == Decimal("3.5")


@pytest.mark.parametrize(
    "defect",
    ["no-opt-in", "smoke-coverage", "matrix", "repetition", "subset", "local", "v2", "sampling"],
)
def test_screening_gates_block_before_http(service: ControlledService, defect: str) -> None:
    screening_coverage(service)
    arguments = list(BASE)

    if defect == "no-opt-in":
        arguments.remove("--allow-server-context")
    elif defect == "smoke-coverage":
        path = service.project / "config/coverage.json"
        data = json.loads(path.read_bytes())
        data["provider"].pop("server_context_stages")
        path.write_text(json.dumps(data))
    elif defect in ("matrix", "repetition"):
        arguments[arguments.index("screening")] = defect
    elif defect == "subset":
        arguments.extend(["--input", "B02-S003-PO01"])
    elif defect == "local":
        arguments[arguments.index("provider")] = "local"
    elif defect == "v2":
        arguments.extend(["--prompt", "v2"])
    else:
        arguments.extend(["--sampling", "different"])

    result = service.invoke("run", *arguments, "--run-id", "blocked")

    assert result.returncode == 2, result.stdout + result.stderr
    assert service.requests == []
    assert not (service.project / "results/budget-ledger.json").exists()
