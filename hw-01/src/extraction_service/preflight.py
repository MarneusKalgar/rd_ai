"""Offline setup verification; this module never invokes a model runtime."""

import hashlib
from pathlib import Path
from typing import Final, Literal

from extraction_service.artifacts import artifact_path, read_text
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.corpus.loading import load_corpus
from extraction_service.extraction.validation import SchemaIdentity
from extraction_service.runtime_types import StrictModel

DEFAULT_EXPERIMENT_FILE: Final[str] = "config/experiments.yaml"


class PromptIdentity(StrictModel):
    """Checked prompt identity for the setup report, without its content."""

    id: str
    file: str
    sha256: str


class PreflightReport(StrictModel):
    """Offline evidence; success does not claim model capability or readiness."""

    mode: Literal["offline"] = "offline"
    corpus_version: str
    input_count: int
    gold_count: int
    annotation_count: int
    source_group_count: int
    layout_group_count: int
    schema_identity: SchemaIdentity
    experiment: ExperimentConfig
    prompts: list[PromptIdentity]
    model_capabilities_verified: Literal[False] = False


def preflight(project_dir: Path, config_file: str = DEFAULT_EXPERIMENT_FILE) -> PreflightReport:
    """Verify configuration, prompt references and the full approved corpus offline.

    Args:
        project_dir: HW-01 root containing config, prompts, schemas and data.
        config_file: Project-relative experiment YAML file.

    Returns:
        Setup evidence without source text, gold answers or credentials.

    Raises:
        ValueError: A configuration, setting, reference or approved artifact fails.
    """

    config_path = artifact_path(project_dir, config_file)
    experiment = load_experiment(config_path)
    ApplicationSettings.load(project_dir)
    prompts: list[PromptIdentity] = []

    for prompt in experiment.prompts:
        path = artifact_path(project_dir, prompt.file)

        if not path.is_relative_to((project_dir / "prompts").resolve()):
            raise ValueError("Referenced prompt must belong to the project's prompts directory")

        text = read_text(path)

        if not text.strip():
            raise ValueError("Referenced prompt cannot be empty")

        prompts.append(
            PromptIdentity(
                id=prompt.id,
                file=prompt.file,
                sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )

    corpus = load_corpus(project_dir)
    source_groups = {item.source_group for item in corpus.inputs}
    layout_groups = {item.layout_group for item in corpus.inputs}

    return PreflightReport(
        corpus_version=corpus.version,
        input_count=len(corpus.inputs),
        gold_count=len(corpus.gold),
        annotation_count=corpus.annotation_count,
        source_group_count=len(source_groups),
        layout_group_count=len(layout_groups),
        schema_identity=corpus.contract.identity,
        experiment=experiment,
        prompts=prompts,
    )
