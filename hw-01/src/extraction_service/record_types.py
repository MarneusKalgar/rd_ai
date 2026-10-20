"""Typed record protocol values, keeping strict string inputs and JSON output."""

from enum import StrEnum
from typing import Final


class AttemptKind(StrEnum):
    """Generation purpose; transport retries retain their generation's purpose."""

    EXTRACTION = "extraction"
    CORRECTION = "correction"


class AttemptOutcome(StrEnum):
    """Internal physical-request outcomes, independent of provider finish strings."""

    VALID = "valid"
    INVALID = "invalid"
    TRANSPORT_ERROR = "transport_error"
    REFUSED = "refused"
    TRUNCATED = "truncated"
    MISSING_RESPONSE = "missing_response"
    INCOMPLETE = "incomplete"
    MODEL_ERROR = "model_error"
    DEADLINE_EXCEEDED = "deadline_exceeded"


class ModelRuntime(StrEnum):
    """Execution environments retained in measured results."""

    OPENROUTER = "openrouter"
    OLLAMA_DOCKER = "ollama-docker"
    OLLAMA_NATIVE = "ollama-native"


class RunStatus(StrEnum):
    """Final input/variant status, distinct from physical-request outcomes."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    NOT_ATTEMPTED = "not_attempted"


class ExecutionReason(StrEnum):
    """Stable reason codes; provider prose remains ordinary text."""

    INPUT_DEADLINE_EXCEEDED = "input_deadline_exceeded"
    INVALID_OUTPUT = "invalid_output"
    EXECUTION_FAILED = "execution_failed"
    RETRY_AFTER_EXCEEDS_BACKOFF_LIMIT = "retry_after_exceeds_backoff_limit"
    TRANSPORT_FAILURE = "transport_failure"
    DEPENDENCY_SETUP_FAILURE = "dependency_setup_failure"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"


VALIDATED_OUTCOMES: Final[frozenset[AttemptOutcome]] = frozenset(
    (AttemptOutcome.VALID, AttemptOutcome.INVALID)
)
FIRST_ATTEMPT_NUMBER: Final[int] = 1
CONTRACT_CONTEXT_KEY: Final[str] = "contract"


class ExecutionStage(StrEnum):
    """Budget membership; changing stage never creates a new spending allowance."""

    SMOKE = "smoke"
    SCREENING = "screening"
    MATRIX = "matrix"
    REPETITION = "repetition"
