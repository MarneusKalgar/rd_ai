"""Translate OpenRouter envelopes without interpreting or repairing the PO JSON."""

from typing import Any

from pydantic import ValidationError

from extraction_service.inference.capabilities import WireModel
from extraction_service.inference.errors import (
    FailureEvidence,
    ModelTransportError,
    classify_http_status,
)
from extraction_service.inference.finish_reasons import (
    CONTENT_FILTER_FINISH_REASON,
    ERROR_FINISH_REASON,
    LENGTH_FINISH_REASON,
    STOP_FINISH_REASON,
)
from extraction_service.inference.http import HttpReply, protocol_error
from extraction_service.inference.types import ModelIdentity, ModelResponse, ResponseKind
from extraction_service.runtime_types import NonNegativeFloat, NonNegativeInt


class _Usage(WireModel):
    prompt_tokens: NonNegativeInt | None = None
    completion_tokens: NonNegativeInt | None = None
    cost: NonNegativeFloat | None = None


class _Message(WireModel):
    role: str
    content: str | None = None
    refusal: str | None = None
    tool_calls: list[Any] | None = None


class _Choice(WireModel):
    finish_reason: str | None = None
    native_finish_reason: str | None = None
    message: _Message
    error: dict[str, Any] | None = None


class _Completion(WireModel):
    id: str | None = None
    model: str
    provider: str | None = None
    choices: list[_Choice]
    usage: _Usage | None = None


def _response_kind(choice: _Choice) -> ResponseKind:
    if choice.error is not None or choice.finish_reason == ERROR_FINISH_REASON:
        return ResponseKind.ERROR

    if choice.message.refusal is not None or choice.finish_reason == CONTENT_FILTER_FINISH_REASON:
        return ResponseKind.REFUSED

    if choice.finish_reason == LENGTH_FINISH_REASON:
        return ResponseKind.TRUNCATED

    if choice.message.content is None:
        return ResponseKind.MISSING_RESPONSE

    if choice.finish_reason != STOP_FINISH_REASON or choice.message.tool_calls:
        return ResponseKind.INCOMPLETE

    return ResponseKind.COMPLETED


def _check_error_envelope(reply: HttpReply) -> None:
    if "error" not in reply.body:
        return

    error = reply.body["error"]

    if not isinstance(error, dict) or type(error.get("code")) is not int:
        raise protocol_error(reply.raw_body, reply.duration_ms, reply.credentials_redacted)

    status = error["code"]
    kind, retryable = classify_http_status(status)
    evidence = FailureEvidence(
        kind=kind,
        retryable=retryable,
        message=f"OpenRouter error {status}",
        status_code=status,
        raw_http_body=reply.raw_body,
        duration_ms=reply.duration_ms,
        credentials_redacted=reply.credentials_redacted,
    )

    raise ModelTransportError(evidence)


def parse_completion(reply: HttpReply, identity: ModelIdentity) -> ModelResponse:
    """Preserve content, finish/refusal/error details and available billed usage."""

    _check_error_envelope(reply)

    try:
        completion = _Completion.model_validate(reply.body)

        if len(completion.choices) != 1 or completion.choices[0].message.role != "assistant":
            raise ValueError("Expected one assistant response")

        choice = completion.choices[0]
        usage = completion.usage

        return ModelResponse(
            identity=identity,
            kind=_response_kind(choice),
            raw_response=choice.message.content,
            raw_http_body=reply.raw_body,
            reported_model=completion.model,
            serving_provider=completion.provider,
            request_id=completion.id,
            finish_reason=choice.finish_reason,
            native_finish_reason=choice.native_finish_reason,
            refusal=choice.message.refusal,
            error=None if choice.error is None else str(choice.error),
            duration_ms=reply.duration_ms,
            input_tokens=None if usage is None else usage.prompt_tokens,
            output_tokens=None if usage is None else usage.completion_tokens,
            cost_usd=None if usage is None else usage.cost,
            credentials_redacted=reply.credentials_redacted,
        )
    except ValidationError, ValueError:
        raise protocol_error(
            reply.raw_body, reply.duration_ms, reply.credentials_redacted
        ) from None
