"""Coordinate the shared PO extraction contract and response validation."""

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.extraction.schema_loading import ContractLoadError as ContractLoadError
from extraction_service.extraction.schema_loading import load_schema
from extraction_service.extraction.validation import JsonObject, SchemaIdentity, ValidationOutcome
from extraction_service.extraction.validation_errors import (
    collect_schema_issues,
    issue_from_json_error,
)


@dataclass(frozen=True)
class ExtractionContract:
    """Own one verified schema and apply its rules throughout an extraction run."""

    identity: SchemaIdentity
    _schema: dict[str, Any] = field(repr=False)
    _validator: Draft202012Validator = field(repr=False)

    @classmethod
    def load(cls, schema_path: Path, *, expected_sha256: str) -> ExtractionContract:
        """Create a contract from the schema approved for the dataset.

        Args:
            schema_path: Path to the versioned extraction schema file.
            expected_sha256: Approved schema hash from the gold manifest.

        Returns:
            A contract reusable for all responses in the run.

        Raises:
            ContractLoadError: Schema loading or verification fails.
        """

        loaded_schema = load_schema(schema_path, expected_sha256=expected_sha256)

        return cls(
            identity=loaded_schema.identity,
            _schema=loaded_schema.document,
            _validator=loaded_schema.validator,
        )

    def schema_for_provider(self) -> dict[str, Any]:
        """Return an independent schema copy for adapter requests.

        Returns:
            A dictionary adapters can modify without affecting local validation.
        """

        return deepcopy(self._schema)

    def validate_json(self, raw_response: str) -> ValidationOutcome:
        """Parse and validate a complete response without repair or coercion.

        Args:
            raw_response: The original response text, including any invalid content.

        Returns:
            The unchanged PO object or structured parsing/schema issues, together
            with the raw response and contract identity for attempt records.
        """

        try:
            parsed_value = parse_json(raw_response)
        except (ValueError, RecursionError) as error:
            issue = issue_from_json_error(error)

            return ValidationOutcome(
                schema=self.identity,
                raw_response=raw_response,
                value=None,
                issues=(issue,),
            )

        issues = collect_schema_issues(self._validator, parsed_value)

        if issues:
            return ValidationOutcome(
                schema=self.identity,
                raw_response=raw_response,
                value=None,
                issues=issues,
            )

        return ValidationOutcome(
            schema=self.identity,
            raw_response=raw_response,
            value=cast(JsonObject, parsed_value),
            issues=(),
        )
