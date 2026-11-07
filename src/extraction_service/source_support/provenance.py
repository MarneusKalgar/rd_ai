"""Exact original-text references; literal occurrence never establishes a field role."""

import hashlib
import json
from typing import Any, Final

from extraction_service.source_support.cells import read_records
from extraction_service.source_support.field_roles import assess_field_roles

MAX_SOURCE_BYTES: Final[int] = 4 * 1024 * 1024
MAX_LINES: Final[int] = 10_000
MAX_CANDIDATES: Final[int] = 64
MAX_ASSESSMENT_BYTES: Final[int] = 128 * 1024 * 1024
FIELDS: Final[tuple[str, ...]] = (
    "purchaseOrderNumber",
    "buyerProductIdentifier",
    "buyerDeliveryDate",
)


def reference(text: str, start: int, end: int) -> dict[str, Any]:
    """Bind a nonempty UTF-8 slice to the exact original source bytes."""

    raw = text.encode("utf-8")
    if not 0 <= start < end <= len(raw):
        raise ValueError("Invalid source range")
    raw[:start].decode("utf-8")
    quote = raw[start:end].decode("utf-8")
    return {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "start": start,
        "end": end,
        "quote": quote,
    }


def validate_reference(text: str, value: dict[str, Any]) -> None:
    """Reject changed quotes, hashes, ranges and incomplete UTF-8 characters."""

    if type(value.get("start")) is not int or type(value.get("end")) is not int:
        raise ValueError("Source offsets must be integers")
    if reference(text, value["start"], value["end"]) != value:
        raise ValueError("Source reference differs from original bytes")


def occurrences(text: str, value: str | None) -> dict[str, Any]:
    """Retain bounded exact occurrences, including overlapping repeated values."""

    if value is None:
        return {"status": "null_value", "references": [], "overflow": False}
    if not value:
        raise ValueError("Empty extraction literal")
    raw = text.encode("utf-8")
    needle = value.encode("utf-8")
    found: list[dict[str, Any]] = []
    offset = 0
    while (position := raw.find(needle, offset)) >= 0:
        if len(found) == MAX_CANDIDATES:
            return {"status": "ambiguous", "references": found, "overflow": True}
        found.append(reference(text, position, position + len(needle)))
        offset = position + 1
    status = "no_exact_occurrence" if not found else "exact" if len(found) == 1 else "ambiguous"
    return {"status": status, "references": found, "overflow": False}


def _cell_locations(text: str, cells: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], bool]:
    """Locate complete records for inherited cells; never choose a duplicate cell."""

    records = read_records(text)
    offsets = []
    offset = 0
    for record in records:
        offsets.append(offset)
        offset += len(record.original.encode("utf-8"))
    refs = []
    complete = True
    for cell in cells:
        matches = [
            index
            for index, record in enumerate(records)
            if any(
                source.reference == cell["reference"]
                and source.label == cell["label"]
                and source.value == cell["value"]
                for source in record.cells
            )
        ]
        if len(matches) != 1:
            complete = False
            continue
        index = matches[0]
        record = records[index]
        refs.append(
            {
                "role": "source_record_context",
                "cell": cell,
                "span": reference(
                    text, offsets[index], offsets[index] + len(record.original.encode("utf-8"))
                ),
            }
        )
    return refs, complete


def assess_fields(text: str, extraction: dict[str, Any] | None) -> dict[str, Any]:
    """Attach locations to inherited findings without changing their semantic verdicts."""

    if len(text.encode("utf-8")) > MAX_SOURCE_BYTES:
        raise ValueError("Source resource limit exceeded")
    if extraction is None:
        return {
            "status": "unusable_extraction",
            "fields": [],
            "inherited": assess_field_roles(text, extraction),
        }
    rows = extraction.get("lineItems")
    if not isinstance(rows, list) or not rows or len(rows) > MAX_LINES:
        raise ValueError("Invalid extraction row population")
    inherited = assess_field_roles(text, extraction)
    values = [("/purchaseOrderNumber", extraction.get("purchaseOrderNumber"))]
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError("Invalid extraction row")
        for field in FIELDS[1:]:
            values.append((f"/lineItems/{index}/{field}", row.get(field)))
    by_path = {item["output_path"]: item for item in inherited["findings"]}
    findings = []
    serialized = 0
    for path, value in values:
        if value is not None and not isinstance(value, str):
            raise ValueError("Invalid extraction scalar")
        semantic = by_path.get(path)
        context = []
        linked = False
        if semantic is not None and semantic["source_resolution"] is not None:
            cells = semantic["source_resolution"]["cells"]
            # Absence needs the entire closed-source audit, not an invented blank.
            if not cells or semantic["reason"] in (
                "no_explicit_buyer_code",
                "no_explicit_line_date",
            ):
                context = [
                    {"role": "closed_source_scope", "span": reference(text, 0, len(text.encode()))}
                ]
                linked = bool(inherited["source"]["recognized"])
            else:
                context, linked = _cell_locations(text, cells)
        finding = {
            "output_path": path,
            "value": value,
            "location": occurrences(text, value),
            "inherited_support": semantic,
            "support_status": "unknown" if semantic is None else semantic["status"],
            "context": context,
            "linkage": "resolved" if linked else "unresolved",
        }
        serialized += len(json.dumps(finding).encode("utf-8"))
        if serialized > MAX_ASSESSMENT_BYTES:
            raise ValueError("Provenance assessment resource limit exceeded")
        findings.append(finding)
    return {"status": "assessed", "fields": findings, "inherited": inherited}


def validate_assessment(
    text: str, extraction: dict[str, Any] | None, saved: dict[str, Any]
) -> None:
    """Recompute paths, roles and locations; valid quotes alone do not validate linkage."""

    if json.dumps(saved, sort_keys=True) != json.dumps(
        assess_fields(text, extraction), sort_keys=True
    ):
        raise ValueError("Provenance differs from bound source/output")
