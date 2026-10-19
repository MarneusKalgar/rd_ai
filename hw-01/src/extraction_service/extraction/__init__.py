"""Shared PO contract boundary for provider and local adapters."""

from extraction_service.extraction.contract import ContractLoadError, ExtractionContract
from extraction_service.extraction.validation import (
    SchemaIdentity,
    ValidationIssue,
    ValidationOutcome,
)

__all__ = [
    "ContractLoadError",
    "ExtractionContract",
    "SchemaIdentity",
    "ValidationIssue",
    "ValidationOutcome",
]
