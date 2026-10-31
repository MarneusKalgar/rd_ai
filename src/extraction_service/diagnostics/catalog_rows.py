"""Detect catalog-row inclusion without changing extraction or scoring results."""

from collections import Counter

from extraction_service.diagnostics.order_forms import parse_order_form
from extraction_service.diagnostics.types import (
    DiagnosticReason,
    EvidenceStatus,
    QuantityEvidence,
    RowFinding,
    SelectionDiagnostic,
    SourceRow,
)
from extraction_service.extraction.validation import JsonObject


def _classify(
    candidates: tuple[SourceRow, ...],
    repeated_output: bool,
) -> tuple[EvidenceStatus, DiagnosticReason]:
    if not candidates:
        return EvidenceStatus.UNKNOWN, DiagnosticReason.UNMATCHED_PRODUCT

    if all(row.quantity_evidence == QuantityEvidence.BLANK for row in candidates):
        return EvidenceStatus.CONTRADICTED, DiagnosticReason.BLANK_ORDER_QUANTITY

    if len(candidates) != 1:
        return EvidenceStatus.UNKNOWN, DiagnosticReason.AMBIGUOUS_PRODUCT

    if repeated_output:
        return EvidenceStatus.UNKNOWN, DiagnosticReason.REPEATED_OUTPUT_PRODUCT

    if candidates[0].quantity_evidence != QuantityEvidence.POSITIVE:
        return EvidenceStatus.UNKNOWN, DiagnosticReason.UNCLEAR_ORDER_QUANTITY

    return EvidenceStatus.SUPPORTED, DiagnosticReason.ORDERED_SOURCE_ROW


def check_ordered_rows(source_text: str, extraction: JsonObject | None) -> SelectionDiagnostic:
    """Check only output row membership under explicitly recognized source layouts.

    Supported means evidence for this row's selection, not correct field values,
    complete extraction or a passed gold evaluation. Exact product-name matching
    deliberately avoids guessed identity, deduplication and fuzzy matching.
    """

    parsed = parse_order_form(source_text)
    output_rows = None if extraction is None else extraction.get("lineItems")

    if not isinstance(output_rows, list) or not output_rows:
        return SelectionDiagnostic(
            parsed.profile_id,
            EvidenceStatus.UNKNOWN,
            DiagnosticReason.UNUSABLE_EXTRACTION,
            parsed.rows,
            (),
        )

    names = [row.get("buyerProductName") if isinstance(row, dict) else None for row in output_rows]
    occurrences = Counter(name for name in names if isinstance(name, str))
    findings: list[RowFinding] = []

    for index, value in enumerate(names):
        name = value if isinstance(value, str) else None
        candidates = tuple(row for row in parsed.rows if row.product_name == name)

        if parsed.reason is not None:
            status, reason = EvidenceStatus.UNKNOWN, parsed.reason
        else:
            status, reason = _classify(candidates, name is not None and occurrences[name] > 1)

        findings.append(
            RowFinding(
                output_path=f"/lineItems/{index}",
                product_name=name,
                status=status,
                reason=reason,
                source_rows=candidates,
            )
        )

    status = EvidenceStatus.SUPPORTED

    if any(finding.status == EvidenceStatus.UNKNOWN for finding in findings):
        status = EvidenceStatus.UNKNOWN

    if any(finding.status == EvidenceStatus.CONTRADICTED for finding in findings):
        status = EvidenceStatus.CONTRADICTED

    return SelectionDiagnostic(
        parsed.profile_id, status, parsed.reason, parsed.rows, tuple(findings)
    )
