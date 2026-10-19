"""Translate Ollama's non-streaming response without validating the model's PO."""

from pydantic import ValidationError

from extraction_service.inference.capabilities import WireModel
from extraction_service.inference.finish_reasons import LENGTH_FINISH_REASON, STOP_FINISH_REASON
from extraction_service.inference.http import HttpReply, protocol_error
from extraction_service.inference.types import ModelIdentity, ModelResponse, ResponseKind
from extraction_service.runtime_types import NonNegativeInt


class _Message(WireModel):
    role: str
    content: str | None = None


class _Completion(WireModel):
    model: str
    message: _Message
    done: bool
    done_reason: str | None = None
    prompt_eval_count: NonNegativeInt | None = None
    eval_count: NonNegativeInt | None = None
    total_duration: NonNegativeInt | None = None
    load_duration: NonNegativeInt | None = None


def _response_kind(completion: _Completion) -> ResponseKind:
    if completion.done_reason == LENGTH_FINISH_REASON:
        return ResponseKind.TRUNCATED

    if not completion.done or completion.done_reason != STOP_FINISH_REASON:
        return ResponseKind.INCOMPLETE

    if completion.message.content is None:
        return ResponseKind.MISSING_RESPONSE

    return ResponseKind.COMPLETED


def parse_completion(reply: HttpReply, identity: ModelIdentity) -> ModelResponse:
    """Retain actual token counts, nanosecond runtime timings and known local API cost."""

    try:
        completion = _Completion.model_validate(reply.body)

        if completion.message.role != "assistant" or completion.model != identity.model_name:
            raise ValueError("Ollama response identity differs from the requested model")

        return ModelResponse(
            identity=identity,
            kind=_response_kind(completion),
            raw_response=completion.message.content,
            raw_http_body=reply.raw_body,
            reported_model=completion.model,
            finish_reason=completion.done_reason,
            duration_ms=reply.duration_ms,
            input_tokens=completion.prompt_eval_count,
            output_tokens=completion.eval_count,
            cost_usd=0.0,
            total_duration_ns=completion.total_duration,
            load_duration_ns=completion.load_duration,
            credentials_redacted=reply.credentials_redacted,
        )
    except ValidationError, ValueError:
        raise protocol_error(
            reply.raw_body, reply.duration_ms, reply.credentials_redacted
        ) from None
