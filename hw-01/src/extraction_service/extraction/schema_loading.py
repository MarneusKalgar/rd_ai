"""Read and verify a frozen schema and prepare its reusable validator."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from jsonschema import Draft202012Validator, FormatChecker, SchemaError

from extraction_service.extraction.constants import DRAFT_2020_12
from extraction_service.extraction.json_parsing import parse_json
from extraction_service.extraction.validation import SchemaIdentity

SCHEMA_FILENAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"(.+)\.(v[0-9]+)\.schema\.json")
UNSUPPORTED_SCHEMA_MESSAGE: Final[str] = "Extraction schema must declare JSON Schema Draft 2020-12"


class ContractLoadError(ValueError):
    """Setup cannot proceed with an unreadable, changed or invalid frozen schema."""


@dataclass(frozen=True)
class LoadedSchema:
    """Verified schema data and validator ready for the contract to own."""

    identity: SchemaIdentity
    document: dict[str, Any]
    validator: Draft202012Validator


def load_schema(schema_path: Path, *, expected_sha256: str) -> LoadedSchema:
    """Read and verify the schema bytes approved for the dataset.

    Args:
        schema_path: Path to a versioned extraction schema file.
        expected_sha256: Approved schema hash from the gold manifest.

    Returns:
        The schema identity, parsed definition and configured date-aware validator.

    Raises:
        ContractLoadError: The file cannot be read, its hash differs, its name
            lacks a version, or its contents are not a valid Draft 2020-12 schema.
    """

    try:
        raw_schema = schema_path.read_bytes()
    except OSError as error:
        raise ContractLoadError(f"Cannot read extraction schema: {schema_path}") from error

    schema_sha256 = hashlib.sha256(raw_schema).hexdigest()

    if schema_sha256 != expected_sha256:
        raise ContractLoadError("Extraction schema hash differs from the approved manifest")

    filename_match = SCHEMA_FILENAME_PATTERN.fullmatch(schema_path.name)

    if filename_match is None:
        raise ContractLoadError("Expected a versioned <name>.v<number>.schema.json file")

    try:
        schema_document = parse_json(raw_schema.decode("utf-8"))

        if not isinstance(schema_document, dict):
            raise ContractLoadError(UNSUPPORTED_SCHEMA_MESSAGE)

        if schema_document.get("$schema") != DRAFT_2020_12:
            raise ContractLoadError(UNSUPPORTED_SCHEMA_MESSAGE)

        Draft202012Validator.check_schema(schema_document)
    except (ValueError, UnicodeError, SchemaError) as error:
        raise ContractLoadError(f"Invalid extraction schema: {error}") from error

    schema_name, schema_version = filename_match.groups()

    identity = SchemaIdentity(
        name=schema_name,
        version=schema_version,
        dialect=DRAFT_2020_12,
        sha256=schema_sha256,
    )

    date_format_checker = FormatChecker(formats=["date"])
    validator = Draft202012Validator(
        schema_document,
        format_checker=date_format_checker,
    )

    return LoadedSchema(
        identity=identity,
        document=schema_document,
        validator=validator,
    )
