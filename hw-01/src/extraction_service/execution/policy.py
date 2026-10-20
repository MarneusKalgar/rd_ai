"""Time and dependency policy, independent of model I/O and record construction."""

import time
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import Final, Protocol

from extraction_service.configuration.models import ExecutionConfig
from extraction_service.execution.reasons import failure_reason
from extraction_service.execution.types import DependencyIdentity
from extraction_service.inference.errors import FailureEvidence, FailureKind
from extraction_service.record_types import ExecutionReason
from extraction_service.runtime_types import NonEmptyText, NonNegativeInt, StrictModel

AVAILABILITY_FAILURES: Final[frozenset[FailureKind]] = frozenset(
    (FailureKind.CONNECTION, FailureKind.TIMEOUT, FailureKind.RATE_LIMIT, FailureKind.SERVER_ERROR)
)
FATAL_FAILURES: Final[frozenset[FailureKind]] = frozenset(
    (FailureKind.AUTHENTICATION, FailureKind.QUOTA, FailureKind.UNSUPPORTED_REQUEST)
)


class Clock(Protocol):
    """Inject monotonic time, wall time for HTTP dates and sleeping together."""

    def monotonic(self) -> float: ...

    def now(self) -> datetime: ...

    def sleep(self, seconds: float) -> None: ...


class SystemClock:
    def monotonic(self) -> float:
        return time.monotonic()

    def now(self) -> datetime:
        return datetime.now(UTC)

    def sleep(self, seconds: float) -> None:
        time.sleep(seconds)


def retry_delay(
    failure: FailureEvidence,
    retry_number: int,
    config: ExecutionConfig,
    now: datetime,
) -> float | None:
    """Respect valid Retry-After without retrying earlier than the server permits.

    An excessive server delay ends this input's retries instead of sleeping
    indefinitely or clamping the delay and sending a premature request.
    """

    delay = min(
        config.backoff_initial_seconds * 2**retry_number,
        config.backoff_max_seconds,
    )
    value = None if failure.retry_after is None else failure.retry_after.strip()

    if value is not None:
        try:
            if value.isascii() and value.isdecimal():
                server_delay = float(value)
            else:
                date = parsedate_to_datetime(value)

                if date.tzinfo is None:
                    raise ValueError("Retry-After date must include a timezone")

                server_delay = max(0.0, (date - now).total_seconds())

            delay = max(delay, server_delay)
        except ValueError, TypeError, OverflowError:
            pass

    return None if delay > config.backoff_max_seconds else delay


class DependencyStop(StrictModel):
    dependency: DependencyIdentity
    reason: NonEmptyText
    consecutive_failures: NonNegativeInt


@dataclass
class DependencyState:
    """Invocation-local state retained across inputs and variants of one route."""

    consecutive_failures: int = 0
    stop_reason: str | None = None

    def completed_response(self) -> None:
        self.consecutive_failures = 0

    def failed_input(self, failure: FailureEvidence, limit: int) -> None:
        if failure.kind in FATAL_FAILURES:
            self.stop_reason = failure_reason(
                ExecutionReason.DEPENDENCY_SETUP_FAILURE, failure.kind
            )
        elif failure.retryable and failure.kind in AVAILABILITY_FAILURES:
            self.consecutive_failures += 1

            if self.consecutive_failures >= limit:
                self.stop_reason = failure_reason(
                    ExecutionReason.DEPENDENCY_UNAVAILABLE, failure.kind
                )
