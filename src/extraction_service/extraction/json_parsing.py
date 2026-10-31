"""Parse the complete model response without salvaging or normalizing its content."""

import json
from typing import Any, Never

from extraction_service.extraction.constants import JSON_DUPLICATE_KEY, JSON_NON_FINITE_NUMBER


class AmbiguousJsonError(ValueError):
    """A decoder extension would otherwise silently change the response's meaning."""

    def __init__(self, keyword: str, message: str) -> None:
        super().__init__(message)

        self.keyword = keyword


def reject_constant(value: str) -> Never:
    raise AmbiguousJsonError(JSON_NON_FINITE_NUMBER, f"{value} is not a JSON number")


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}

    for key, value in pairs:
        if key in result:
            raise AmbiguousJsonError(JSON_DUPLICATE_KEY, f"Duplicate JSON object key: {key!r}")

        result[key] = value

    return result


def parse_json(raw_response: str) -> Any:
    """Parse a complete JSON document with duplicate and non-finite checks.

    Args:
        raw_response: Original schema or response text; surrounding commentary
            and Markdown fences are not removed.

    Returns:
        Decoded JSON data whose application-level structure is not yet validated.

    Raises:
        json.JSONDecodeError: The text is not one complete JSON document.
        AmbiguousJsonError: Duplicate keys or non-JSON numeric constants occur.
        ValueError: A decoder number limit is exceeded.
        RecursionError: Nesting exceeds the decoder's supported depth.
    """

    return json.loads(
        raw_response,
        object_pairs_hook=unique_object,
        parse_constant=reject_constant,
    )
