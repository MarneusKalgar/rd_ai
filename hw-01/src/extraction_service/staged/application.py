"""One native gold10 split phase, persisting both independent stage outputs and failures."""

import hashlib
import json
import shutil
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from extraction_service.application.composition import compose_targets
from extraction_service.application.persistence import RunState, item_key, reload_records
from extraction_service.application.selection import RunOptions
from extraction_service.artifacts import artifact_path, read_checked
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.settings import ApplicationSettings, OllamaMode
from extraction_service.corpus.files import read_input
from extraction_service.corpus.manifests import load_manifests
from extraction_service.execution.types import ExtractionJob, InputExecution
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime.storage import write_report
from extraction_service.staged.contracts import (
    POLICY_VERSION,
    SplitStage,
    canonical_bytes,
    policy_rules,
    stage_contract,
)
from extraction_service.staged.extractor import SplitExtractor, SplitResult

CONFIG_SNAPSHOT = "experiment-source.yaml"


def run_split(
    project: Path,
    *,
    base_run_id: str,
    run_id: str,
    config_file: str = "config/gemma-scoped-roles.yaml",
    on_case: Callable[[str, SplitResult], None] | None = None,
) -> Path:
    """Use saved baseline metadata/source views, never its predictions or gold answers."""

    RunOptions(run_id=run_id)
    RunOptions(run_id=base_run_id)
    directory = project / "results/split" / run_id
    if directory.exists():
        raise FileExistsError("Split run exists; automatic replay is disabled")
    if ApplicationSettings.load(project).ollama_mode != OllamaMode.NATIVE:
        raise ValueError("Split execution requires native mode")
    base_dir = project / "results/submission" / base_run_id
    baseline, records = reload_records(base_dir)
    config_path = artifact_path(project, config_file)
    experiment = load_experiment(config_path)
    if baseline.state != RunState.COMPLETE or experiment != baseline.experiment:
        raise ValueError("Split phase requires the complete unchanged scoped baseline controls")
    if (
        len(experiment.models) != 1
        or experiment.models[0].backend != "ollama"
        or len(experiment.prompts) != 1
        or experiment.prompts[0].skill is not None
        or experiment.source_view != "ordered-rows-scoped-roles-v1"
        or any(record.runtime != ModelRuntime.OLLAMA_NATIVE for record in records)
    ):
        raise ValueError("Split phase requires one native scoped plain-prompt baseline")
    approved = load_manifests(project / "data")
    if len(records) != 10 or {record.input_id for record in records} != set(approved.gold_by_id):
        raise ValueError("Split phase requires exact gold10 membership")
    contract = ExtractionContract.load(
        project / "schemas" / SCHEMA_FILENAME, expected_sha256=approved.gold.schema_sha256
    )
    if baseline.schema_sha256 != contract.identity.sha256:
        raise ValueError("Split parent schema differs from the baseline")
    source_cases = {case.input_id: case for case in approved.corpus.cases}
    instructions = read_checked(
        artifact_path(project, experiment.prompts[0].file), records[0].prompt_sha256
    )
    for record in records:
        if record.prompt_sha256 != records[0].prompt_sha256:
            raise ValueError("Split inputs must share one frozen instruction prefix")
        if record.input_sha256 != source_cases[record.input_id].input_sha256:
            raise ValueError("Split input differs from the approved source")
        read_input(project / "data", source_cases[record.input_id])
    directory.mkdir(parents=True)
    for name in ("cases", "checkpoints", "projections"):
        (directory / name).mkdir()
    shutil.copyfile(project / "schemas" / SCHEMA_FILENAME, directory / SCHEMA_FILENAME)
    shutil.copyfile(config_path, directory / CONFIG_SNAPSHOT)
    projections = {}
    for stage in SplitStage:
        derived = stage_contract(contract, stage)
        relative = f"projections/{stage.value}.schema.json"
        (directory / relative).write_bytes(canonical_bytes(derived.schema_for_provider()))
        projections[stage.value] = {"file": relative, "sha256": derived.identity.sha256}
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    experiment_sha = hashlib.sha256(
        canonical_bytes(
            {
                "policy": POLICY_VERSION,
                "config_sha256": config_sha,
                "projections": projections,
            }
        )
    ).hexdigest()
    header: dict[str, Any] = {
        "version": POLICY_VERSION,
        "run_id": run_id,
        "base_run_id": base_run_id,
        "base_manifest_sha256": hashlib.sha256(
            (base_dir / "manifest.json").read_bytes()
        ).hexdigest(),
        "schema_sha256": contract.identity.sha256,
        "config_sha256": config_sha,
        "experiment_sha256": experiment_sha,
        "experiment": experiment.model_dump(mode="json"),
        "projections": projections,
        "base_instructions": instructions,
        "state": "running",
        "cases": {},
        "checkpoints": {},
        "policy": policy_rules(experiment),
    }
    header_path = directory / "split-run.json"
    write_report(header_path, header)
    started = time.monotonic()
    try:
        with compose_targets(project, experiment.models, RunOptions(run_id=run_id)) as (
            targets,
            setup,
        ):
            prepared = targets[experiment.models[0].id]
            identity = prepared.target.adapter.identity
            previous = baseline.setup[identity.model_id]
            runtime = OllamaRuntime.model_validate_json(json.dumps(previous["runtime"]))
            if identity != runtime.identity(experiment.models[0], native=True):
                raise ValueError("Split installed identity differs from baseline")
            observed = setup[identity.model_id]
            if any(
                observed.get(key) != previous.get(key) for key in ("thinking", "tokenizer_sha256")
            ):
                raise ValueError("Split thinking/tokenizer differs from baseline")
            if observed["loaded"]["context_length"] != previous["loaded"]["context_length"]:
                raise ValueError("Split context differs from baseline")
            header.update(identity=identity.model_dump(mode="json"), setup=setup)
            write_report(header_path, header)

            def checkpoint(stage: SplitStage, progress: InputExecution) -> None:
                input_id = progress.scheduled.job.input_id
                relative = f"checkpoints/{input_id}-{stage.value}.json"
                write_report(
                    directory / relative,
                    {
                        "job": progress.scheduled.job.model_dump(mode="json"),
                        "attempts": [a.model_dump(mode="json") for a in progress.attempts],
                        "admissions": [a.model_dump(mode="json") for a in progress.admissions],
                        "reason": progress.reason,
                    },
                )
                header["checkpoints"].setdefault(input_id, {})[stage.value] = relative
                write_report(header_path, header)

            extractor = SplitExtractor(
                contract,
                prepared.target,
                prepared.admission,
                experiment.execution,
                checkpoint=checkpoint,
            )
            for record in records:
                source = baseline.setup["source_views"][record.input_id]["rendered_text"]
                job = ExtractionJob(
                    run_id=run_id,
                    input_id=record.input_id,
                    input_sha256=record.input_sha256,
                    source_text=source,
                    experiment_sha256=experiment_sha,
                    prompt_id=record.prompt_id,
                    prompt_sha256=record.prompt_sha256,
                    instructions=instructions,
                    sampling=record.sampling,
                )
                result = extractor.extract(job)
                key = item_key(
                    record.input_id, record.model_id, record.prompt_id, record.sampling_id
                )
                relative = f"cases/{record.input_id}.json"
                write_report(
                    directory / relative,
                    {
                        "input_id": record.input_id,
                        "base_record_sha256": baseline.record_sha256[key],
                        "stage_records": {
                            s.value: r.model_dump(mode="json") for s, r in result.records.items()
                        },
                        "extraction": result.extraction,
                        "duration_ms": result.duration_ms,
                    },
                )
                header["cases"][record.input_id] = relative
                write_report(header_path, header)
                if on_case is not None:
                    on_case(record.input_id, result)
        header.update(state="complete", phase_wall_seconds=time.monotonic() - started)
        write_report(header_path, header)
    except BaseException as error:
        header.update(state="interrupted", error_type=type(error).__name__)
        write_report(header_path, header)
        raise
    return directory
