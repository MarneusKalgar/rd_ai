"""Inspect checked saved runs using source evidence, never gold answer values."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final, Literal

from extraction_service.application.exporting import verify_export
from extraction_service.application.persistence import RunState, item_key, reload_records
from extraction_service.application.selection import RunOptions
from extraction_service.artifacts import artifact_path
from extraction_service.corpus.files import read_input
from extraction_service.corpus.manifests import load_manifests
from extraction_service.diagnostics.catalog_rows import check_ordered_rows
from extraction_service.diagnostics.order_forms import PROFILES
from extraction_service.diagnostics.types import EvidenceStatus

CHECK_ID: Final[str] = "catalog-order-evidence-v1"
CHECK_FILES: Final[tuple[str, ...]] = (
    "types.py",
    "order_forms.py",
    "catalog_rows.py",
    "reporting.py",
)


def diagnose_runs(
    project_dir: Path,
    run_ids: list[str],
    *,
    source: Literal["runs", "submission"] = "submission",
) -> dict[str, Any]:
    """Return repeatable diagnostic evidence without writes, models or gold labels.

    Validate source/run/schema hashes first. Unknown cases remain in the report;
    contradictions do not change run status or cause model correction calls.
    """

    if not run_ids or len(set(run_ids)) != len(run_ids):
        raise ValueError("Choose distinct saved runs")

    if source not in ("runs", "submission"):
        raise ValueError("Unsupported diagnostic source")

    manifests = load_manifests(project_dir / "data")
    cases = {case.input_id: case for case in manifests.corpus.cases}
    report_runs: list[dict[str, Any]] = []
    totals = dict.fromkeys(EvidenceStatus, 0)
    code_hashes = {
        name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
        for name in CHECK_FILES
    }
    definition = json.dumps(code_hashes, sort_keys=True).encode()

    for run_id in run_ids:
        RunOptions(run_id=run_id)
        directory = artifact_path(project_dir, f"results/{source}/{run_id}")

        if source == "submission":
            verify_export(directory)

        manifest, records = reload_records(directory)

        if manifest.run_id != run_id or manifest.state not in (
            RunState.COMPLETE,
            RunState.INCOMPLETE,
        ):
            raise ValueError("Diagnostic requires a matching terminal run")

        if manifest.schema_sha256 != manifests.gold.schema_sha256:
            raise ValueError("Run schema differs from approved corpus")

        results = []

        for record in records:
            case = cases.get(record.input_id)

            if case is None or case.input_sha256 != record.input_sha256:
                raise ValueError("Run source identity differs from approved corpus")

            source_text = read_input(project_dir / "data", case)
            diagnostic = check_ordered_rows(source_text, record.extraction)
            counts = dict.fromkeys(EvidenceStatus, 0)

            for finding in diagnostic.findings:
                counts[finding.status] += 1
                totals[finding.status] += 1

            key = item_key(record.input_id, record.model_id, record.prompt_id, record.sampling_id)
            results.append(
                {
                    "input_id": record.input_id,
                    "model_id": record.model_id,
                    "prompt_id": record.prompt_id,
                    "sampling_id": record.sampling_id,
                    "input_sha256": record.input_sha256,
                    "record_sha256": manifest.record_sha256[key],
                    "original_status": record.status.value,
                    "original_reason": record.reason,
                    "row_counts": counts,
                    "diagnostic": asdict(diagnostic),
                }
            )

        report_runs.append(
            {
                "run_id": run_id,
                "original_state": manifest.state.value,
                "manifest_sha256": hashlib.sha256(
                    (directory / "manifest.json").read_bytes()
                ).hexdigest(),
                "records": results,
            }
        )

    return {
        "version": "row-diagnostics-v1",
        "check_id": CHECK_ID,
        "diagnostic_only": True,
        "gold_answers_read": False,
        "source": source,
        "check_files_sha256": code_hashes,
        "check_sha256": hashlib.sha256(definition).hexdigest(),
        "profiles": [asdict(profile) for profile in PROFILES],
        "row_counts": totals,
        "scope": "Output-row selection evidence only; not field accuracy or completeness",
        "runs": report_runs,
    }
