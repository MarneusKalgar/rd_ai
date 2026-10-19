"""Typed transport failures with explicit retry classification and safe evidence."""

from enum import StrEnum

from pydantic import Field

from extraction_service.runtime_types import NonNegativeFloat, StrictModel


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


class ModelTransportError(Exception):
    """Expose typed evidence without retaining an HTTP request or its authorization headers."""

    def __init__(self, evidence: FailureEvidence) -> None:
        self.evidence = evidence

        super().__init__(f"{evidence.kind}: {evidence.message}")


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
