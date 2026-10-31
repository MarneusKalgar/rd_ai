"""Reconstruct stage contracts, request bindings and complete-PO assembly from saved bytes."""

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from extraction_service.application.admission import request_fingerprint
from extraction_service.application.persistence import item_key, reload_records
from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import confined, read_json, regular_bytes
from extraction_service.configuration.loading import load_experiment
from extraction_service.execution.admission import AdmissionEvidence
from extraction_service.execution.evidence import correction_instructions
from extraction_service.execution.types import ExtractionJob
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime
from extraction_service.records import RunRecord
from extraction_service.runtime.storage import write_report
from extraction_service.runtime_types import Identifier, NonNegativeFloat, Sha256, StrictModel
from extraction_service.staged.application import CONFIG_SNAPSHOT
from extraction_service.staged.contracts import (
    POLICY_VERSION,
    SplitStage,
    assemble,
    canonical_bytes,
    policy_rules,
    stage_contract,
    stage_instructions,
)


class SavedSplitCase(StrictModel):
    """Operational wrapper; each nested record is revalidated with its stage contract."""

    input_id: Identifier
    base_record_sha256: Sha256
    stage_records: dict[SplitStage, dict[str, Any]]
    extraction: JsonObject | None
    duration_ms: NonNegativeFloat


