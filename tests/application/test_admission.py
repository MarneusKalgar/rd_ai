"""Exact provider-request certificates and their fail-closed boundaries."""

import json
from typing import Any

import pytest

from extraction_service.application.admission import (
    LocalAdmission,
    ProviderAdmission,
    ProviderCoverage,
)
from extraction_service.application.persistence import reload_records
from extraction_service.application.selection import RunOptions, selected_jobs
from extraction_service.application.tokenization import GemmaTokenizer
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.admission import AdmissionRejected
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime.configuration import load_model_pin

from .conftest import ControlledService, tokenizer_info


@pytest.mark.parametrize("version", ["0.40.7", "0.40.12"])
def test_local_admission_binds_observed_version(
    service: ControlledService, contract: ExtractionContract, version: str
) -> None:
    service.native = True
    pin = load_model_pin(service.project, native=True)
    sampling = load_experiment(service.project / "config/experiments.yaml").sampling[0]
    request = GenerationRequest.from_contract(
        instructions="Extract the purchase order.",
        source_text="Order PO-1",
        contract=contract,
        sampling=sampling,
        timeout_seconds=1.0,
    )
    identity = ModelIdentity(
        model_id="local",
        model_name=pin.model,
        runtime=ModelRuntime.OLLAMA_NATIVE,
        runtime_version=version,
        model_digest=pin.digest,
    )
    client = JsonHttpClient(service.base_url)

    try:
        admission = LocalAdmission(
            client, pin, GemmaTokenizer(tokenizer_info()), 32768, runtime_version="0.40.12"
        )

        if version == "0.40.12":
            evidence = admission.check(request, identity)
            assert evidence.context_length == 32768
            assert [path for path, _, _ in service.requests] == ["/api/chat"]
        else:
            with pytest.raises(AdmissionRejected, match="context_identity_mismatch"):
                admission.check(request, identity)

            assert service.requests == []
    finally:
        client.close()


@pytest.mark.parametrize(
    "defect",
    [
        "none",
        "overflow",
        "changed-input",
        "correction",
        "schema",
        "sampling",
        "route",
        "output-coverage",
    ],
)
def test_exact_request_admission(service: ControlledService, defect: str) -> None:
    service.coverage(["B02-S003-PO01"])
    coverage_path = service.project / "config/coverage.json"
    coverage_data = json.loads(coverage_path.read_bytes())["provider"]
    coverage_data["context_length"] = 24096
    experiment = load_experiment(service.project / "config/experiments.yaml")
    corpus = load_corpus(service.project)
    job = selected_jobs(
        service.project, corpus, experiment, RunOptions(input_ids=["B02-S003-PO01"]), "a" * 64
    )[0]
    request = GenerationRequest.from_contract(
        instructions=job.instructions,
        source_text=job.source_text,
        contract=corpus.contract,
        sampling=job.sampling,
        timeout_seconds=1.0,
    )
    identity = ModelIdentity(
        model_id="provider",
        model_name="google/gemini-3.5-flash-lite",
        runtime=ModelRuntime.OPENROUTER,
        serving_provider="google-ai-studio",
    )
    expected = "context_capacity_exceeded"

    if defect == "overflow":
        coverage_data["context_length"] -= 1
    elif defect in ("changed-input", "correction"):
        field = "source_text" if defect == "changed-input" else "instructions"
        request = request.model_copy(
            update={field: "Different actual content and validation evidence"}
        )
        expected = "verified_provider_token_bound_unavailable"
    elif defect == "route":
        identity = identity.model_copy(update={"serving_provider": "different-route"})
        expected = "provider_coverage_identity_mismatch"
    elif defect == "schema":
        request = request.model_copy(update={"output_schema": {"type": "object"}})
        expected = "verified_provider_token_bound_unavailable"
    elif defect == "sampling":
        changed = request.sampling.model_copy(update={"temperature": 0.2})
        request = request.model_copy(update={"sampling": changed})
        expected = "verified_provider_token_bound_unavailable"
    elif defect == "output-coverage":
        coverage_data["pricing"]["output_token_ceiling"] = 4095

    coverage = ProviderCoverage.model_validate_json(json.dumps(coverage_data))
    admission = ProviderAdmission(coverage)

    if defect == "none":
        evidence = admission.check(request, identity)
        assert evidence.prompt_token_bound == 20000
        assert evidence.output_allowance == 4096
        assert evidence.context_length == 24096
    else:
        with pytest.raises(AdmissionRejected, match=expected):
            admission.check(request, identity)

    assert service.requests == []


@pytest.mark.parametrize(
    "field,value", [("input_usd_per_token", "0"), ("output_usd_per_token", "0")]
)
def test_stale_pricing_rejects_before_paid_http(
    service: ControlledService,
    field: str,
    value: Any,
) -> None:
    service.coverage(["B02-S003-PO01"])
    path = service.project / "config/coverage.json"
    coverage = json.loads(path.read_bytes())
    coverage["provider"]["pricing"][field] = value
    path.write_text(json.dumps(coverage))

    result = service.invoke(
        "run",
        "--run-id",
        "stale-pricing",
        "--model",
        "provider",
        "--input",
        "B02-S003-PO01",
        "--allow-provider",
        "--coverage",
        "config/coverage.json",
    )

    assert result.returncode == 3
    manifest, records = reload_records(service.project / "results/runs/stale-pricing")
    assert records[0].reason == "unsafe_pricing"
    assert manifest.summary is not None
    assert [stop.value for stop in manifest.summary.budget_stops] == ["unsafe_pricing"]
    assert not service.generation_started.is_set()
    assert not (service.project / "results/budget-ledger.json").exists()


@pytest.mark.parametrize("overflow", [False, True])
def test_local_exact_context_boundary(
    service: ControlledService,
    gold: dict[str, Any],
    overflow: bool,
) -> None:
    service.responses = [json.dumps(gold)]
    service.rendered_override = "a" * (32768 - 4096 - 2 + int(overflow))

    result = service.invoke("run", "--run-id", "context-boundary", "--input", "B02-S003-PO01")

    _, records = reload_records(service.project / "results/runs/context-boundary")

    if overflow:
        assert result.returncode == 3
        assert records[0].reason == "context_capacity_exceeded"
        assert records[0].attempts == []
        assert not service.generation_started.is_set()
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        assert records[0].extraction == gold
        checkpoint = next(
            (service.project / "results/runs/context-boundary/checkpoints").glob("*.json")
        )
        admission = json.loads(checkpoint.read_bytes())["admissions"][0]
        assert admission["prompt_token_bound"] + admission["output_allowance"] == 32768
