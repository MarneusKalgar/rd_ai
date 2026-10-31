import json
from decimal import Decimal

import pytest

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.coordinator import ExtractionCoordinator, ScheduledExtraction
from extraction_service.execution.types import ExecutionTarget, ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.types import ModelIdentity

from .helpers import FakeClock, ScriptedAdapter, response


def test_known_failed_request_cost_and_usage_are_included_in_totals_and_ledger(
    contract: ExtractionContract,
    gold: JsonObject,
    policy: ExecutionConfig,
    job: ExtractionJob,
    paid_identity: ModelIdentity,
    pricing: VerifiedPricing,
    ledger: BudgetLedger,
    clock: FakeClock,
) -> None:
    error = ModelTransportError(
        FailureEvidence(
            kind=FailureKind.SERVER_ERROR,
            retryable=True,
            message="Failed after billable work",
            duration_ms=10.0,
            input_tokens=2,
            output_tokens=3,
            cost_usd=0.01,
        )
    )
    adapter = ScriptedAdapter(
        paid_identity, clock, [error, response(paid_identity, json.dumps(gold))]
    )
    coordinator = ExtractionCoordinator(contract, policy, ledger=ledger, clock=clock)

    record = coordinator.execute(
        ScheduledExtraction(
            job,
            ExecutionTarget(adapter, "https://provider.test/api/v1"),
            pricing,
        )
    )

    assert record.status == "succeeded"
    assert record.total_input_tokens == 14
    assert record.total_output_tokens == 7
    assert record.total_cost_usd == pytest.approx(0.06)
    assert ledger.snapshot().accounted_usd == Decimal("0.06")
    assert record.attempts[0].failure == error.evidence
    assert record.attempts[0].accounting_note is None
