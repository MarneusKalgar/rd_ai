"""Explicit provider context enforcement through the real CLI and loopback HTTP."""

import json
from decimal import Decimal
from typing import Any

import pytest
from pydantic import ValidationError

from extraction_service.application.persistence import reload_records
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.admission import AdmissionEvidence

from .conftest import ControlledService

INPUT: str = "B02-S003-PO01"
CATALOG: str = "/api/v1/models/google/gemini-3.5-flash-lite/endpoints"
ARGUMENTS: tuple[str, ...] = (
    "--model",
    "provider",
    "--coverage",
    "config/coverage.json",
    "--allow-provider",
    "--allow-server-context",
)


def prepare_coverage(service: ControlledService) -> dict[str, Any]:
    """Use catalog-sized reservations without supplying any request certificate."""

    service.coverage([INPUT])
    path = service.project / "config/coverage.json"
    coverage: dict[str, Any] = json.loads(path.read_bytes())
    provider = coverage["provider"]
    provider.update(context_length=1048576, context_enforcement="provider", request_token_bounds={})
    provider["pricing"].update(
        input_token_ceiling=1048576,
        input_usd_per_token="0.00000025",
        output_usd_per_token="0.0000015",
    )
    path.write_text(json.dumps(coverage))
    _, catalog = service.reply(CATALOG, None)
    endpoint = catalog["data"]["endpoints"][0]
    endpoint["context_length"] = 1048576
    endpoint["pricing"] = {"prompt": "0.00000025", "completion": "0.0000015"}
    service.replacements[CATALOG] = catalog

    return coverage


def initialize_budget(service: ControlledService) -> None:
    result = service.invoke("budget-init", "--opening-spend", "0", "--evidence", "Test only")
    assert result.returncode == 0, result.stdout + result.stderr


