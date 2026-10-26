"""Source-only identifier ownership and line-date linkage with explicit abstention."""

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import date
from enum import StrEnum
from typing import Any, Final

from extraction_service.diagnostics.types import EvidenceStatus
from extraction_service.extraction.validation import JsonObject
from extraction_service.source_support.cells import SourceCell, read_records
from extraction_service.source_support.field_labels import (
    BUYER_CODES,
    CONTEXT_DATES,
    DELIVERY_DATES,
    KNOWN_FIELDS,
    OTHER_CODES,
    PRODUCT_NAMES,
)

FIELD_ROLES_VERSION: Final[str] = "source-field-roles-v1"


class RoleField(StrEnum):
    IDENTIFIER = "buyerProductIdentifier"
    DELIVERY_DATE = "buyerDeliveryDate"


class RoleReason(StrEnum):
    EXPLICIT_BUYER_CODE = "explicit_buyer_code"
    NO_BUYER_CODE = "no_explicit_buyer_code"
    EXPLICIT_LINE_DATE = "explicit_line_date"
    NO_LINE_DATE = "no_explicit_line_date"
    BLANK_FIELD = "explicit_blank_field"
    AMBIGUOUS_SCOPE = "ambiguous_scope"
    UNSUPPORTED_DATE = "unsupported_date"
    UNKNOWN_SOURCE = "unknown_source"
    UNMATCHED_PRODUCT = "unmatched_product"
    AMBIGUOUS_PRODUCT = "ambiguous_product"
    MISSING_OUTPUT = "missing_output_field"


@dataclass(frozen=True)
class RoleResolution:
    field: RoleField
    resolved: bool
    value: str | None
    reason: RoleReason
    cells: tuple[SourceCell, ...]


@dataclass(frozen=True)
class RoleRow:
    product_cell: SourceCell
    identifier: RoleResolution
    delivery_date: RoleResolution


@dataclass(frozen=True)
class FieldRoleSource:
    recognized: bool
    reason: str
    rows: tuple[RoleRow, ...] = ()
    context_dates: tuple[SourceCell, ...] = ()


def _own_row(cell: SourceCell, product: SourceCell) -> bool:
    return (
        cell.row == product.row
        and cell.reference.split("!", 1)[0] == product.reference.split("!", 1)[0]
    )


def _resolve(
    field: RoleField, candidates: tuple[SourceCell, ...], other: tuple[SourceCell, ...]
) -> RoleResolution:
    if len(candidates) > 1:
        return RoleResolution(field, False, None, RoleReason.AMBIGUOUS_SCOPE, candidates)
    if not candidates:
        reason = (
            RoleReason.NO_BUYER_CODE if field == RoleField.IDENTIFIER else RoleReason.NO_LINE_DATE
        )
        return RoleResolution(field, True, None, reason, other)
    cell = candidates[0]
    if cell.value == "[blank]":
        return RoleResolution(field, True, None, RoleReason.BLANK_FIELD, candidates)
    if not cell.value:
        return RoleResolution(field, False, None, RoleReason.AMBIGUOUS_SCOPE, candidates)
    if field == RoleField.DELIVERY_DATE:
        try:
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", cell.value) is None:
                raise ValueError("Unknown date representation")
            date.fromisoformat(cell.value)
        except ValueError:
            return RoleResolution(field, False, None, RoleReason.UNSUPPORTED_DATE, candidates)
    reason = (
        RoleReason.EXPLICIT_BUYER_CODE
        if field == RoleField.IDENTIFIER
        else RoleReason.EXPLICIT_LINE_DATE
    )
    return RoleResolution(field, True, cell.value, reason, candidates)


def parse_field_roles(text: str) -> FieldRoleSource:
    """Resolve only completely parsed, declared cell labels; never read gold or IDs.

    Unknown labels or free text could qualify ownership/date scope, so they
    invalidate closed-source absence claims. Shared critical cells, multiple
    products per record and unlinked buyer codes also require abstention.
    """

    records = read_records(text)
    if not records or any(not row.cells for row in records):
        return FieldRoleSource(False, "unparsed_source")
    if any(cell.label not in KNOWN_FIELDS for row in records for cell in row.cells):
        return FieldRoleSource(False, "unknown_source_label")
    rows: list[RoleRow] = []
    context: list[SourceCell] = []
    product_cells = [
        cell for record in records for cell in record.cells if cell.label in PRODUCT_NAMES
    ]
    for record in records:
        products = [cell for cell in record.cells if cell.label in PRODUCT_NAMES]
        if not products:
            if any(cell.label in BUYER_CODES for cell in record.cells):
                return FieldRoleSource(False, "unlinked_buyer_code")
            context_cells = [
                cell for cell in record.cells if cell.label in DELIVERY_DATES | CONTEXT_DATES
            ]
            if any(_own_row(cell, product) for cell in context_cells for product in product_cells):
                return FieldRoleSource(False, "unlinked_line_date")
            context.extend(context_cells)
            continue
        if len(products) != 1 or products[0].value in ("", "[blank]"):
            return FieldRoleSource(False, "ambiguous_product_record")
        product = products[0]
        critical = [cell for cell in record.cells if cell.label in BUYER_CODES | DELIVERY_DATES]
        if any(not _own_row(cell, product) for cell in critical):
            return FieldRoleSource(False, "shared_critical_cell")
        buyer = tuple(cell for cell in record.cells if cell.label in BUYER_CODES)
        generic = tuple(cell for cell in record.cells if cell.label in OTHER_CODES)
        dates = tuple(cell for cell in record.cells if cell.label in DELIVERY_DATES)
        rows.append(
            RoleRow(
                product,
                _resolve(RoleField.IDENTIFIER, buyer, generic),
                _resolve(RoleField.DELIVERY_DATE, dates, ()),
            )
        )
    if not rows:
        return FieldRoleSource(False, "no_product_records")
    return FieldRoleSource(True, "declared_cell_roles", tuple(rows), tuple(context))


