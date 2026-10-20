"""Format stable reason codes with classified causes without changing JSON values."""

from extraction_service.inference.errors import FailureKind
from extraction_service.record_types import ExecutionReason


def failure_reason(reason: ExecutionReason, cause: FailureKind) -> str:
    return f"{reason.value}:{cause.value}"
