"""Complete-request checks; render-only HTTP is never an inference attempt."""

import hashlib
import json
from decimal import Decimal, InvalidOperation

from extraction_service.application.tokenization import GemmaTokenizer
from extraction_service.execution.admission import (
    AdmissionEvidence,
    AdmissionReason,
    AdmissionRejected,
)
from extraction_service.execution.budget.ledger import BudgetStop, BudgetStopReason
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.inference.messages import request_messages
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime.configuration import ModelPin
from extraction_service.runtime_types import NonEmptyText, PositiveInt, StrictModel


def request_fingerprint(request: GenerationRequest) -> str:
    """Identify exact instructions/schema/source and output/sampling controls."""

    serialized = json.dumps(request.model_dump(exclude={"timeout_seconds"}), sort_keys=True)

    return hashlib.sha256(serialized.encode()).hexdigest()


class LocalAdmission:
    def __init__(
        self,
        client: JsonHttpClient,
        pin: ModelPin,
        tokenizer: GemmaTokenizer,
        context_length: int,
        *,
        runtime_version: str,
    ) -> None:
        self._client = client
        self._pin = pin
        self._tokenizer = tokenizer
        self._context_length = context_length
        self._runtime_version = runtime_version

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        if (
            identity.model_digest != self._pin.digest
            or identity.runtime_version != self._runtime_version
        ):
            raise AdmissionRejected(AdmissionReason.CONTEXT_IDENTITY_MISMATCH)

        # This pinned server returns before its completion path. There is no
        # num_predict=1 probe and no prompt-evaluation/generation timing sample.
        reply = self._client.post(
            "api/chat",
            {
                "model": self._pin.model,
                "messages": request_messages(request),
                "format": request.output_schema,
                "stream": False,
                "truncate": False,
                "shift": False,
                "_debug_render_only": True,
                "options": {"num_ctx": self._context_length},
            },
            request.timeout_seconds,
        )
        debug = reply.body.get("_debug_info")

        if reply.body.get("model") != self._pin.model or not isinstance(debug, dict):
            raise ValueError("Pinned runtime did not return render-only evidence")

        rendered = debug.get("rendered_template")

        if not isinstance(rendered, str) or not rendered:
            raise ValueError("Missing rendered prompt")

        # Two extra slots conservatively cover automatic boundary tokens.
        count = self._tokenizer.count(rendered) + 2
        allowance = request.sampling.max_output_tokens

        if count + allowance > self._context_length:
            raise AdmissionRejected(AdmissionReason.CONTEXT_CAPACITY_EXCEEDED)

        return AdmissionEvidence(
            method="gemma4-installed-bpe-render-only-plus-two-boundary-tokens",
            request_sha256=request_fingerprint(request),
            counter_identity=f"{self._pin.digest}/{self._tokenizer.sha256}",
            prompt_token_bound=count,
            output_allowance=allowance,
            context_length=self._context_length,
        )


class ProviderCoverage(StrictModel):
    """Operator-verified coverage; never infer a token bound from character counts.

    Each admitted request requires a certificate for its exact fingerprint.
    Certificates come from a verified non-generating provider token-count method.
    Missing correction certificates fail closed rather than generating a probe.
    """

    pricing: VerifiedPricing
    context_length: PositiveInt
    request_token_bounds: dict[str, PositiveInt]
    evidence: NonEmptyText

    def check_catalog(self, endpoint: OpenRouterEndpoint) -> None:
        """Reject stale lower rates; catalog floors do not prove complete tier coverage."""

        rates = (
            ("prompt", self.pricing.input_usd_per_token),
            ("completion", self.pricing.output_usd_per_token),
            ("request", self.pricing.request_usd),
        )

        for name, ceiling in rates:
            raw = endpoint.pricing.get(name, "0" if name == "request" else None)

            try:
                advertised = Decimal(str(raw))
            except InvalidOperation:
                raise ValueError("Provider catalog pricing is unavailable") from None

            if not advertised.is_finite() or advertised < 0 or ceiling < advertised:
                raise ValueError("Verified provider rates do not cover current catalog pricing")


class ProviderAdmission:
    def __init__(self, coverage: ProviderCoverage | None) -> None:
        self.coverage = coverage

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        if self.coverage is None:
            raise BudgetStop(BudgetStopReason.UNSAFE_PRICING)

        dependency = self.coverage.pricing.dependency

        if (
            identity.runtime != ModelRuntime.OPENROUTER
            or identity.model_name != dependency.model_name
            or identity.serving_provider != dependency.serving_provider
        ):
            raise AdmissionRejected(AdmissionReason.PROVIDER_IDENTITY_MISMATCH)

        fingerprint = request_fingerprint(request)
        bound = self.coverage.request_token_bounds.get(fingerprint)

        if bound is None:
            raise AdmissionRejected(AdmissionReason.PROVIDER_BOUND_UNAVAILABLE)

        output = request.sampling.max_output_tokens

        if (
            bound > self.coverage.pricing.input_token_ceiling
            or output > self.coverage.pricing.output_token_ceiling
            or bound + output > self.coverage.context_length
        ):
            raise AdmissionRejected(AdmissionReason.CONTEXT_CAPACITY_EXCEEDED)

        return AdmissionEvidence(
            method="verified-exact-request-provider-token-certificate",
            request_sha256=fingerprint,
            counter_identity=self.coverage.evidence,
            prompt_token_bound=bound,
            output_allowance=output,
            context_length=self.coverage.context_length,
        )
