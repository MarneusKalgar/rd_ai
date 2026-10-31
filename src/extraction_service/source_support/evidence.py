"""Narrow source completeness/quantity evidence; no extraction repair or gold access."""

from collections import Counter
from decimal import Decimal
from typing import Any

from extraction_service.diagnostics.catalog_rows import check_ordered_rows
from extraction_service.diagnostics.order_forms import DECIMAL_PATTERN, parse_order_form
from extraction_service.diagnostics.types import EvidenceStatus, QuantityEvidence
from extraction_service.extraction.validation import JsonObject


def assess_order_evidence(source_text: str, extraction: JsonObject | None) -> dict[str, Any]:
    """Keep ambiguous identities unknown; supported selection does not prove full correctness."""

    parsed = parse_order_form(source_text)
    diagnostic = check_ordered_rows(source_text, extraction)
    output = None if extraction is None else extraction.get("lineItems")
    if parsed.reason is not None or not isinstance(output, list) or not output:
        return {
            "profile": parsed.profile_id,
            "completeness": "unknown",
            "reason": str(parsed.reason or "unusable_extraction"),
            "missing_source_rows": [],
            "quantity_findings": [],
        }

    source_names = Counter(row.product_name for row in parsed.rows)
    names = [row.get("buyerProductName") for row in output if isinstance(row, dict)]
    output_names = Counter(name for name in names if isinstance(name, str))
    ordered = [row for row in parsed.rows if row.quantity_evidence == QuantityEvidence.POSITIVE]
    unclear = any(row.quantity_evidence == QuantityEvidence.UNKNOWN for row in parsed.rows)
    ambiguous = any(
        source_names[row.product_name] != 1 or output_names[row.product_name] > 1 for row in ordered
    )
    unmatched = any(finding.status == EvidenceStatus.UNKNOWN for finding in diagnostic.findings)
    missing = (
        []
        if unmatched or ambiguous
        else [
            row.reference
            for row in ordered
            if source_names[row.product_name] == 1 and output_names[row.product_name] == 0
        ]
    )
    quantities = []
    for finding, row in zip(diagnostic.findings, output, strict=True):
        candidates = finding.source_rows
        status = "unknown"
        if (
            len(candidates) == 1
            and finding.product_name is not None
            and candidates[0].quantity_evidence == QuantityEvidence.POSITIVE
            and output_names[finding.product_name] == 1
        ):
            value = row.get("buyerProductQuantity") if isinstance(row, dict) else None
            if value is None:
                status = "contradicted"
            elif isinstance(value, str) and DECIMAL_PATTERN.fullmatch(value):
                expected = candidates[0].quantity_value
                assert expected is not None
                status = "supported" if Decimal(value) == Decimal(expected) else "contradicted"
        quantities.append(
            {
                "output_path": finding.output_path,
                "status": status,
                "source_rows": [candidate.reference for candidate in candidates],
            }
        )
    completeness = (
        "contradicted"
        if missing
        else "unknown"
        if unclear or ambiguous or unmatched
        else "supported"
    )
    return {
        "profile": parsed.profile_id,
        "completeness": completeness,
        "missing_source_rows": missing,
        "quantity_findings": quantities,
    }
