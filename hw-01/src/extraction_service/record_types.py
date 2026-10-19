"""Typed record protocol values, keeping strict string inputs and JSON output."""

from typing import Final, Literal

type AttemptKind = Literal["extraction", "correction"]
type AttemptOutcome = Literal["valid", "invalid", "transport_error", "refused", "truncated"]
type ModelRuntime = Literal["openrouter", "ollama-docker", "ollama-native"]
type RunStatus = Literal["succeeded", "failed", "not_attempted"]

EXTRACTION_ATTEMPT: Final[AttemptKind] = "extraction"
VALID_OUTCOME: Final[AttemptOutcome] = "valid"
INVALID_OUTCOME: Final[AttemptOutcome] = "invalid"
TRANSPORT_ERROR_OUTCOME: Final[AttemptOutcome] = "transport_error"
TRUNCATED_OUTCOME: Final[AttemptOutcome] = "truncated"
VALIDATED_OUTCOMES: Final[frozenset[AttemptOutcome]] = frozenset((VALID_OUTCOME, INVALID_OUTCOME))

SUCCEEDED_STATUS: Final[RunStatus] = "succeeded"
NOT_ATTEMPTED_STATUS: Final[RunStatus] = "not_attempted"
FIRST_ATTEMPT_NUMBER: Final[int] = 1
CONTRACT_CONTEXT_KEY: Final[str] = "contract"
