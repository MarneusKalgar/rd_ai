"""Incremental selected execution through the existing shared coordinator."""

import hashlib
from collections.abc import Callable
from pathlib import Path

from extraction_service.application.composition import (
    PreparedTarget,
    SelectedAdmission,
    compose_targets,
)
from extraction_service.application.persistence import RunStore
from extraction_service.application.selection import RunOptions, select_models, selected_jobs
from extraction_service.artifacts import artifact_path
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.corpus.loading import LoadedCorpus, load_corpus
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.execution.coordinator import ExtractionCoordinator
from extraction_service.execution.types import ExtractionJob, ScheduledExtraction
from extraction_service.exit_status import ExitStatus
from extraction_service.preflight import DEFAULT_EXPERIMENT_FILE, preflight
from extraction_service.records import RunRecord


def execute_selected(
    project_dir: Path,
    corpus: LoadedCorpus,
    experiment: ExperimentConfig,
    jobs: list[ExtractionJob],
    targets: dict[str, PreparedTarget],
    setup: dict[str, object],
    on_record: Callable[[RunRecord], None] | None = None,
) -> tuple[int, RunStore]:
    """Borrow composed dependencies; persist work before proceeding to the next input."""

    scheduled = []

    for prepared in targets.values():
        for job in jobs:
            scheduled.append(
                ScheduledExtraction(
                    job=job,
                    target=prepared.target,
                    pricing=prepared.pricing,
                )
            )

    store = RunStore(project_dir, scheduled, experiment, corpus.contract, setup)
    ledger = BudgetLedger(project_dir, experiment.execution)
    coordinator = ExtractionCoordinator(
        corpus.contract,
        experiment.execution,
        ledger=ledger,
        admission=SelectedAdmission(targets),
        checkpoint=store.checkpoint,
    )
    records: list[RunRecord] = []

    try:
        for item in scheduled:
            record = coordinator.execute(item)
            store.save(record)
            records.append(record)

            if on_record is not None:
                on_record(record)

        batch = coordinator.summarize(records)
        store.finish(batch.summary)
    except BaseException as error:
        store.interrupt(error)
        raise

    if not batch.summary.comparison_complete:
        return ExitStatus.INCOMPLETE, store

    status = ExitStatus.EXTRACTION_FAILURE if batch.summary.failed else ExitStatus.SUCCESS

    return status, store


def run(
    project_dir: Path,
    options: RunOptions,
    config_file: str = DEFAULT_EXPERIMENT_FILE,
    *,
    on_record: Callable[[RunRecord], None] | None = None,
) -> tuple[int, Path]:
    if (project_dir / "results/runs" / options.run_id).exists():
        raise FileExistsError("Run directory already exists; automatic replay is disabled")

    corpus = load_corpus(project_dir)
    report = preflight(project_dir, config_file, corpus=corpus)
    experiment = report.experiment
    models = select_models(experiment, options)
    digest = hashlib.sha256(artifact_path(project_dir, config_file).read_bytes()).hexdigest()
    jobs = selected_jobs(project_dir, corpus, experiment, options, digest)

    with compose_targets(project_dir, models, options) as (targets, evidence):
        status, store = execute_selected(
            project_dir,
            corpus,
            experiment,
            jobs,
            targets,
            evidence,
            on_record,
        )

    return status, store.directory
