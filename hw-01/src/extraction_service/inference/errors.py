"""Typed transport failures with explicit retry classification and safe evidence."""

from enum import StrEnum
from typing import Final

from pydantic import ConfigDict, Field

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.runtime_types import NonNegativeFloat, NonNegativeInt, StrictModel

QUOTA_ERROR_CODES: Final[frozenset[str]] = frozenset(
    ("insufficient_quota", "quota_exceeded", "billing_hard_limit_reached", "credits_exhausted")
)


class FailureKind(StrEnum):
    """Internal transport failure categories used by the coordinator's policy."""

    TIMEOUT = "timeout"
    CONNECTION = "connection"
    RATE_LIMIT = "rate_limit"
    AUTHENTICATION = "authentication"
    QUOTA = "quota"
    UNSUPPORTED_REQUEST = "unsupported_request"
    SERVER_ERROR = "server_error"
    PROTOCOL_ERROR = "protocol_error"
    HTTP_ERROR = "http_error"


class FailureEvidence(StrictModel):
    """A request failure without a usable model response, preserving available error text."""

    kind: FailureKind
    retryable: bool
    message: str
    duration_ms: NonNegativeFloat
    status_code: int | None = None
    raw_http_body: str | None = Field(default=None, repr=False)
    retry_after: str | None = None
    credentials_redacted: bool = False
    input_tokens: NonNegativeInt | None = None
    output_tokens: NonNegativeInt | None = None
    cost_usd: NonNegativeFloat | None = None


class _ErrorUsage(StrictModel):
    """Known OpenRouter usage fields, when also supplied on an error envelope."""

    model_config = ConfigDict(extra="ignore")

    prompt_tokens: NonNegativeInt | None = None
    completion_tokens: NonNegativeInt | None = None
    cost: NonNegativeFloat | None = None


def error_usage(raw_body: str) -> _ErrorUsage:
    """Retain checked error accounting; an unusable field never conceals the error."""

    try:
        body = parse_json(raw_body)

        if isinstance(body, dict) and isinstance(body.get("usage"), dict):
            return _ErrorUsage.model_validate(body["usage"])
    except ValueError, RecursionError:
        pass

    return _ErrorUsage()


class ModelTransportError(Exception):
    """Expose typed evidence without retaining an HTTP request or its authorization headers."""

    def __init__(self, evidence: FailureEvidence) -> None:
        self.evidence = evidence

        super().__init__(f"{evidence.kind}: {evidence.message}")


class ModelConfigurationError(ValueError):
    """A known unsupported generation setting rejected before any physical request."""


def classify_http_status(status: int) -> tuple[FailureKind, bool]:
    """Classify status-based transport policy without treating PO errors as outages."""

    if status in (401, 403):
        return FailureKind.AUTHENTICATION, False

    if status == 402:
        return FailureKind.QUOTA, False

    if status == 429:
        return FailureKind.RATE_LIMIT, True

    if status in (408, 504):
        return FailureKind.TIMEOUT, True

    if status in (500, 502, 503):
        return FailureKind.SERVER_ERROR, True

    if status in (400, 404, 405, 413, 422):
        return FailureKind.UNSUPPORTED_REQUEST, False

    return FailureKind.HTTP_ERROR, False


def classify_error_body(status: int, raw_body: str) -> tuple[FailureKind, bool]:
    """Recognize explicit account/quota evidence without guessing from arbitrary prose."""

    if status == 429:
        try:
            body = parse_json(raw_body)
        except ValueError, RecursionError:
            body = None

        if isinstance(body, dict) and isinstance(body.get("error"), dict):
            error = body["error"]

            for field in ("code", "type"):
                if isinstance(error.get(field), str) and error[field] in QUOTA_ERROR_CODES:
                    return FailureKind.QUOTA, False

    return classify_http_status(status)
