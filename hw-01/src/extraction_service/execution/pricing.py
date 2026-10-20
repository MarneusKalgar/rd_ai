"""Explicit verified pricing ceilings; no guessed tokenizer counts or live prices."""

from decimal import Decimal
from typing import Annotated

from pydantic import Field

from extraction_service.execution.types import DependencyIdentity
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime_types import NonEmptyText, PositiveInt, StrictModel

type Money = Annotated[Decimal, Field(ge=0, allow_inf_nan=False)]


class VerifiedPricing(StrictModel):
    """An operator-verified upper bound for this exact paid route.

    input_token_ceiling must cover every billable input token (the full verified
    context ceiling is safe). Rates must cover applicable tiers, reasoning/output
    and fixed fees. Evidence records the source, verification date and assumptions.
    Missing or unsupported pricing means no safe paid request can be established.
    """

    dependency: DependencyIdentity
    input_token_ceiling: PositiveInt
    output_token_ceiling: PositiveInt
    input_usd_per_token: Money
    output_usd_per_token: Money
    request_usd: Money
    evidence: NonEmptyText

    def reserve_for(self, request: GenerationRequest, dependency: DependencyIdentity) -> Decimal:
        """Use the verified input ceiling and the adapter's explicit output limit."""

        if dependency != self.dependency or dependency.runtime != ModelRuntime.OPENROUTER:
            raise ValueError("Pricing identity differs from the paid dependency")

        if request.sampling.max_output_tokens > self.output_token_ceiling:
            raise ValueError("Output limit exceeds verified pricing coverage")

        return (
            self.input_token_ceiling * self.input_usd_per_token
            + request.sampling.max_output_tokens * self.output_usd_per_token
            + self.request_usd
        )
