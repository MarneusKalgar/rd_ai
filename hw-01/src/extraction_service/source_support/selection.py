"""Optional deterministic selection under narrowly declared order-form conventions."""

from dataclasses import dataclass
from typing import Final

from extraction_service.diagnostics.order_forms import PROFILES, parse_order_form
from extraction_service.diagnostics.types import QuantityEvidence
from extraction_service.source_support.cells import SourceRecord

ORDERED_ROWS_PROFILE: Final[str] = "ordered-rows-v1"
EXTRA_ROW_LABELS: Final[dict[str, frozenset[tuple[str, str]]]] = {
    "hu-entered-order-quantity-v1": frozenset({("D", "Mértékegység"), ("G", "Ár")}),
    "nl-entered-order-quantity-v1": frozenset({("F", "Eenheid")}),
    "ro-entered-order-quantity-v1": frozenset({("D", "Unitate"), ("K", "Preț unitar")}),
}
HEADER_LABELS: Final[dict[str, frozenset[str]]] = {
    "hu-entered-order-quantity-v1": frozenset(
        {
            "Megrendelés dátuma",
            "Ügyfél neve",
            "Szállítási cím",
            "Fizetési feltétel",
            "A rendelés összértéke",
            "Delivery date",
        }
    ),
    "nl-entered-order-quantity-v1": frozenset(
        {"PO nummer", "Order datum", "Leveradres", "Delivery date"}
    ),
    "ro-entered-order-quantity-v1": frozenset(
        {
            "Data emiterii comenzii",
            "Firma",
            "Moneda",
            "Valoare comandă fără TVA",
            "Requested delivery date",
        }
    ),
}


@dataclass(frozen=True)
class SourceSelection:
    applied: bool
    reason: str
    profile_id: str | None
    excluded_lines: tuple[int, ...] = ()


def select_source_records(text: str, records: tuple[SourceRecord, ...]) -> SourceSelection:
    """Abstain for unknown quantities, extra item evidence or unfamiliar headers.

    Retain headers and shared unit/date cells. Only recognized explicit blank
    catalog rows can be excluded; unknown cases keep the full source. No case
    IDs, labels, model outputs or universal non-null-quantity rule are used.
    """

    parsed = parse_order_form(text)
    if parsed.reason is not None or parsed.profile_id is None:
        return SourceSelection(False, "unsupported_or_ambiguous_source", parsed.profile_id)
    if any(row.quantity_evidence == QuantityEvidence.UNKNOWN for row in parsed.rows):
        return SourceSelection(False, "unknown_quantity_evidence", parsed.profile_id)
    if not any(row.quantity_evidence == QuantityEvidence.POSITIVE for row in parsed.rows):
        return SourceSelection(False, "no_explicit_positive_order", parsed.profile_id)
    profile = next(profile for profile in PROFILES if profile.id == parsed.profile_id)
    allowed = EXTRA_ROW_LABELS[profile.id] | {
        (profile.product_column, profile.product_label),
        (profile.description_column, profile.description_label),
        (profile.quantity_column, profile.quantity_label),
    }
    product_lines = {row.source_line for row in parsed.rows}
    shared_cells: dict[str, tuple[str, str]] = {}
    for record in records:
        if not record.cells:
            return SourceSelection(False, "unparsed_source_evidence", profile.id)
        if record.number in product_lines:
            if any((cell.column, cell.label) not in allowed for cell in record.cells):
                return SourceSelection(False, "additional_item_evidence", profile.id)
            anchor = record.cells[0]
            for cell in record.cells:
                if (
                    cell.row != anchor.row
                    or cell.reference.split("!", 1)[0] != anchor.reference.split("!", 1)[0]
                ):
                    value = (cell.label, cell.value)
                    if cell.reference in shared_cells and shared_cells[cell.reference] != value:
                        return SourceSelection(False, "conflicting_shared_cell", profile.id)
                    shared_cells[cell.reference] = value
        elif any(cell.label not in HEADER_LABELS[profile.id] for cell in record.cells):
            return SourceSelection(False, "unfamiliar_header_evidence", profile.id)
    excluded = tuple(
        row.source_line for row in parsed.rows if row.quantity_evidence == QuantityEvidence.BLANK
    )
    return SourceSelection(True, "recognized_blank_catalog_rows_only", profile.id, excluded)
