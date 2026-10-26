"""Build versioned source views and validate their original-to-request provenance."""

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, Literal

from extraction_service.diagnostics import order_forms, types
from extraction_service.source_support import cells, field_labels, field_roles, selection
from extraction_service.source_support.cells import (
    CELL_RECORDS_PROFILE,
    SourceRecord,
    read_records,
    render_records,
    text_digest,
)
from extraction_service.source_support.selection import ORDERED_ROWS_PROFILE, select_source_records

ORDERED_ROWS_RAW_FALLBACK_PROFILE: Final[str] = "ordered-rows-raw-fallback-v1"
ORDERED_ROWS_FIELD_ROLES_PROFILE: Final[str] = "ordered-rows-field-roles-v1"

type SourceViewProfile = Literal[
    "cell-records-v1",
    "ordered-rows-v1",
    "ordered-rows-raw-fallback-v1",
    "ordered-rows-field-roles-v1",
]


def view_identity(profile: SourceViewProfile) -> dict[str, Any]:
    """Bind the profile to its source-only implementation files."""

    files = [Path(cells.__file__), Path(__file__)]
    if profile in (
        ORDERED_ROWS_PROFILE,
        ORDERED_ROWS_RAW_FALLBACK_PROFILE,
        ORDERED_ROWS_FIELD_ROLES_PROFILE,
    ):
        files.extend((Path(selection.__file__), Path(order_forms.__file__), Path(types.__file__)))
    if profile == ORDERED_ROWS_FIELD_ROLES_PROFILE:
        files.extend((Path(field_labels.__file__), Path(field_roles.__file__)))
    return {
        "profile": profile,
        "implementation": {
            f"{path.parent.name}/{path.name}": hashlib.sha256(path.read_bytes()).hexdigest()
            for path in files
        },
    }


@dataclass(frozen=True)
class SourceView:
    profile: SourceViewProfile
    original_text: str
    rendered_text: str
    selection: dict[str, Any] | None
    source_map: tuple[dict[str, Any], ...]
    field_roles: dict[str, Any] | None = None

    def evidence(self) -> dict[str, Any]:
        """Retain reversible source, request text and transformation identity."""

        data = asdict(self)
        if self.field_roles is None:
            data.pop("field_roles")
        return {
            **data,
            "original_sha256": text_digest(self.original_text),
            "rendered_sha256": text_digest(self.rendered_text),
            "identity": view_identity(self.profile),
        }


def build_source_view(text: str, profile: SourceViewProfile) -> SourceView:
    """Format source records with optional conservative, explicitly recorded selection."""

    records = read_records(text)
    decision = None
    raw_fallback = False
    excluded: set[int] = set()
    if profile in (
        ORDERED_ROWS_PROFILE,
        ORDERED_ROWS_RAW_FALLBACK_PROFILE,
        ORDERED_ROWS_FIELD_ROLES_PROFILE,
    ):
        selected = select_source_records(text, records)
        decision = asdict(selected)
        excluded = set(selected.excluded_lines)
        raw_fallback = (
            profile in (ORDERED_ROWS_RAW_FALLBACK_PROFILE, ORDERED_ROWS_FIELD_ROLES_PROFILE)
            and not selected.applied
        )
    elif profile != CELL_RECORDS_PROFILE:
        raise ValueError("Unsupported source representation")
    preserved = {
        (cell.reference, cell.label, cell.value)
        for record in records
        if record.number not in excluded
        for cell in record.cells
    }
    retained_records = []
    shared_references: dict[int, list[str]] = {}
    for record in records:
        if record.number not in excluded:
            retained_records.append(record)
            continue
        anchor = record.cells[0]
        shared = [
            cell
            for cell in record.cells
            if cell.row != anchor.row
            or cell.reference.split("!", 1)[0] != anchor.reference.split("!", 1)[0]
        ]
        shared_references[record.number] = [cell.reference for cell in shared]
        remaining = []
        for cell in shared:
            identity = (cell.reference, cell.label, cell.value)
            if identity not in preserved:
                remaining.append(cell)
                preserved.add(identity)
        if remaining:
            retained_records.append(SourceRecord(record.number, record.original, tuple(remaining)))
    rendered = text if raw_fallback else render_records(tuple(retained_records))
    mapping = tuple(
        {
            "source_line": record.number,
            "references": [cell.reference for cell in record.cells],
            "retained": record.number not in excluded,
            "shared_context_references_preserved": shared_references.get(record.number, []),
        }
        for record in records
    )
    role_evidence = None
    if profile == ORDERED_ROWS_FIELD_ROLES_PROFILE:
        cue, role_evidence = field_roles.render_field_role_cues(text)
        role_evidence = {**role_evidence, "cue_applied": cue is not None, "cue_text": cue}
        if cue is not None:
            rendered += cue
    return SourceView(profile, text, rendered, decision, mapping, role_evidence)


def validate_source_view(value: Any, profile: SourceViewProfile, original_sha256: str) -> str:
    """Reconstruct the declared view; checksums alone cannot justify dropped source rows."""

    if not isinstance(value, dict) or value.get("profile") != profile:
        raise ValueError("Source view profile differs from the run")
    identity = value.get("identity")
    if not isinstance(identity, dict) or identity.get("profile") != profile:
        raise ValueError("Source view implementation profile differs")
    implementation = identity.get("implementation")
    if (
        not isinstance(implementation, dict)
        or not implementation
        or any(
            not isinstance(name, str)
            or not isinstance(digest, str)
            or re.fullmatch(r"[a-f0-9]{64}", digest) is None
            for name, digest in implementation.items()
        )
    ):
        raise ValueError("Source view implementation evidence is missing")
    original = value.get("original_text")
    rendered = value.get("rendered_text")
    if not isinstance(original, str) or not isinstance(rendered, str):
        raise ValueError("Source view text is missing")
    if text_digest(original) != original_sha256 or value.get("original_sha256") != original_sha256:
        raise ValueError("Source view original differs from the approved input")
    if text_digest(rendered) != value.get("rendered_sha256"):
        raise ValueError("Source view rendered hash differs")
    expected = build_source_view(original, profile).evidence()
    for key in ("rendered_text", "selection", "source_map"):
        # JSON serialization converts the operational tuples to arrays.
        if json.dumps(value.get(key), sort_keys=True) != json.dumps(expected[key], sort_keys=True):
            raise ValueError("Source view does not preserve its declared source transformation")
    if profile == ORDERED_ROWS_FIELD_ROLES_PROFILE:
        if json.dumps(value.get("field_roles"), sort_keys=True) != json.dumps(
            expected.get("field_roles"), sort_keys=True
        ):
            raise ValueError("Source view field-role evidence differs from its source")
    return rendered
