"""Explicit local one-token diagnostics with truncation and context shifting disabled."""

from collections.abc import Callable, Iterable
from time import monotonic
from typing import Any

from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.messages import request_messages
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.wire_models import WireModel
from extraction_service.runtime.configuration import ModelPin, SetupSettings
from extraction_service.runtime.context import PreparedRequest
from extraction_service.runtime.errors import SetupError
from extraction_service.runtime_types import NonEmptyText, PositiveInt


class TokenMeasurement(WireModel):
    model: NonEmptyText
    done: bool
    prompt_eval_count: PositiveInt


def measure_capacity(
    client: JsonHttpClient,
    requests: Iterable[PreparedRequest],
    pin: ModelPin,
    settings: SetupSettings,
    *,
    clock: Callable[[], float] = monotonic,
) -> dict[str, Any]:
    """Measure the selected requests; fail closed on missing counts or insufficient room.

    One generated token obtains the runtime's actual full rendered prompt count.
    The pinned server implements truncate=false and shift=false. Reserve the real
    configured output allowance, not the diagnostic's one-token generation limit.
    These are setup measurements, never extraction results or latency samples.
    """

    deadline = clock() + settings.capacity_seconds
    measurements: list[dict[str, Any]] = []
    largest: dict[str, Any] | None = None

    for prepared in requests:
        remaining = deadline - clock()

        if remaining <= 0:
            return {
                "token_capacity_verified": False,
                "blocker": "capacity_deadline_exceeded",
                "measurements": measurements,
            }

        request = prepared.request
        payload = {
            "model": pin.model,
            "messages": request_messages(request),
            "format": request.output_schema,
            "stream": False,
            "truncate": False,
            "shift": False,
            "keep_alive": settings.keep_alive_seconds,
            "options": {
                "num_ctx": settings.context_length,
                "num_predict": 1,
                "temperature": request.sampling.temperature,
                "top_p": request.sampling.top_p,
            },
        }
        try:
            reply = client.post("api/chat", payload, min(settings.measurement_seconds, remaining))
        except ModelTransportError as error:
            return {
                "token_capacity_verified": False,
                "blocker": "local_capacity_request_failed",
                "failed_request": prepared.inventory(),
                "http_status": error.evidence.status_code,
                "kind": error.evidence.kind.value,
                "body": error.evidence.raw_http_body,
                "measurements": measurements,
                "largest_measured": largest,
            }

        measured = TokenMeasurement.model_validate(reply.body)

        if not measured.done or measured.model != pin.model:
            raise SetupError(
                "Capacity diagnostic returned an incomplete or different model response"
            )

        required = measured.prompt_eval_count + request.sampling.max_output_tokens
        item = prepared.inventory()
        item.update(prompt_tokens=measured.prompt_eval_count, required_context_tokens=required)
        measurements.append(item)

        if largest is None or required > largest["required_context_tokens"]:
            largest = item

        if required > settings.context_length:
            return {
                "token_capacity_verified": False,
                "blocker": "insufficient_context",
                "largest_measured": largest,
                "measurements": measurements,
            }

    return {
        "token_capacity_verified": bool(measurements),
        "scope": "selected_initial_and_fixture_correction_requests_only",
        "largest_measured": largest,
        "measurements": measurements,
    }