def verify_split(
    directory: Path, base_dir: Path
) -> tuple[dict[str, Any], list[SavedSplitCase], dict[SplitStage, list[RunRecord]]]:
    """Recompute projections, controls, request bindings and disjoint assembly offline."""

    header = read_json(confined(directory, "split-run.json"))
    if header["version"] != POLICY_VERSION or header["state"] != "complete":
        raise ValueError("Split run must be complete and use the supported policy")
    baseline, originals = reload_records(base_dir)
    if (
        hashlib.sha256(regular_bytes(base_dir / "manifest.json")).hexdigest()
        != header["base_manifest_sha256"]
        or baseline.run_id != header["base_run_id"]
    ):
        raise ValueError("Split baseline binding differs")
    config_path = confined(directory, CONFIG_SNAPSHOT)
    experiment = load_experiment(config_path)
    if (
        experiment != baseline.experiment
        or experiment.model_dump(mode="json") != header["experiment"]
        or hashlib.sha256(regular_bytes(config_path)).hexdigest() != header["config_sha256"]
        or canonical_bytes(header["policy"]) != canonical_bytes(policy_rules(experiment))
    ):
        raise ValueError("Split controls or declared policy differ")
    identity = ModelIdentity.model_validate_json(json.dumps(header["identity"]))
    model = experiment.models[0]
    runtime = OllamaRuntime.model_validate_json(json.dumps(baseline.setup[model.id]["runtime"]))
    if identity != runtime.identity(model, native=True):
        raise ValueError("Split installed identity differs")
    if set(header["cases"]) != {r.input_id for r in originals} or len(originals) != 10:
        raise ValueError("Split case membership differs")
    if set(header["checkpoints"]) != set(header["cases"]):
        raise ValueError("Split checkpoint membership differs")
    parent = ExtractionContract.load(
        directory / SCHEMA_FILENAME, expected_sha256=baseline.schema_sha256
    )
    if header["schema_sha256"] != parent.identity.sha256:
        raise ValueError("Split authoritative contract differs")
    expected_projections = {}
    contracts = {}
    for stage in SplitStage:
        derived = stage_contract(parent, stage)
        relative = f"projections/{stage.value}.schema.json"
        if regular_bytes(confined(directory, relative)) != canonical_bytes(
            derived.schema_for_provider()
        ):
            raise ValueError("Split stage projection differs from the authoritative schema")
        contracts[stage] = derived
        expected_projections[stage.value] = {"file": relative, "sha256": derived.identity.sha256}
    if header["projections"] != expected_projections:
        raise ValueError("Split projection declarations differ")
    expected_sha = hashlib.sha256(
        canonical_bytes(
            {
                "policy": POLICY_VERSION,
                "config_sha256": header["config_sha256"],
                "projections": expected_projections,
            }
        )
    ).hexdigest()
    if header["experiment_sha256"] != expected_sha:
        raise ValueError("Split experiment identity differs")
    cases = []
    stage_records: dict[SplitStage, list[RunRecord]] = {stage: [] for stage in SplitStage}
    for original in originals:
        case = SavedSplitCase.model_validate_json(
            regular_bytes(confined(directory, header["cases"][original.input_id]))
        )
        key = item_key(
            original.input_id, original.model_id, original.prompt_id, original.sampling_id
        )
        if (
            case.input_id != original.input_id
            or case.base_record_sha256 != baseline.record_sha256[key]
        ):
            raise ValueError("Split source record binding differs")
        base_instructions = header["base_instructions"]
        if hashlib.sha256(base_instructions.encode()).hexdigest() != original.prompt_sha256:
            raise ValueError("Split base instruction prefix differs")
        if set(case.stage_records) != set(SplitStage):
            raise ValueError("Split case must retain both stage records, including failures")
        if set(header["checkpoints"][original.input_id]) != {stage.value for stage in SplitStage}:
            raise ValueError("Split stage checkpoints differ")
        outputs = {}
        for stage in SplitStage:
            record = RunRecord.model_validate_json(
                json.dumps(case.stage_records[stage]), context={"contract": contracts[stage]}
            )
            instructions = stage_instructions(base_instructions, stage)
            sha = hashlib.sha256(instructions.encode()).hexdigest()
            if (
                record.run_id != header["run_id"]
                or record.input_id != original.input_id
                or record.input_sha256 != original.input_sha256
                or record.experiment_sha256 != expected_sha
                or record.prompt_id != f"{original.prompt_id}-{stage.value}"
                or record.prompt_sha256 != sha
                or record.sampling != original.sampling
                or record.model_id != original.model_id
                or record.model_name != original.model_name
                or record.runtime != ModelRuntime.OLLAMA_NATIVE
                or record.dependency is None
                or record.dependency.model_digest != identity.model_digest
                or record.dependency.runtime_version != identity.runtime_version
            ):
                raise ValueError("Split stage job identity or controls differ")
            checkpoint = read_json(
                confined(directory, header["checkpoints"][original.input_id][stage.value])
            )
            job = ExtractionJob.model_validate_json(json.dumps(checkpoint["job"]))
            source = baseline.setup["source_views"][original.input_id]["rendered_text"]
            if (
                job.run_id != record.run_id
                or job.input_id != record.input_id
                or job.input_sha256 != record.input_sha256
                or job.experiment_sha256 != expected_sha
                or job.prompt_id != record.prompt_id
                or job.prompt_sha256 != sha
                or job.instructions != instructions
                or job.source_text != source
                or job.sampling != original.sampling
                or checkpoint["attempts"] != [a.model_dump(mode="json") for a in record.attempts]
            ):
                raise ValueError("Split checkpoint differs from the declared stage request")
            admissions = [
                AdmissionEvidence.model_validate_json(json.dumps(a))
                for a in checkpoint["admissions"]
            ]
            if not len(record.attempts) <= len(admissions) <= len(record.attempts) + 1:
                raise ValueError("Split request admissions differ from attempt history")
            maximum = 2 * (experiment.execution.transport_retries + 1)
            if len(record.attempts) > maximum:
                raise ValueError("Split stage exceeds its configured call bound")
            if any(
                sum(a.kind == kind for a in record.attempts)
                > experiment.execution.transport_retries + 1
                for kind in AttemptKind
            ):
                raise ValueError("Split generation exceeds its transport retry bound")
            for index, attempt in enumerate(record.attempts):
                request_instructions = instructions
                if attempt.kind == AttemptKind.CORRECTION:
                    invalid = next(
                        a for a in record.attempts[:index] if a.outcome == AttemptOutcome.INVALID
                    )
                    request_instructions = correction_instructions(instructions, invalid)
                request = GenerationRequest.from_contract(
                    instructions=request_instructions,
                    source_text=source,
                    contract=contracts[stage],
                    sampling=record.sampling,
                    timeout_seconds=attempt.request_timeout_seconds or 1.0,
                )
                admission = admissions[index]
                if (
                    admission.request_sha256
                    != request_fingerprint(
                        request, thinking=model.thinking, ollama_options=model.ollama_options
                    )
                    or admission.context_length
                    != baseline.setup[model.id]["loaded"]["context_length"]
                    or admission.output_allowance != record.sampling.max_output_tokens
                    or admission.thinking != model.thinking
                ):
                    raise ValueError("Split admission does not bind the actual stage request")
            stage_records[stage].append(record)
            outputs[stage] = record.extraction
        assembled = assemble(parent, outputs[SplitStage.HEADERS], outputs[SplitStage.LINES])
        if case.extraction != assembled:
            raise ValueError("Split final extraction differs from declared disjoint assembly")
        cases.append(case)
    return header, cases, stage_records


def export_split(directory: Path, base_dir: Path, destination: Path) -> dict[str, Any]:
    """Export declared evidence only, with exact hashes and credential scanning."""

    header, cases, _ = verify_split(directory, base_dir)
    if destination.exists():
        raise FileExistsError("Split export exists")
    selected = ["split-run.json", SCHEMA_FILENAME, CONFIG_SNAPSHOT]
    selected.extend(item["file"] for item in header["projections"].values())
    selected.extend(header["cases"].values())
    for stages in header["checkpoints"].values():
        selected.extend(stages.values())
    destination.mkdir(parents=True)
    try:
        for relative in selected:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(regular_bytes(confined(directory, relative)))
        hashes = {
            path: hashlib.sha256((destination / path).read_bytes()).hexdigest() for path in selected
        }
        write_report(destination / "files.sha256.json", hashes)
        verify_bundle(destination)
        verify_split(destination, base_dir)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {"run_id": header["run_id"], "cases": len(cases)}
