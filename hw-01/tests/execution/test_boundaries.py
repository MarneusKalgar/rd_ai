from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import AnyHttpUrl, ValidationError

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget import BudgetLedger, Reservation
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.pricing import VerifiedPricing
from extraction_service.execution.types import DependencyIdentity, ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import ExecutionStage

from .helpers import FakeClock, ScriptedAdapter


@pytest.mark.parametrize("defect", ["route", "model", "endpoint", "output-limit"])
def test_uncovered_pricing_is_rejected_before_reservation_or_inference(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
    defect: str,
) -> None:
    values = pricing.model_dump()

    if defect == "output-limit":
        values["output_token_ceiling"] = 99
    else:
        dependency = values["dependency"]

        if defect == "route":
            dependency["serving_provider"] = "other-route"
        elif defect == "model":
            dependency["model_name"] = "other-model"
        else:
            dependency["endpoint"] = AnyHttpUrl("https://other.test/api")

        values["dependency"] = DependencyIdentity.model_validate(dependency)

    mismatched = VerifiedPricing.model_validate(values)
    adapter = ScriptedAdapter(paid_identity, clock, [])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(
            job,
            ExecutionTarget(adapter, "https://provider.test/api/v1"),
            mismatched,
        )
    )

    assert record.status == "not_attempted"
    assert record.reason == "unsafe_pricing"
    assert record.attempts == []
    assert adapter.requests == []
    assert ledger.snapshot().reservations == []


def test_budget_policy_cannot_be_changed_between_coordinator_and_ledger(
    contract: ExtractionContract, policy: ExecutionConfig, ledger: BudgetLedger
) -> None:
    changed = policy.model_copy(update={"api_budget_usd": 0.9})

    with pytest.raises(ValueError, match="budget policies differ"):
        ExtractionCoordinator(contract, changed, ledger=ledger)


def test_deadline_expiring_during_reservation_refunds_unsent_request(
    contract: ExtractionContract,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    clock: FakeClock,
    tmp_path: Path,
) -> None:
    class SlowLedger(BudgetLedger):
        def reserve(
            self,
            *,
            amount_usd: Decimal,
            stage: ExecutionStage,
            request_key: str,
            pricing_evidence: str,
        ) -> Reservation:
            reservation = super().reserve(
                amount_usd=amount_usd,
                stage=stage,
                request_key=request_key,
                pricing_evidence=pricing_evidence,
            )
            clock.seconds += 20.0

            return reservation

    ledger = SlowLedger(tmp_path, policy)
    ledger.initialize(opening_spend_usd=Decimal("0"), evidence="test opening")
    adapter = ScriptedAdapter(paid_identity, clock, [])
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(
            job,
            ExecutionTarget(adapter, "https://provider.test/api/v1"),
            pricing,
        )
    )

    assert record.status == "not_attempted"
    assert record.reason == "input_deadline_exceeded"
    assert record.attempts == []
    assert adapter.requests == []
    assert ledger.snapshot().accounted_usd == Decimal("0")


@pytest.mark.parametrize(
    "url",
    [
        "https://user:secret@provider.test",
        "https://provider.test?key=x",
        "https://provider.test#fragment",
    ],
)
def test_dependency_identity_rejects_credential_bearing_urls(
    paid_identity: ModelIdentity, url: str
) -> None:
    with pytest.raises(ValidationError):
        DependencyIdentity.from_model(url, paid_identity)