def assess_field_roles(text: str, extraction: JsonObject | None) -> dict[str, Any]:
    """Compare each uniquely matched output product with its own source roles.

    Missing/duplicated/paraphrased products remain unknown. A supported field
    does not certify row membership, quantity, another field or the whole PO.
    """

    source = parse_field_roles(text)
    lines = None if extraction is None else extraction.get("lineItems")
    if not isinstance(lines, list):
        return {"version": FIELD_ROLES_VERSION, "source": asdict(source), "findings": []}
    source_names = Counter(row.product_cell.value for row in source.rows)
    output_names = Counter(
        row.get("buyerProductName")
        for row in lines
        if isinstance(row, dict) and isinstance(row.get("buyerProductName"), str)
    )
    findings = []
    for index, line in enumerate(lines):
        name = line.get("buyerProductName") if isinstance(line, dict) else None
        matches = [row for row in source.rows if row.product_cell.value == name]
        reason = RoleReason.UNKNOWN_SOURCE
        matched = None
        if source.recognized:
            reason = RoleReason.UNMATCHED_PRODUCT
            if isinstance(name, str) and (source_names[name] > 1 or output_names[name] > 1):
                reason = RoleReason.AMBIGUOUS_PRODUCT
            elif len(matches) == 1:
                matched = matches[0]
        for field in RoleField:
            resolution = None
            status = EvidenceStatus.UNKNOWN
            if matched is not None:
                resolution = (
                    matched.identifier if field == RoleField.IDENTIFIER else matched.delivery_date
                )
                reason = resolution.reason
                if not isinstance(line, dict) or field.value not in line:
                    reason = RoleReason.MISSING_OUTPUT
                elif resolution.resolved:
                    status = (
                        EvidenceStatus.SUPPORTED
                        if line[field.value] == resolution.value
                        else EvidenceStatus.CONTRADICTED
                    )
            findings.append(
                {
                    "output_path": f"/lineItems/{index}/{field.value}",
                    "status": status,
                    "reason": reason,
                    "product_name": name,
                    "source_resolution": None if resolution is None else asdict(resolution),
                }
            )
    return {"version": FIELD_ROLES_VERSION, "source": asdict(source), "findings": findings}


def render_field_role_cues(text: str) -> tuple[str | None, dict[str, Any]]:
    """Render source-derived role cues; abstain instead of inventing missing scope."""

    source = parse_field_roles(text)
    return render_role_evidence(source)


def render_role_evidence(source: FieldRoleSource) -> tuple[str | None, dict[str, Any]]:
    """Render already resolved source roles without changing their values or scope."""

    evidence = {"version": FIELD_ROLES_VERSION, "source": asdict(source)}
    if not source.recognized or any(
        not row.identifier.resolved or not row.delivery_date.resolved for row in source.rows
    ):
        return None, evidence
    names = Counter(row.product_cell.value for row in source.rows)
    explicit = []
    for row in source.rows:
        if row.identifier.value is None and row.delivery_date.value is None:
            continue
        if names[row.product_cell.value] != 1:
            return None, evidence
        explicit.append(
            {
                "product_cell": row.product_cell.reference,
                "product_name": row.product_cell.value,
                "buyer_owned_code": asdict(row.identifier),
                "line_linked_delivery_date": asdict(row.delivery_date),
            }
        )
    data = {
        "explicit_line_roles": explicit,
        "order_context_dates": [asdict(cell) for cell in source.context_dates],
    }
    cue = (
        "\n\nAPPLICATION SOURCE-ROLE EVIDENCE (source-field-roles-v1)\n"
        "This is source provenance, not additional purchase-order data or an example.\n"
        "Generic article/product codes, supplier codes and barcodes alone "
        "do not establish buyer ownership. "
        "Use buyerProductIdentifier only for the explicit buyer-owned code "
        "linked to that product; otherwise null.\n"
        "Order-level delivery/service dates do not establish "
        "buyerDeliveryDate for an individual line. "
        "Use only the explicit line-linked date for that product; otherwise null. "
        "Do not transfer a code/date between products.\n"
        "The complete recognized source was checked. "
        "Explicit line roles and order-only date context follow; "
        "an empty explicit_line_roles list means no populated buyer-owned code "
        "or line-linked delivery date was found.\n"
        + json.dumps(data, ensure_ascii=False, allow_nan=False)
    )
    return cue, evidence
