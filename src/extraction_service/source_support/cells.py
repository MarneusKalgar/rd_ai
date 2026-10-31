"""Lossless record grouping without field translation, inference or row filtering."""

import hashlib
from dataclasses import dataclass
from typing import Final

from extraction_service.diagnostics.order_forms import CELL_PATTERN

CELL_RECORDS_PROFILE: Final[str] = "cell-records-v1"


@dataclass(frozen=True)
class SourceCell:
    reference: str
    column: str
    row: str
    label: str
    value: str


@dataclass(frozen=True)
class SourceRecord:
    number: int
    original: str
    cells: tuple[SourceCell, ...]


def read_records(text: str) -> tuple[SourceRecord, ...]:
    """Keep each original line, including its ending, and parse only complete cell rows."""

    records = []
    for number, original in enumerate(text.splitlines(keepends=True), start=1):
        line = original.rstrip("\r\n")
        matches = [CELL_PATTERN.fullmatch(part) for part in line.split(" | ")]
        cells: list[SourceCell] = []
        default_sheet = (
            None if not matches or matches[0] is None else matches[0].groupdict()["sheet"]
        )
        if matches and all(match is not None for match in matches):
            for match in matches:
                assert match is not None
                fields = match.groupdict()
                sheet = fields["sheet"] or default_sheet
                if sheet is None:
                    cells = []
                    break
                cells.append(
                    SourceCell(
                        reference=f"{sheet}!{fields['column']}{fields['row']}",
                        column=fields["column"],
                        row=fields["row"],
                        label=fields["label"],
                        value=fields["value"],
                    )
                )
        records.append(SourceRecord(number, original, tuple(cells)))
    return tuple(records)


def render_records(records: tuple[SourceRecord, ...]) -> str:
    """Expose cells on separate lines, retaining logical grouping and exact literals."""

    result = ["SOURCE RECORDS; columns: cell | label | literal value\n"]
    for record in records:
        if not record.cells:
            result.append(record.original)
            if not record.original.endswith(("\n", "\r")):
                result.append("\n")
            continue
        result.append("[SOURCE RECORD]\n")
        for cell in record.cells:
            result.append(f"{cell.reference} | {cell.label} | {cell.value}\n")
        result.append("[/SOURCE RECORD]\n")
    return "".join(result)


def text_digest(text: str) -> str:
    """Hash the exact UTF-8 source or request representation."""

    return hashlib.sha256(text.encode()).hexdigest()
