"""Offline schedules, request fingerprints and conservative paid-run estimates."""

import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from extraction_service.application.admission import ProviderCoverage, request_fingerprint
from extraction_service.application.selection import RunOptions, select_models, selected_jobs
from extraction_service.artifacts import artifact_path
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.models import ModelConfig
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetStop
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import ModelRuntime


def _provider_estimate(
    model: ModelConfig,
    coverage: ProviderCoverage | None,
    requests: list[GenerationRequest],
    physical_limit: int,
) -> str | None:
    """Use compatible operator evidence without claiming a live price refresh."""

    if coverage is None:
        return None

    pricing = coverage.pricing
    dependency = pricing.dependency

    if (
        dependency.runtime != ModelRuntime.OPENROUTER
        or dependency.model_name != model.model
        or dependency.serving_provider != model.serving_provider
    ):
        return None

    maximum = Decimal("0")

    try:
        for request in requests:
            maximum += physical_limit * pricing.reserve_for(request, dependency)
    except ValueError:
        return None

    return str(maximum)


def describe_run(project_dir: Path, options: RunOptions, config_file: str) -> dict[str, Any]:
    """Describe selected work without clients, model probes or budget initialization."""

    config_path = artifact_path(project_dir, config_file)
    experiment = load_experiment(config_path)
    corpus = load_corpus(project_dir)
    digest = hashlib.sha256(config_path.read_bytes()).hexdigest()
    jobs = selected_jobs(project_dir, corpus, experiment, options, digest)
    models = select_models(experiment, options)
    fingerprints = []
    requests = []

    for job in jobs:
        request = GenerationRequest.from_contract(
            instructions=job.instructions,
            source_text=job.source_text,
            contract=corpus.contract,
            sampling=job.sampling,
            timeout_seconds=experiment.execution.request_timeout_seconds,
        )
        requests.append(request)
        fingerprints.append(
            {
                "input_id": job.input_id,
                "prompt_id": job.prompt_id,
                "sampling_id": job.sampling.id,
                "initial_request_sha256": request_fingerprint(request),
            }
        )

    physical_limit = 2 * (experiment.execution.transport_retries + 1)
    estimates: dict[str, str | None] = {}
    coverages: dict[str, ProviderCoverage] = {}

    if options.coverage_file is not None:
        coverage_path = artifact_path(project_dir, options.coverage_file)
        coverages = TypeAdapter(dict[str, ProviderCoverage]).validate_json(
            coverage_path.read_bytes()
        )

    for model in models:
        if model.backend == "ollama":
            estimates[model.id] = "0"
            continue

        coverage = coverages.get(model.id)
        estimates[model.id] = _provider_estimate(model, coverage, requests, physical_limit)

    accounted: str | None = None
    ledger = BudgetLedger(project_dir, experiment.execution)

    if ledger.path.exists():
        try:
            accounted = str(ledger.snapshot().accounted_usd)
        except BudgetStop:
            pass

    return {
        "run_id": options.run_id,
        "stage": options.stage.value,
        "models": [model.model_dump() for model in models],
        "experiment_sha256": digest,
        "execution": experiment.execution.model_dump(),
        "jobs_per_model": fingerprints,
        "primary_requests": len(models) * len(jobs),
        "maximum_physical_requests": len(models) * len(jobs) * physical_limit,
        "maximum_api_usd_by_model": estimates,
        "accounted_prior_usd": accounted,
        "provider_approval_required": any(model.backend == "openrouter" for model in models),
        "note": (
            "Null cost/ledger means unverified, not zero. Actual corrections need admission too."
        ),
    }
