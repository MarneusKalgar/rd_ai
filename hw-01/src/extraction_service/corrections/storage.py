"""Revalidate correction provenance and export immutable public evidence bundles."""

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
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.corrections.identifiers import (
    candidate_decision,
    correction_instructions,
    identifier_targets,
)
from extraction_service.corrections.types import (
    CONFIG_SNAPSHOT,
    POLICY_RULES,
    POLICY_VERSION,
    CorrectionCase,
    CorrectionDecision,
    SavedCorrectionCase,
)
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.types import GenerationRequest, ModelIdentity
from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime
from extraction_service.runtime.storage import write_report
from extraction_service.source_support.field_roles import assess_field_roles


def verify_corrections(
    directory: Path, base_dir: Path
) -> tuple[dict[str, Any], list[CorrectionCase]]:
    """Recompute triggers, edit guards and retained outputs from actual candidate responses."""

    header = read_json(confined(directory, "correction-run.json"))
    if header["version"] != POLICY_VERSION or header["state"] != "complete":
        raise ValueError("Correction run must be complete and use the supported policy")
    if json.dumps(header["policy"], sort_keys=True) != json.dumps(POLICY_RULES, sort_keys=True):
        raise ValueError("Correction policy declaration differs")
    if (
        hashlib.sha256(regular_bytes(base_dir / "manifest.json")).hexdigest()
        != header["base_manifest_sha256"]
    ):
        raise ValueError("Correction baseline manifest differs")
    manifest, records = reload_records(base_dir)
    if manifest.run_id != header["base_run_id"] or len(records) != 10:
        raise ValueError("Correction baseline membership differs")
    if set(header["cases"]) != {record.input_id for record in records}:
        raise ValueError("Correction case membership differs")
    experiment = ExperimentConfig.model_validate_json(json.dumps(header["experiment"]))
    if experiment != manifest.experiment:
        raise ValueError("Correction controls differ from baseline")
    config_path = confined(directory, CONFIG_SNAPSHOT)
    if (
        hashlib.sha256(regular_bytes(config_path)).hexdigest() != header["config_sha256"]
        or load_experiment(config_path) != experiment
        or header["schema_sha256"] != manifest.schema_sha256
    ):
        raise ValueError("Correction configuration/schema snapshot differs")
    if not set(header["requests"]).issubset(header["cases"]):
        raise ValueError("Correction request intent membership differs")
    runtime = OllamaRuntime.model_validate_json(
        json.dumps(manifest.setup[experiment.models[0].id]["runtime"])
    )
    identity = runtime.identity(experiment.models[0], native=True)
    if ModelIdentity.model_validate_json(json.dumps(header["identity"])) != identity:
        raise ValueError("Correction run identity differs from baseline")
    contract = ExtractionContract.load(
        directory / SCHEMA_FILENAME, expected_sha256=manifest.schema_sha256
    )
    results = []
    for record in records:
        saved = SavedCorrectionCase.model_validate_json(
            regular_bytes(confined(directory, header["cases"][record.input_id]))
        )
        key = item_key(record.input_id, record.model_id, record.prompt_id, record.sampling_id)
        if (
            saved.base_record_sha256 != manifest.record_sha256[key]
            or saved.input_id != record.input_id
        ):
            raise ValueError("Correction source record differs")
        source = saved.original_source
        instructions = saved.base_instructions
        if hashlib.sha256(source.encode()).hexdigest() != record.input_sha256:
            raise ValueError("Correction original source differs")
        if hashlib.sha256(instructions.encode()).hexdigest() != record.prompt_sha256:
            raise ValueError("Correction base instruction bytes differ")
        result = saved.result
        if result.prior != record.extraction:
            raise ValueError("Correction starting extraction differs")
        intent = header["requests"].get(record.input_id)
        if intent is not None:
            recorded = GenerationRequest.model_validate_json(
                regular_bytes(confined(directory, intent))
            )
            if (
                result.request is None
                or result.admission is None
                or request_fingerprint(recorded) != request_fingerprint(result.request)
                or recorded.timeout_seconds > experiment.execution.request_timeout_seconds
            ):
                raise ValueError("Correction request intent differs from actual request")
        if result.attempt is not None and intent is None:
            raise ValueError("Correction attempt requires a persisted request intent")
        if result.prior is None:
            if (
                result.decision != CorrectionDecision.BASE_UNUSABLE
                or result.retained is not None
                or result.attempt is not None
            ):
                raise ValueError("Unusable baseline cannot claim a correction")
            results.append(result)
            continue
        before = assess_field_roles(source, result.prior)
        targets = identifier_targets(before)
        if result.before != json.loads(json.dumps(before)) or [
            target.model_dump(mode="json") for target in result.targets
        ] != [target.model_dump(mode="json") for target in targets]:
            raise ValueError("Correction source findings/targets differ")
        expected_decision = result.decision
        if not targets:
            unknown = any(
                f["status"] == "unknown"
                for f in before["findings"]
                if f["output_path"].endswith("/buyerProductIdentifier")
            )
            expected_decision = (
                CorrectionDecision.ABSTAINED if unknown else CorrectionDecision.NOT_NEEDED
            )
            if result.attempt is not None or result.request is not None:
                raise ValueError("No-trigger case cannot make a correction call")
        else:
            request = result.request
            rendered = (
                source
                if experiment.source_view is None
                else manifest.setup["source_views"][record.input_id]["rendered_text"]
            )
            if (
                request is None
                or request.instructions
                != correction_instructions(instructions, result.prior, targets)
                or request.source_text != rendered
                or request.sampling != record.sampling
                or request.output_schema != contract.schema_for_provider()
                or request.timeout_seconds > experiment.execution.request_timeout_seconds
            ):
                raise ValueError("Correction request differs from its declared policy")
            if result.admission is not None:
                model = experiment.models[0]
                expected_sha = request_fingerprint(
                    request, thinking=model.thinking, ollama_options=model.ollama_options
                )
                if result.admission.request_sha256 != expected_sha:
                    raise ValueError("Correction admission does not bind the actual request")
                observed_context = manifest.setup[record.model_id]["loaded"]["context_length"]
                if (
                    result.admission.context_length != observed_context
                    or result.admission.output_allowance != record.sampling.max_output_tokens
                    or result.admission.thinking != model.thinking
                ):
                    raise ValueError("Correction admission controls differ from baseline")
            if result.attempt is not None:
                if result.attempt.runtime != ModelRuntime.OLLAMA_NATIVE or result.admission is None:
                    raise ValueError("Correction generation requires admitted native evidence")
                if (
                    result.attempt.kind != AttemptKind.CORRECTION
                    or result.attempt.number != 1
                    or result.attempt.model_name != record.model_name
                    or result.attempt.model_id != record.model_id
                    or result.attempt.runtime_version != identity.runtime_version
                    or result.attempt.model_digest != identity.model_digest
                ):
                    raise ValueError("Correction attempt identity or bound differs from baseline")
                response = result.attempt.response
                candidate = (
                    None
                    if response is None or response.raw_response is None
                    else contract.validate_json(response.raw_response).value
                )
                if candidate != result.candidate:
                    raise ValueError("Correction candidate differs from raw response")
                if result.attempt.outcome == AttemptOutcome.VALID and candidate is not None:
                    expected_decision = candidate_decision(source, result.prior, candidate, targets)
                elif result.attempt.failure is not None:
                    expected_decision = CorrectionDecision.TRANSPORT_FAILED
                else:
                    expected_decision = CorrectionDecision.INVALID
            elif result.decision not in (
                CorrectionDecision.ADMISSION_FAILED,
                CorrectionDecision.SETUP_FAILED,
            ):
                raise ValueError("Triggered correction has no attempt or pre-call stop")
        if expected_decision != result.decision:
            raise ValueError("Correction decision violates its acceptance guard")
        retained = (
            result.candidate if result.decision == CorrectionDecision.APPLIED else result.prior
        )
        if result.retained != retained or result.after != json.loads(
            json.dumps(assess_field_roles(source, retained))
        ):
            raise ValueError("Retained extraction/audit differs from the declared policy")
        results.append(result)
    return header, results


def export_corrections(directory: Path, base_dir: Path, destination: Path) -> dict[str, object]:
    """Copy only declared evidence, with credential checks and an exact byte inventory."""

    header, results = verify_corrections(directory, base_dir)
    if destination.exists():
        raise FileExistsError("Correction export exists")
    selected = [
        "correction-run.json",
        CONFIG_SNAPSHOT,
        SCHEMA_FILENAME,
        *header["cases"].values(),
        *header["requests"].values(),
    ]
    destination.mkdir(parents=True)
    try:
        hashes = {}
        for relative in selected:
            content = regular_bytes(confined(directory, relative))
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            hashes[relative] = hashlib.sha256(content).hexdigest()
        write_report(destination / "files.sha256.json", hashes)
        verify_bundle(destination)
        verify_corrections(destination, base_dir)
    except BaseException:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return {"run_id": header["run_id"], "cases": len(results)}
