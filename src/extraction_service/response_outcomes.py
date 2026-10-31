"""Shared translation between response states and unsuccessful attempt outcomes."""

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from extraction_service.inference.types import ResponseKind
from extraction_service.record_types import AttemptOutcome

RESPONSE_OUTCOMES: Final[Mapping[ResponseKind, AttemptOutcome]] = MappingProxyType(
    {
        ResponseKind.REFUSED: AttemptOutcome.REFUSED,
        ResponseKind.TRUNCATED: AttemptOutcome.TRUNCATED,
        ResponseKind.MISSING_RESPONSE: AttemptOutcome.MISSING_RESPONSE,
        ResponseKind.INCOMPLETE: AttemptOutcome.INCOMPLETE,
        ResponseKind.ERROR: AttemptOutcome.MODEL_ERROR,
    }
)
