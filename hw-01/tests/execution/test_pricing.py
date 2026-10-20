"""Use independently calculated quotes to protect conservative request bounds."""

from decimal import Decimal

from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.types import ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.types import GenerationRequest


def test_reservation_quote_includes_nonzero_fixed_request_fee(
    contract: ExtractionContract, job: ExtractionJob, pricing: VerifiedPricing
) -> None:
    configured = pricing.model_copy(update={"request_usd": Decimal("0.03")})
    request = GenerationRequest.from_contract(
        instructions=job.instructions,
        source_text=job.source_text,
        contract=contract,
        sampling=job.sampling,
        timeout_seconds=5.0,
    )

    quote = configured.reserve_for(request, configured.dependency)

    # $0.10 for the input bound + $0.10 for output + $0.03 per request.
    assert quote == Decimal("0.23")
