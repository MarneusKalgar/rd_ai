"""Validation evidence belongs beside an extraction, never inside the PO object."""

from dataclasses import dataclass
from typing import Literal

type JsonValue = str | int | float | bool | None | list[JsonValue] | dict[str, JsonValue]
type JsonObject = dict[str, JsonValue]


@dataclass(frozen=True)
class SchemaIdentity:
    name: str
    version: str
    dialect: str
    sha256: str


@dataclass(frozen=True)
class ValidationIssue:
    stage: Literal["json", "schema"]
    keyword: str
    message: str

    instance_path: str = ""
    schema_path: str | None = None

    line: int | None = None
    column: int | None = None


@dataclass(frozen=True)
class ValidationOutcome:
    schema: SchemaIdentity
    raw_response: str

    value: JsonObject | None
    issues: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return not self.issues
