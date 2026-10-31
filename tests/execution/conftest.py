from decimal import Decimal
from pathlib import Path

import pytest

from extraction_service.configuration.models import ExecutionConfig, SamplingConfig
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.types import DependencyIdentity, ExtractionJob
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import ModelRuntime

from .helpers import FakeClock


@pytest.fixture
def policy() -> ExecutionConfig:
    return ExecutionConfig(
        request_timeout_seconds=5.0,
        input_timeout_seconds=20.0,
        transport_retries=1,
        api_budget_usd=1.0,
        matrix_reserve_usd=0.5,
        dependency_failure_limit=3,
        backoff_initial_seconds=1.0,
        backoff_max_seconds=3.0,
    )


@pytest.fixture
def job() -> ExtractionJob:
    return ExtractionJob(
        run_id="run-1",
        input_id="input-1",
        input_sha256="1" * 64,
        experiment_sha256="2" * 64,
        prompt_id="v1",
        prompt_sha256="3" * 64,
        instructions="Extract supported values only.",
        source_text="ORDER!A1 PO number | B1 PO-1001",
        sampling=SamplingConfig(id="baseline", temperature=0.0, top_p=1.0, max_output_tokens=100),
    )


@pytest.fixture
def local_identity() -> ModelIdentity:
    return ModelIdentity(
        model_id="local",
        model_name="test-local",
        runtime=ModelRuntime.OLLAMA_DOCKER,
        runtime_version="test-version",
        model_digest="a" * 64,
    )


@pytest.fixture
def paid_identity() -> ModelIdentity:
    return ModelIdentity(
        model_id="provider",
        model_name="test-provider",
        runtime=ModelRuntime.OPENROUTER,
        serving_provider="test-route",
    )


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


@pytest.fixture
def ledger(tmp_path: Path, policy: ExecutionConfig) -> BudgetLedger:
    ledger = BudgetLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="No prior test spend")

    return ledger


@pytest.fixture
def pricing(paid_identity: ModelIdentity) -> VerifiedPricing:
    return VerifiedPricing(
        dependency=DependencyIdentity.from_model("https://provider.test/api/v1", paid_identity),
        input_token_ceiling=1000,
        output_token_ceiling=100,
        input_usd_per_token=Decimal("0.0001"),
        output_usd_per_token=Decimal("0.001"),
        request_usd=Decimal("0"),
        evidence="Fictional test prices and full context bound; not live provider pricing.",
    )
