"""Inspect checked saved outputs without reading gold answers or making model calls."""

import hashlib
from pathlib import Path
from typing import Any, Literal

from extraction_service.application.persistence import item_key, reload_records
from extraction_service.artifacts import artifact_path
from extraction_service.corpus.files import read_input
from extraction_service.corpus.manifests import load_manifests
from extraction_service.diagnostics.reporting import diagnose_runs
from extraction_service.source_support import (
    cells,
    evidence,
    field_labels,
    field_roles,
    selection,
    views,
)
from extraction_service.source_support.evidence import assess_order_evidence
from extraction_service.source_support.views import build_source_view


def assess_saved_runs(
    project_dir: Path, run_ids: list[str], *, source: Literal["runs", "submission"] = "submission"
) -> dict[str, Any]:
    """Keep detection-only completeness/quantity findings apart from original outcomes."""

    legacy = diagnose_runs(project_dir, run_ids, source=source)
    manifests = load_manifests(project_dir / "data")
    cases = {case.input_id: case for case in manifests.corpus.cases}
    runs = []
    for original in legacy["runs"]:
        run_id = original["run_id"]
        _, records = reload_records(artifact_path(project_dir, f"results/{source}/{run_id}"))
        by_key = {item_key(r.input_id, r.model_id, r.prompt_id, r.sampling_id): r for r in records}
        findings = []
        for saved in original["records"]:
            key = item_key(
                saved["input_id"], saved["model_id"], saved["prompt_id"], saved["sampling_id"]
            )
            record = by_key[key]
            text = read_input(project_dir / "data", cases[record.input_id])
            view = build_source_view(text, "ordered-rows-v1")
            findings.append(
                {
                    "input_id": record.input_id,
                    "record_sha256": saved["record_sha256"],
                    "original_status": saved["original_status"],
                    "evidence": assess_order_evidence(text, record.extraction),
                    "selection_eligibility": view.selection,
                    "field_roles": field_roles.assess_field_roles(text, record.extraction),
                }
            )
        runs.append(
            {"run_id": run_id, "manifest_sha256": original["manifest_sha256"], "records": findings}
        )
    files = (
        Path(__file__),
        Path(cells.__file__),
        Path(evidence.__file__),
        Path(selection.__file__),
        Path(views.__file__),
        Path(field_labels.__file__),
        Path(field_roles.__file__),
    )
    return {
        "version": "source-support-assessment-v2",
        "diagnostic_only": True,
        "gold_answers_read": False,
        "legacy_selection_check": legacy,
        "implementation": {
            path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in files
        },
        "runs": runs,
    }