def test_provider_context_correction_and_export(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    prepare_coverage(service)
    initialize_budget(service)
    service.responses = ["{}", json.dumps(gold)]

    result = service.invoke("smoke", *ARGUMENTS, "--run-id", "server-context", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    directory = service.project / "results/runs/server-context"
    manifest, records = reload_records(directory)
    assert records[0].extraction == gold
    assert [attempt.outcome.value for attempt in records[0].attempts] == ["invalid", "valid"]
    completions = [
        payload for path, payload, _ in service.requests if path.endswith("/completions")
    ]
    assert len(completions) == 2
    initial, correction = completions
    assert initial is not None and correction is not None
    source = next(
        source for source in load_corpus(service.project).inputs if source.input_id == INPUT
    )
    assert source.text in initial["messages"][1]["content"]
    assert initial["messages"][1] == correction["messages"][1]
    schema = load_corpus(service.project).contract.schema_for_provider()

    for payload in (initial, correction):
        assert payload["plugins"] == [{"id": "context-compression", "enabled": False}]
        assert payload["service_tier"] == "default"
        assert payload["provider"] == {
            "only": ["google-ai-studio"],
            "allow_fallbacks": False,
            "require_parameters": True,
        }
        assert payload["response_format"]["json_schema"]["schema"] == schema
        assert payload["max_tokens"] == 4096

    checkpoint = next((directory / "checkpoints").glob("*.json"))
    admissions = json.loads(checkpoint.read_bytes())["admissions"]
    assert len(admissions) == 2
    assert admissions[0]["request_sha256"] != admissions[1]["request_sha256"]

    for admission in admissions:
        assert admission["context_enforcement"] == "provider"
        assert admission["prompt_token_bound"] is None
        assert admission["counter_identity"] is None
        assert admission["context_length"] == 1048576

    ledger = json.loads((service.project / "results/budget-ledger.json").read_bytes())
    assert [Decimal(entry["reserved_usd"]) for entry in ledger["reservations"]] == [
        Decimal("0.268288"),
        Decimal("0.268288"),
    ]
    assert all(entry["resolved"] for entry in ledger["reservations"])
    assert sum(Decimal(entry["billed_usd"]) for entry in ledger["reservations"]) == Decimal(
        "0.00002"
    )
    assert manifest.setup["provider"]["context_enforcement"] == "provider"
    exported = service.invoke("export-run", "server-context")
    verified = service.invoke("verify-export", "server-context")
    assert exported.returncode == verified.returncode == 0, exported.stdout + verified.stdout


@pytest.mark.parametrize("defect", ["no-opt-in", "matrix", "short-ceiling", "fake-bound"])
def test_provider_context_policy_rejection(service: ControlledService, defect: str) -> None:
    coverage = prepare_coverage(service)
    arguments = list(ARGUMENTS)
    command = "smoke"

    if defect == "no-opt-in":
        arguments.remove("--allow-server-context")
    elif defect == "matrix":
        command = "run"
    elif defect == "short-ceiling":
        coverage["provider"]["pricing"]["input_token_ceiling"] -= 1
    else:
        coverage["provider"]["request_token_bounds"] = {"a" * 64: 100}

    (service.project / "config/coverage.json").write_text(json.dumps(coverage))

    result = service.invoke(command, *arguments, "--input", INPUT)

    assert result.returncode == 2, result.stdout + result.stderr
    assert service.requests == []
    assert not (service.project / "results/budget-ledger.json").exists()


@pytest.mark.parametrize("context", [None, 1048575, 1048577])
def test_provider_context_catalog_drift(service: ControlledService, context: int | None) -> None:
    prepare_coverage(service)
    endpoint = service.replacements[CATALOG]["data"]["endpoints"][0]
    endpoint["context_length"] = context

    result = service.invoke("smoke", *ARGUMENTS, "--input", INPUT, "--run-id", "drift")

    assert result.returncode == 3, result.stdout + result.stderr
    _, records = reload_records(service.project / "results/runs/drift")
    assert records[0].reason == "unsafe_pricing"
    assert records[0].attempts == []
    assert [path for path, _, _ in service.requests] == [CATALOG]


def test_provider_context_unknown_billing_protects_matrix(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    prepare_coverage(service)
    initialize_budget(service)
    _, completion = service.reply("/api/v1/chat/completions", {})
    completion["choices"][0]["message"]["content"] = json.dumps(gold)
    completion["usage"].pop("cost")
    service.replacements["/api/v1/chat/completions"] = completion
    arguments = ["smoke", *ARGUMENTS, "--run-id", "unknown-billing"]

    for input_id in (INPUT, "B02-S006-PO01", "B02-S008-PO01", "B02-S030-PO01"):
        arguments.extend(["--input", input_id])

    result = service.invoke(*arguments)

    assert result.returncode == 3, result.stdout + result.stderr
    _, records = reload_records(service.project / "results/runs/unknown-billing")
    assert [record.status.value for record in records] == ["succeeded"] * 3 + ["not_attempted"]
    assert records[-1].reason == "matrix_budget_protected"
    assert records[-1].attempts == []
    completions = [path for path, _, _ in service.requests if path.endswith("/completions")]
    assert len(completions) == 3
    ledger = json.loads((service.project / "results/budget-ledger.json").read_bytes())
    assert len(ledger["reservations"]) == 3
    assert all(entry["billed_usd"] is None for entry in ledger["reservations"])
    accounted = sum(Decimal(entry["reserved_usd"]) for entry in ledger["reservations"])
    assert accounted == Decimal("0.804864")
    assert Decimal(ledger["budget_usd"]) - accounted >= Decimal("3.50")


def test_provider_context_offline_plan(service: ControlledService) -> None:
    prepare_coverage(service)

    result = service.invoke("plan-run", *ARGUMENTS, "--stage", "smoke", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["provider_context_enforcement"] == {"provider": "provider"}
    assert Decimal(report["maximum_api_usd_by_model"]["provider"]) == Decimal("1.073152")
    assert service.requests == []


def test_increased_reasoning_rate_stops_before_paid_http(service: ControlledService) -> None:
    prepare_coverage(service)
    endpoint = service.replacements[CATALOG]["data"]["endpoints"][0]
    endpoint["pricing"]["internal_reasoning"] = "0.000002"

    result = service.invoke("smoke", *ARGUMENTS, "--input", INPUT, "--run-id", "reasoning-rate")

    assert result.returncode == 3, result.stdout + result.stderr
    _, records = reload_records(service.project / "results/runs/reasoning-rate")
    assert records[0].reason == "unsafe_pricing" and records[0].attempts == []
    assert [path for path, _, _ in service.requests] == [CATALOG]


def test_provider_context_rejection_retains_physical_failure(service: ControlledService) -> None:
    prepare_coverage(service)
    initialize_budget(service)
    service.generation_status = 400

    result = service.invoke("smoke", *ARGUMENTS, "--run-id", "rejected", "--input", INPUT)

    assert result.returncode == 3, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/rejected")
    assert manifest.state.value == "incomplete"
    assert records[0].status.value == "failed"
    assert len(records[0].attempts) == 1
    failure = records[0].attempts[0].failure
    assert failure is not None
    assert failure.status_code == 400
    assert failure.kind.value == "unsupported_request"
    assert failure.retryable is False
    assert failure.raw_http_body == '{"error": "controlled temporary failure"}'
    completions = [path for path, _, _ in service.requests if path.endswith("/completions")]
    assert len(completions) == 1
    ledger = json.loads((service.project / "results/budget-ledger.json").read_bytes())
    assert len(ledger["reservations"]) == 1
    assert ledger["reservations"][0]["billed_usd"] is None
    assert Decimal(ledger["reservations"][0]["reserved_usd"]) == Decimal("0.268288")


def test_admission_evidence_preserves_old_counted_records() -> None:
    historical = {
        "method": "historical-counter",
        "request_sha256": "a" * 64,
        "counter_identity": "counter-v1",
        "prompt_token_bound": 123,
        "output_allowance": 4096,
        "context_length": 32768,
    }

    restored = AdmissionEvidence.model_validate_json(json.dumps(historical))

    assert restored.context_enforcement.value == "counted"
    assert restored.prompt_token_bound == 123

    for defect in ({"prompt_token_bound": None}, {"context_enforcement": "provider"}):
        with pytest.raises(ValidationError):
            AdmissionEvidence.model_validate_json(json.dumps({**historical, **defect}))
