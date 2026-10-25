"""Select public evidence from checked membership and explicit provenance references."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from extraction_service.application.persistence import RunManifest, item_key, reload_records
from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import confined, digest, read_json
from extraction_service.archiving.models import BundleInfo, safe_name
from extraction_service.records import RunRecord
from extraction_service.runtime_types import StrictModel


class Selection(StrictModel):
    membership: str
    evidence_index: str | None = None


class Selections(StrictModel):
    selections: dict[str, Selection]


@dataclass(frozen=True)
class SelectedEvidence:
    bundles: tuple[BundleInfo, ...]
    membership_sha256: str
    evidence_index_sha256: str | None
    covered_observations: int
    membership_json: str


def _check_member(
    manifest: RunManifest, records: dict[str, RunRecord], entry: dict[str, Any]
) -> None:
    run_id = entry["source_run_id"]
    key = item_key(entry["input_id"], entry["model_id"], entry["prompt_id"], entry["sampling_id"])
    record = records.get(key)

    if record is None or not record.attempts:
        raise ValueError("Covered membership must have original attempted evidence")

    if (
        manifest.record_sha256.get(key) != entry["source_record_sha256"]
        or entry["source_record_path"] != f"results/runs/{run_id}/{manifest.records.get(key)}"
        or record.input_sha256 != entry["input_sha256"]
        or record.schema_sha256 != entry["schema_sha256"]
        or ("prompt_sha256" in entry and record.prompt_sha256 != entry["prompt_sha256"])
        or record.status.value != entry["result_status"]
    ):
        raise ValueError("Membership record identity or hash differs")


def verify_membership(submission: Path, membership: dict[str, Any]) -> tuple[set[str], int]:
    """Check every covered observation against its original terminal source record."""

    if membership.get("version") != "matrix-membership-v1":
        raise ValueError("Unsupported membership version")

    entries = membership["entries"]
    identities = [
        (entry["input_id"], entry["model_id"], entry["prompt_id"], entry["sampling_id"])
        for entry in entries
    ]

    if not entries or len(identities) != len(set(identities)):
        raise ValueError("Membership is empty or contains duplicate observations")

    covered = [entry for entry in entries if entry["status"] == "covered"]

    if not covered or len(covered) != membership["covered_observations"]:
        raise ValueError("Membership covered count differs")

    checked: dict[str, tuple[RunManifest, dict[str, RunRecord], str]] = {}

    for entry in covered:
        run_id = safe_name(entry["source_run_id"])

        if run_id not in checked:
            directory = confined(submission, run_id)
            verify_bundle(directory)
            manifest, records = reload_records(directory)
            by_key = {
                item_key(
                    record.input_id, record.model_id, record.prompt_id, record.sampling_id
                ): record
                for record in records
            }
            checked[run_id] = manifest, by_key, digest(directory / "manifest.json")

        manifest, by_key, manifest_hash = checked[run_id]

        if manifest_hash != entry["source_manifest_sha256"]:
            raise ValueError("Membership manifest hash differs")

        _check_member(manifest, by_key, entry)

    return set(checked), len(covered)


def select_evidence(project: Path, config_file: str, name: str) -> SelectedEvidence:
    """Fail on missing, ambiguous or changed evidence rather than selecting by age."""

    config_path = confined(project, config_file)
    config = Selections.model_validate_json(json.dumps(yaml.safe_load(config_path.read_text())))
    selection = config.selections[name]
    membership_path = confined(project, selection.membership)
    membership = read_json(membership_path)
    names, covered_count = verify_membership(project / "results/submission", membership)
    index_hash = None

    if selection.evidence_index is not None:
        index_path = confined(project, selection.evidence_index)
        index = read_json(index_path)
        index_hash = digest(index_path)

        for reference in index["bundles"]:
            relative = reference["path"]
            parts = relative.split("/")

            if len(parts) != 3 or parts[:2] != ["results", "submission"]:
                raise ValueError("Provenance references must identify public submission bundles")

            directory = confined(project, relative)
            bundle = verify_bundle(directory)

            if bundle.inventory_sha256 != reference["source_inventory_sha256"]:
                raise ValueError("Provenance inventory hash differs")

            if reference.get("source_manifest_sha256") is not None:
                if digest(directory / "manifest.json") != reference["source_manifest_sha256"]:
                    raise ValueError("Provenance manifest hash differs")

            names.add(safe_name(parts[2]))

    bundles = tuple(
        verify_bundle(confined(project, f"results/submission/{name}")) for name in sorted(names)
    )

    return SelectedEvidence(
        bundles, digest(membership_path), index_hash, covered_count, membership_path.read_text()
    )
