"""Translate decoder and schema errors into stable, serializable issue records."""

import json
from collections.abc import Iterable

from jsonschema import Draft202012Validator

from extraction_service.extraction.constants import (
    JSON_DECODER_LIMIT,
    JSON_NESTING_LIMIT,
    JSON_STAGE,
    JSON_SYNTAX,
    SCHEMA_STAGE,
)
from extraction_service.extraction.json_parsing import AmbiguousJsonError
from extraction_service.extraction.validation import ValidationIssue


def json_pointer(parts: Iterable[str | int]) -> str:
    """Encode a path as an RFC 6901 pointer, with an empty string for the root."""

    escaped_parts: list[str] = []

    for part in parts:
        escaped_part = str(part).replace("~", "~0").replace("/", "~1")
        escaped_parts.append(escaped_part)

    if not escaped_parts:
        return ""

    return "/" + "/".join(escaped_parts)


def issue_from_json_error(error: ValueError | RecursionError) -> ValidationIssue:
    """Describe a JSON parsing failure without changing decoder error details.

    Args:
        error: A syntax, ambiguity, number-limit or nesting error from parsing.

    Returns:
        One JSON-stage issue, retaining line and column for syntax errors.
    """

    if isinstance(error, json.JSONDecodeError):
        return ValidationIssue(
            stage=JSON_STAGE,
            keyword=JSON_SYNTAX,
            message=error.msg,
            line=error.lineno,
            column=error.colno,
        )

    if isinstance(error, AmbiguousJsonError):
        return ValidationIssue(
            stage=JSON_STAGE,
            keyword=error.keyword,
            message=str(error),
        )

    if isinstance(error, RecursionError):
        return ValidationIssue(
            stage=JSON_STAGE,
            keyword=JSON_NESTING_LIMIT,
            message="JSON nesting exceeds the decoder limit",
        )

    return ValidationIssue(
        stage=JSON_STAGE,
        keyword=JSON_DECODER_LIMIT,
        message=str(error),
    )


def collect_schema_issues(
    validator: Draft202012Validator,
    parsed_value: object,
) -> tuple[ValidationIssue, ...]:
    """Collect all violations in validator order with instance and schema paths.

    Args:
        validator: The validator configured from the frozen extraction schema.
        parsed_value: Decoded response; its type and structure are not yet trusted.

    Returns:
        An empty tuple for valid data, otherwise every schema-stage issue.
    """

    issues: list[ValidationIssue] = []

    for violation in validator.iter_errors(parsed_value):
        issue = ValidationIssue(
            stage=SCHEMA_STAGE,
            keyword=str(violation.validator),
            message=violation.message,
            instance_path=json_pointer(violation.absolute_path),
            schema_path=json_pointer(violation.absolute_schema_path),
        )

        issues.append(issue)

    return tuple(issues)
