"""Complete-request checks; render-only HTTP is never an inference attempt."""

import hashlib
import json
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import Field, model_validator

from extraction_service.application.tokenization import GemmaTokenizer
from extraction_service.execution.admission import (
    AdmissionEvidence,
    AdmissionReason,
    AdmissionRejected,
    ContextEnforcement,
)
from extraction_service.execution.budget.ledger import BudgetStop, BudgetStopReason
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.inference.messages import request_messages
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.record_types import ExecutionStage, ModelRuntime
from extraction_service.runtime.configuration import ModelPin
from extraction_service.runtime_types import NonEmptyText, PositiveInt, StrictModel


def request_fingerprint(request: GenerationRequest, *, thinking: bool | None = None) -> str:
    """Hash request content/sampling and any explicit Ollama thinking control."""

    payload = request.model_dump(exclude={"timeout_seconds"})

    if thinking is not None:
        payload["ollama_thinking"] = thinking

    serialized = json.dumps(payload, sort_keys=True)

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
        thinking: bool | None = None,
    ) -> None:
        self._client = client
        self._pin = pin
        self._tokenizer = tokenizer
        self._context_length = context_length
        self._runtime_version = runtime_version
        self._thinking = thinking

    def check(self, request: GenerationRequest, identity: ModelIdentity) -> AdmissionEvidence:
        if (
            identity.model_digest != self._pin.digest
            or identity.runtime_version != self._runtime_version
        ):
            raise AdmissionRejected(AdmissionReason.CONTEXT_IDENTITY_MISMATCH)

        # This pinned server returns before its completion path. There is no
        # num_predict=1 probe and no prompt-evaluation/generation timing sample.
        payload: dict[str, Any] = {
            "model": self._pin.model,
            "messages": request_messages(request),
            "format": request.output_schema,
            "stream": False,
            "truncate": False,
            "shift": False,
            "_debug_render_only": True,
            "options": {"num_ctx": self._context_length},
        }

        if self._thinking is not None:
            payload["think"] = self._thinking

        reply = self._client.post(
            "api/chat",
            payload,
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
            request_sha256=request_fingerprint(request, thinking=self._thinking),
            counter_identity=f"{self._pin.digest}/{self._tokenizer.sha256}",
            prompt_token_bound=count,
            output_allowance=allowance,
            context_length=self._context_length,
            thinking=self._thinking,
        )


class ProviderCoverage(StrictModel):
    """Operator-verified coverage; never infer a token bound from character counts.

    Counted mode requires exact non-generating request certificates. Explicit
    provider enforcement instead reserves the entire verified context ceiling;
    it makes no claim that a request has been counted or will fit.
    """

    pricing: VerifiedPricing
    context_length: PositiveInt
    context_enforcement: ContextEnforcement = ContextEnforcement.COUNTED
    server_context_stages: frozenset[ExecutionStage] = frozenset({ExecutionStage.SMOKE})
    request_token_bounds: dict[str, PositiveInt] = Field(default_factory=dict)
    evidence: NonEmptyText

    @model_validator(mode="after")
    def check_provider_ceiling(self) -> ProviderCoverage:
        if not self.server_context_stages or not self.server_context_stages <= {
            ExecutionStage.SMOKE,
            ExecutionStage.SCREENING,
            ExecutionStage.MATRIX,
        }:
            raise ValueError("Provider context stages must be smoke, screening and/or matrix")

        if self.context_enforcement == ContextEnforcement.PROVIDER:
            if self.pricing.input_token_ceiling < self.context_length:
                raise ValueError(
                    "Provider enforcement requires full-context input pricing coverage"
                )

            if self.request_token_bounds:
                raise ValueError("Provider enforcement must not claim request token certificates")

        return self

    def check_policy(self, *, allow_server_context: bool, stage: ExecutionStage) -> None:
        """Keep provider enforcement explicit, with coverage-specific allowed stages."""

        if self.context_enforcement == ContextEnforcement.PROVIDER:
            if not allow_server_context or stage not in self.server_context_stages:
                raise ValueError(
                    "Provider context enforcement requires an approved stage "
                    "and --allow-server-context"
                )

    def check_catalog(self, endpoint: OpenRouterEndpoint) -> None:
        """Reject stale lower rates; catalog floors do not prove complete tier coverage."""

        if self.context_enforcement == ContextEnforcement.PROVIDER:
            if endpoint.context_length != self.context_length:
                raise ValueError("Provider context coverage differs from current catalog context")

        rates = [
            ("prompt", self.pricing.input_usd_per_token),
            ("completion", self.pricing.output_usd_per_token),
            ("request", self.pricing.request_usd),
        ]

        if "internal_reasoning" in endpoint.pricing:
            rates.append(("internal_reasoning", self.pricing.output_usd_per_token))

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
        output = request.sampling.max_output_tokens

        if self.coverage.context_enforcement == ContextEnforcement.PROVIDER:
            if (
                output > self.coverage.pricing.output_token_ceiling
                or output > self.coverage.context_length
            ):
                raise AdmissionRejected(AdmissionReason.CONTEXT_CAPACITY_EXCEEDED)

            return AdmissionEvidence(
                method="provider-enforced-context-full-ceiling-reservation",
                request_sha256=fingerprint,
                context_enforcement=ContextEnforcement.PROVIDER,
                counter_identity=None,
                prompt_token_bound=None,
                output_allowance=output,
                context_length=self.coverage.context_length,
            )

        bound = self.coverage.request_token_bounds.get(fingerprint)

        if bound is None:
            raise AdmissionRejected(AdmissionReason.PROVIDER_BOUND_UNAVAILABLE)

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
