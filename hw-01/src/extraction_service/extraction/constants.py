"""Shared extraction protocol values, independent of experiment configuration."""

from typing import Final, Literal

DRAFT_2020_12: Final[str] = "https://json-schema.org/draft/2020-12/schema"
SCHEMA_FILENAME: Final[str] = "purchase-order-extraction.v1.schema.json"

JSON_STAGE: Final[Literal["json"]] = "json"
SCHEMA_STAGE: Final[Literal["schema"]] = "schema"

JSON_SYNTAX: Final[str] = "syntax"
JSON_DUPLICATE_KEY: Final[str] = "duplicate_key"
JSON_NON_FINITE_NUMBER: Final[str] = "non_finite_number"
JSON_DECODER_LIMIT: Final[str] = "decoder"
JSON_NESTING_LIMIT: Final[str] = "nesting"
