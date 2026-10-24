"""Recognize explicit quantity columns in three prepared order-form layouts."""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from extraction_service.diagnostics.types import (
    DiagnosticReason,
    ParsedOrderForm,
    QuantityEvidence,
    SourceRow,
)

CELL_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:(?P<sheet>[^!|]+)!)?(?P<column>[A-Z]{1,3})(?P<row>[1-9][0-9]*) "
    r"(?P<label>[^:|]+): (?P<value>.*)"
)
DECIMAL_PATTERN: Final[re.Pattern[str]] = re.compile(r"[0-9]+(?:\.[0-9]+)?")
BLANK_CELL: Final[str] = "[blank]"


@dataclass(frozen=True)
class OrderFormProfile:
    id: str
    product_column: str
    product_label: str
    description_column: str
    description_label: str
    quantity_column: str
    quantity_label: str


PROFILES: Final[tuple[OrderFormProfile, ...]] = (
    OrderFormProfile(
        id="hu-entered-order-quantity-v1",
        product_column="A",
        product_label="Termék kódja",
        description_column="B",
        description_label="Megnevezés",
        quantity_column="C",
        quantity_label="Rendelt mennyiség",
    ),
    OrderFormProfile(
        id="nl-entered-order-quantity-v1",
        product_column="E",
        product_label="Artikelcode",
        description_column="C",
        description_label="Omschrijving",
        quantity_column="F",
        quantity_label="Aantal",
    ),
    OrderFormProfile(
        id="ro-entered-order-quantity-v1",
        product_column="B",
        product_label="Cod produs",
        description_column="C",
        description_label="Nume produs",
        quantity_column="D",
        quantity_label="Comanda",
    ),
)


def _quantity_evidence(value: str | None) -> QuantityEvidence:
    if value == BLANK_CELL:
        return QuantityEvidence.BLANK

    if value is not None and DECIMAL_PATTERN.fullmatch(value) and Decimal(value) > 0:
        return QuantityEvidence.POSITIVE

    # Zero, missing fields and unfamiliar numeric representations are not proof
    # of catalog membership under this deliberately narrow first candidate.
    return QuantityEvidence.UNKNOWN


def parse_order_form(text: str) -> ParsedOrderForm:
    """Read known labeled rows without consulting case IDs, gold or annotations.

    Unrecognized/mixed structures and duplicate source references yield unknown.
    Shared unit cells on a different spreadsheet row are permitted; product,
    description and ordered-quantity evidence must refer to the product row.
    """

    rows: list[SourceRow] = []
    profile_ids: set[str] = set()
    references: set[str] = set()

    for number, line in enumerate(text.splitlines(), start=1):
        relevant = any(
            f" {profile.description_label}:" in line or f" {profile.product_label}:" in line
            for profile in PROFILES
        )

        if not relevant:
            continue

        matches = [CELL_PATTERN.fullmatch(part.strip()) for part in line.split(" | ")]

        if not matches or any(match is None for match in matches):
            return ParsedOrderForm(None, (), DiagnosticReason.AMBIGUOUS_SOURCE)

        cells = [match.groupdict() for match in matches if match is not None]
        first = cells[0]
        profile = next(
            (
                p
                for p in PROFILES
                if first["column"] == p.product_column and first["label"] == p.product_label
            ),
            None,
        )

        if profile is None or first["sheet"] is None:
            return ParsedOrderForm(None, (), DiagnosticReason.UNSUPPORTED_LAYOUT)

        profile_ids.add(profile.id)
        reference = f"{first['sheet']}!{first['row']}"
        coordinates = [
            (cell["sheet"] or first["sheet"], cell["column"], cell["row"]) for cell in cells
        ]

        if len(profile_ids) != 1 or reference in references or len(set(coordinates)) != len(cells):
            return ParsedOrderForm(None, (), DiagnosticReason.AMBIGUOUS_SOURCE)

        references.add(reference)
        own_cells = {
            cell["column"]: cell
            for cell in cells
            if (cell["sheet"] or first["sheet"]) == first["sheet"] and cell["row"] == first["row"]
        }
        description = own_cells.get(profile.description_column)
        quantity = own_cells.get(profile.quantity_column)

        if description is None or description["label"] != profile.description_label:
            return ParsedOrderForm(None, (), DiagnosticReason.UNSUPPORTED_LAYOUT)

        if not description["value"] or description["value"] == BLANK_CELL:
            return ParsedOrderForm(None, (), DiagnosticReason.AMBIGUOUS_SOURCE)

        quantity_value = None
        quantity_cell = None

        if quantity is not None and quantity["label"] == profile.quantity_label:
            quantity_value = quantity["value"]
            quantity_cell = f"{first['sheet']}!{profile.quantity_column}{first['row']}"

        rows.append(
            SourceRow(
                reference=reference,
                source_line=number,
                product_name=description["value"],
                quantity_cell=quantity_cell,
                quantity_value=quantity_value,
                quantity_evidence=_quantity_evidence(quantity_value),
                text=line,
            )
        )

    if not rows:
        return ParsedOrderForm(None, (), DiagnosticReason.UNSUPPORTED_LAYOUT)

    return ParsedOrderForm(next(iter(profile_ids)), tuple(rows))
