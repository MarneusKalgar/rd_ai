"""Diagnostic evidence is not an extraction validity decision."""

from dataclasses import dataclass
from enum import StrEnum


class EvidenceStatus(StrEnum):
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"


class QuantityEvidence(StrEnum):
    POSITIVE = "positive"
    BLANK = "blank"
    UNKNOWN = "unknown"


class DiagnosticReason(StrEnum):
    ORDERED_SOURCE_ROW = "ordered_source_row"
    BLANK_ORDER_QUANTITY = "blank_order_quantity"
    UNSUPPORTED_LAYOUT = "unsupported_layout"
    AMBIGUOUS_SOURCE = "ambiguous_source"
    UNMATCHED_PRODUCT = "unmatched_product"
    AMBIGUOUS_PRODUCT = "ambiguous_product"
    REPEATED_OUTPUT_PRODUCT = "repeated_output_product"
    UNCLEAR_ORDER_QUANTITY = "unclear_order_quantity"
    UNUSABLE_EXTRACTION = "unusable_extraction"


@dataclass(frozen=True)
class SourceRow:
    reference: str
    source_line: int
    product_name: str
    quantity_cell: str | None
    quantity_value: str | None
    quantity_evidence: QuantityEvidence
    text: str


@dataclass(frozen=True)
class ParsedOrderForm:
    profile_id: str | None
    rows: tuple[SourceRow, ...]
    reason: DiagnosticReason | None = None


@dataclass(frozen=True)
class RowFinding:
    output_path: str
    product_name: str | None
    status: EvidenceStatus
    reason: DiagnosticReason
    source_rows: tuple[SourceRow, ...]


@dataclass(frozen=True)
class SelectionDiagnostic:
    profile_id: str | None
    status: EvidenceStatus
    reason: DiagnosticReason | None
    source_rows: tuple[SourceRow, ...]
    findings: tuple[RowFinding, ...]
