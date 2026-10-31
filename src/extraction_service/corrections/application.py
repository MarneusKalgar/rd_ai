"""Replay a frozen native gold10 baseline through one guarded correction phase."""

import hashlib
import json
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from extraction_service.application.composition import compose_targets
from extraction_service.application.persistence import RunState, item_key, reload_records
from extraction_service.application.selection import RunOptions
from extraction_service.artifacts import artifact_path, read_checked
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.settings import ApplicationSettings, OllamaMode
from extraction_service.corpus.files import read_input
from extraction_service.corpus.manifests import load_manifests
from extraction_service.corrections.identifiers import IdentifierCorrector
from extraction_service.corrections.types import (
    CONFIG_SNAPSHOT,
    POLICY_RULES,
    POLICY_VERSION,
    CorrectionCase,
    CorrectionDecision,
)
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime.storage import write_report


def run_corrections(
    project: Path,
    *,
    base_run_id: str,
    run_id: str,
    config_file: str,
    source: Literal["runs", "submission"] = "submission",
    on_case: Callable[[str, CorrectionCase], None] | None = None,
) -> Path:
    """Generate no new primaries; execute only source-triggered correction requests.

    Gold answer/annotation files are never read. Frozen membership metadata
    limits this experiment to exact gold10. All baseline records stay unchanged.
    """

    RunOptions(run_id=run_id)
    RunOptions(run_id=base_run_id)
    directory = project / "results/corrections" / run_id
    if directory.exists():
        raise FileExistsError("Correction run exists; automatic replay is disabled")
    if ApplicationSettings.load(project).ollama_mode != OllamaMode.NATIVE:
        raise ValueError("Correction execution requires native Ollama mode")
    base_dir = project / f"results/{source}" / base_run_id
    manifest, records = reload_records(base_dir)
    config_path = artifact_path(project, config_file)
    experiment = load_experiment(config_path)
    if manifest.state != RunState.COMPLETE or experiment != manifest.experiment:
        raise ValueError(
            "Correction must use the complete baseline's unchanged experiment controls"
        )
    if len(experiment.models) != 1 or experiment.models[0].backend != "ollama":
        raise ValueError("Correction experiment accepts one native model only")
    if any(record.runtime != ModelRuntime.OLLAMA_NATIVE for record in records):
        raise ValueError("Provider/Docker baselines are not eligible for this native experiment")
    approved = load_manifests(project / "data")
    if len(records) != 10 or {r.input_id for r in records} != set(approved.gold_by_id):
        raise ValueError("Correction experiment requires exact gold10, not remaining20 or all30")
    cases = {case.input_id: case for case in approved.corpus.cases}
    contract = ExtractionContract.load(
        project / "schemas" / SCHEMA_FILENAME, expected_sha256=approved.gold.schema_sha256
    )
    if manifest.schema_sha256 != contract.identity.sha256:
        raise ValueError("Baseline contract differs from the frozen contract")
    prompts = {prompt.id: prompt for prompt in experiment.prompts}
    for record in records:
        if record.input_sha256 != cases[record.input_id].input_sha256:
            raise ValueError("Baseline input differs from approved source")
        read_checked(artifact_path(project, prompts[record.prompt_id].file), record.prompt_sha256)
    directory.mkdir(parents=True)
    (directory / "cases").mkdir()
    (directory / "requests").mkdir()
    shutil.copyfile(project / "schemas" / SCHEMA_FILENAME, directory / SCHEMA_FILENAME)
    shutil.copyfile(config_path, directory / CONFIG_SNAPSHOT)
    header: dict[str, Any] = {
        "version": POLICY_VERSION,
        "run_id": run_id,
        "base_run_id": base_run_id,
        "base_manifest_sha256": hashlib.sha256(
            (base_dir / "manifest.json").read_bytes()
        ).hexdigest(),
        "base_source": source,
        "state": "running",
        "experiment": experiment.model_dump(mode="json"),
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "schema_sha256": contract.identity.sha256,
        "cases": {},
        "requests": {},
        "policy": dict(POLICY_RULES),
    }
    header_path = directory / "correction-run.json"
    write_report(header_path, header)
    started = time.monotonic()
    try:
        with compose_targets(project, experiment.models, RunOptions(run_id=run_id)) as (
            targets,
            setup,
        ):
            prepared = targets[experiment.models[0].id]
            identity = prepared.target.adapter.identity
            old_setup = manifest.setup[identity.model_id]
            runtime = OllamaRuntime.model_validate_json(json.dumps(old_setup["runtime"]))
            if identity != runtime.identity(experiment.models[0], native=True):
                raise ValueError("Correction installed identity differs from baseline")
            for record in records:
                if (
                    identity.model_name != record.model_name
                    or identity.model_id != record.model_id
                    or identity.runtime != record.runtime
                ):
                    raise ValueError("Correction model/runtime differs from the saved baseline")
            observed = setup[identity.model_id]
            if any(
                observed.get(key) != old_setup.get(key) for key in ("thinking", "tokenizer_sha256")
            ):
                raise ValueError("Correction thinking/tokenizer differs from baseline")
            if observed["loaded"]["context_length"] != old_setup["loaded"]["context_length"]:
                raise ValueError("Correction context differs from baseline")
            header.update(identity=identity.model_dump(mode="json"), setup=setup)
            write_report(header_path, header)
            corrector = IdentifierCorrector(
                contract, prepared.target.adapter, prepared.admission, experiment.execution
            )
            for record in records:
                original = read_input(project / "data", cases[record.input_id])
                rendered = (
                    original
                    if experiment.source_view is None
                    else manifest.setup["source_views"][record.input_id]["rendered_text"]
                )
                instructions = read_checked(
                    artifact_path(project, prompts[record.prompt_id].file), record.prompt_sha256
                )

                def checkpoint(request: GenerationRequest, input_id: str = record.input_id) -> None:
                    relative = f"requests/{input_id}.json"
                    write_report(directory / relative, request.model_dump(mode="json"))
                    header["requests"][input_id] = relative
                    write_report(header_path, header)

                if record.extraction is None:
                    result = CorrectionCase(
                        decision=CorrectionDecision.BASE_UNUSABLE,
                        prior=None,
                        retained=None,
                        before={},
                        after={},
                    )
                else:
                    result = corrector.correct(
                        source=original,
                        rendered_source=rendered,
                        prior=record.extraction,
                        instructions=instructions,
                        sampling=record.sampling,
                        on_request=checkpoint,
                    )
                key = item_key(
                    record.input_id, record.model_id, record.prompt_id, record.sampling_id
                )
                relative = f"cases/{record.input_id}.json"
                write_report(
                    directory / relative,
                    {
                        "input_id": record.input_id,
                        "base_record_sha256": manifest.record_sha256[key],
                        "original_source": original,
                        "base_instructions": instructions,
                        "result": result.model_dump(mode="json"),
                    },
                )
                header["cases"][record.input_id] = relative
                write_report(header_path, header)
                if on_case is not None:
                    on_case(record.input_id, result)
        header["state"] = "complete"
        header["phase_wall_seconds"] = time.monotonic() - started
        write_report(header_path, header)
    except BaseException as error:
        header.update(state="interrupted", error_type=type(error).__name__)
        write_report(header_path, header)
        raise
    return directory
