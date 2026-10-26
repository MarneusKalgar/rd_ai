"""Expose field-role cues only for independently confirmed ordered source rows."""

from collections import Counter
from dataclasses import asdict, replace
from enum import StrEnum
from typing import Any, Final

from extraction_service.source_support.cells import read_records
from extraction_service.source_support.field_labels import PRODUCT_NAMES
from extraction_service.source_support.field_roles import parse_field_roles, render_role_evidence
from extraction_service.source_support.selection import select_source_records

SCOPE_VERSION: Final[str] = "ordered-row-field-role-scope-v1"


class ScopeReason(StrEnum):
    UNKNOWN_MEMBERSHIP = "unknown_order_membership"
    UNKNOWN_ROLES = "unknown_field_roles"
    SCOPE_MISMATCH = "unmatched_source_scope"
    AMBIGUOUS_PRODUCTS = "ambiguous_scoped_products"
    CONFIRMED_ROWS = "confirmed_ordered_rows"


def render_scoped_role_cues(text: str) -> tuple[str | None, dict[str, Any]]:
    """Recheck selection, then render roles from its exact retained product cells.

    The caller cannot authorize a scope by passing product names or an applied
    flag. Unsupported/ambiguous membership leaves the existing hybrid body alone.
    Role checking does not establish membership; the unchanged selector does.
    """

    records = read_records(text)
    selected = select_source_records(text, records)
    scope: dict[str, Any] = {
        "version": SCOPE_VERSION,
        "selection": asdict(selected),
        "product_cells": [],
        "reason": ScopeReason.UNKNOWN_MEMBERSHIP,
    }
    if not selected.applied:
        return None, {"scope": scope}

    source = parse_field_roles(text)
    if not source.recognized:
        scope["reason"] = ScopeReason.UNKNOWN_ROLES
        return None, {"scope": scope, "source": asdict(source)}

    references = [
        cell.reference
        for record in records
        if record.number not in selected.excluded_lines
        for cell in record.cells
        if cell.label in PRODUCT_NAMES
    ]
    rows = tuple(row for row in source.rows if row.product_cell.reference in references)
    if not references or len(set(references)) != len(references) or len(rows) != len(references):
        scope["reason"] = ScopeReason.SCOPE_MISMATCH
        return None, {"scope": scope}

    names = Counter(row.product_cell.value for row in rows)
    if any(count != 1 for count in names.values()):
        scope["reason"] = ScopeReason.AMBIGUOUS_PRODUCTS
        return None, {"scope": scope}

    scope["product_cells"] = references
    scope["reason"] = ScopeReason.CONFIRMED_ROWS
    cue, evidence = render_role_evidence(replace(source, rows=rows))
    return cue, {**evidence, "scope": scope}
