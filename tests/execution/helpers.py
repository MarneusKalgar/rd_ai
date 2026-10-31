"""Controlled model and clock boundaries; production validation remains real."""

from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from extraction_service.inference.errors import FailureEvidence, FailureKind, ModelTransportError
from extraction_service.inference.types import (
    GenerationRequest,
    ModelIdentity,
    ModelResponse,
    ResponseKind,
)
from extraction_service.record_types import ModelRuntime


@dataclass
class FakeClock:
    seconds: float = 0.0
    sleeps: list[float] = field(default_factory=list)

    def monotonic(self) -> float:
        return self.seconds

    def now(self) -> datetime:
        return datetime(2026, 10, 20, tzinfo=UTC) + timedelta(seconds=self.seconds)

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.seconds += seconds


class ScriptedAdapter:
    def __init__(
        self,
        identity: ModelIdentity,
        clock: FakeClock,
        outcomes: Sequence[ModelResponse | Exception],
        *,
        elapsed_seconds: float = 0.01,
    ) -> None:
        self.identity = identity
        self.clock = clock
        self.outcomes = list(outcomes)
        self.elapsed_seconds = elapsed_seconds
        self.requests: list[GenerationRequest] = []

    def generate(self, request: GenerationRequest) -> ModelResponse:
        self.requests.append(request)
        self.clock.seconds += self.elapsed_seconds
        outcome = self.outcomes.pop(0)

        if isinstance(outcome, Exception):
            raise outcome

        return outcome


def response(identity: ModelIdentity, text: str | None) -> ModelResponse:
    return ModelResponse(
        identity=identity,
        kind=ResponseKind.COMPLETED,
        raw_response=text,
        raw_http_body="exact wire envelope",
        reported_model=identity.model_name,
        serving_provider=identity.serving_provider,
        finish_reason="stop",
        request_id="response-001",
        duration_ms=10.0,
        input_tokens=12,
        output_tokens=4,
        cost_usd=0.0 if identity.runtime != ModelRuntime.OPENROUTER else 0.05,
    )


def failure(
    kind: FailureKind = FailureKind.TIMEOUT,
    *,
    retryable: bool = True,
    retry_after: str | None = None,
) -> ModelTransportError:
    return ModelTransportError(
        FailureEvidence(
            kind=kind,
            retryable=retryable,
            message=f"test {kind.value}",
            duration_ms=10.0,
            raw_http_body="exact failure envelope",
            retry_after=retry_after,
        )
    )
