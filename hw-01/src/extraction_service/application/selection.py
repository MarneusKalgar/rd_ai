"""Validate explicit selections before constructing any clients or run directories."""

import hashlib
from pathlib import Path
from typing import Annotated
from uuid import uuid4

from pydantic import Field, StringConstraints

from extraction_service.artifacts import artifact_path, read_text
from extraction_service.configuration.models import ExperimentConfig, ModelConfig
from extraction_service.corpus.loading import CorpusInput, LoadedCorpus
from extraction_service.execution.types import ExtractionJob
from extraction_service.record_types import ExecutionStage
from extraction_service.runtime_types import StrictModel


class RunOptions(StrictModel):
    run_id: Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")] = Field(
        default_factory=lambda: uuid4().hex
    )
    model_ids: list[str] = Field(default_factory=list)
    prompt_ids: list[str] = Field(default_factory=list)
    sampling_ids: list[str] = Field(default_factory=list)
    input_ids: list[str] = Field(default_factory=list)
    stage: ExecutionStage = ExecutionStage.MATRIX
    allow_provider: bool = False
    coverage_file: str | None = None


def select_ids(requested: list[str], available: list[str], defaults: list[str]) -> list[str]:
    selected = requested or defaults

    if len(selected) != len(set(selected)) or any(item not in available for item in selected):
        raise ValueError("Selection contains duplicate or unknown IDs")

    return selected


def select_models(experiment: ExperimentConfig, options: RunOptions) -> list[ModelConfig]:
    identifiers = select_ids(
        options.model_ids,
        [model.id for model in experiment.models],
        [experiment.selection.model_id],
    )

    by_id = {model.id: model for model in experiment.models}

    return [by_id[identifier] for identifier in identifiers]


def select_inputs(corpus: LoadedCorpus, options: RunOptions) -> list[CorpusInput]:
    available = [source.input_id for source in corpus.inputs]
    identifiers = select_ids(options.input_ids, available, available)

    by_id = {source.input_id: source for source in corpus.inputs}

    return [by_id[identifier] for identifier in identifiers]


def selected_jobs(
    project_dir: Path,
    corpus: LoadedCorpus,
    experiment: ExperimentConfig,
    options: RunOptions,
    experiment_sha256: str,
) -> list[ExtractionJob]:
    """Construct a source-only schedule; gold labels never enter generation jobs."""

    prompts = select_ids(
        options.prompt_ids,
        [prompt.id for prompt in experiment.prompts],
        [experiment.selection.prompt_id],
    )
    sampling_ids = select_ids(
        options.sampling_ids,
        [sampling.id for sampling in experiment.sampling],
        [experiment.selection.sampling_id],
    )
    sources = select_inputs(corpus, options)
    jobs = []

    for prompt in experiment.prompts:
        if prompt.id not in prompts:
            continue

        instructions = read_text(artifact_path(project_dir, prompt.file))

        for sampling in experiment.sampling:
            if sampling.id not in sampling_ids:
                continue

            for source in sources:
                jobs.append(
                    ExtractionJob(
                        run_id=options.run_id,
                        input_id=source.input_id,
                        input_sha256=source.input_sha256,
                        source_text=source.text,
                        experiment_sha256=experiment_sha256,
                        prompt_id=prompt.id,
                        prompt_sha256=hashlib.sha256(instructions.encode()).hexdigest(),
                        instructions=instructions,
                        sampling=sampling,
                        stage=options.stage,
                    )
                )

    return jobs
