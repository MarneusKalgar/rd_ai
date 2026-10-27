"""Derive stage schemas from the authoritative contract without duplicating PO definitions."""

import hashlib
import json
from copy import deepcopy
from enum import StrEnum
from typing import Any, Final

from jsonschema import Draft202012Validator, FormatChecker

from extraction_service.configuration.models import ExperimentConfig
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject, SchemaIdentity

POLICY_VERSION: Final[str] = "header-lines-split-v1"
LINE_ITEMS: Final[str] = "lineItems"


class SplitStage(StrEnum):
    HEADERS = "headers"
    LINES = "lines"


def policy_rules(experiment: ExperimentConfig) -> dict[str, Any]:
    """Declare changed aggregate allowances alongside unchanged per-stage controls."""

    return {
        "source": "identical_baseline_scoped_body_for_both_stages",
        "order": [stage.value for stage in SplitStage],
        "stage_feedback": False,
        "examples": False,
        "semantic_correction": False,
        "stage_failure_policy": "unchanged_coordinator_with_shared_dependency_stops",
        "stage_input_deadline_seconds": experiment.execution.input_timeout_seconds,
        "maximum_combined_input_deadline_seconds": 2 * experiment.execution.input_timeout_seconds,
        "maximum_primary_output_allowance": 2 * experiment.sampling[0].max_output_tokens,
        "final_validation": "authoritative_parent_schema",
    }


def canonical_bytes(value: Any) -> bytes:
    """Serialize operational evidence and derived schemas for stable byte identities."""

    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def stage_contract(parent: ExtractionContract, stage: SplitStage) -> ExtractionContract:
    """Restrict top-level keys, retaining their exact properties, formats and constraints."""

    schema = parent.schema_for_provider()
    selected = [
        key for key in schema["required"] if (key == LINE_ITEMS) == (stage == SplitStage.LINES)
    ]
    if LINE_ITEMS not in schema["required"] or not selected:
        raise ValueError("Parent contract does not support this stage projection")
    schema["required"] = selected
    schema["properties"] = {key: schema["properties"][key] for key in selected}
    schema["title"] = f"{schema.get('title', 'PO')} / {stage.value} / {POLICY_VERSION}"
    schema["description"] = f"{stage.value} projection of authoritative PO {parent.identity.sha256}"
    Draft202012Validator.check_schema(schema)
    identity = SchemaIdentity(
        name=f"{parent.identity.name}-{stage.value}",
        version=parent.identity.version,
        dialect=parent.identity.dialect,
        sha256=hashlib.sha256(canonical_bytes(schema)).hexdigest(),
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker(formats=["date"]))
    return ExtractionContract(identity=identity, _schema=schema, _validator=validator)


def stage_instructions(original: str, stage: SplitStage) -> str:
    """Change only output scope; the complete frozen business instructions remain a prefix."""

    scope = (
        "Return only the header fields required by the supplied projected schema. "
        "Do not output lineItems. Line-item rules above are reference context only."
        if stage == SplitStage.HEADERS
        else "Return only an object containing lineItems, as required by the projected schema. "
        "Do not output top-level header fields. "
        "Source headers remain context for line interpretation."
    )
    return (
        original
        + f"\n\nAPPLICATION STAGE SCOPE ({POLICY_VERSION}/{stage.value})\n"
        + scope
        + " This stage scope restricts the earlier whole-PO output requirement. "
        "Use the unchanged source and business rules; return only one complete stage JSON object."
    )


def assemble(
    parent: ExtractionContract, headers: JsonObject | None, lines: JsonObject | None
) -> JsonObject | None:
    """Compose distinct declared fields only; a failed stage cannot be replaced or repaired."""

    if headers is None or lines is None:
        return None
    for stage, value in ((SplitStage.HEADERS, headers), (SplitStage.LINES, lines)):
        if not stage_contract(parent, stage).validate_json(json.dumps(value)).is_valid:
            raise ValueError("Stage output violates its derived schema")
    if set(headers) & set(lines):
        raise ValueError("Stage ownership must be disjoint")
    combined = deepcopy({**headers, **lines})
    validation = parent.validate_json(json.dumps(combined))
    if not validation.is_valid:
        raise ValueError("Assembled PO violates the authoritative contract")
    return combined
