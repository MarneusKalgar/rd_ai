"""Atomic per-attempt/input evidence and uniquely owned run directories."""

import hashlib
import json
import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from extraction_service.application.selection import RunOptions
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.execution.admission import AdmissionEvidence
from extraction_service.execution.results import BatchSummary
from extraction_service.execution.types import InputExecution, ScheduledExtraction
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.records import AttemptResult, RunRecord
from extraction_service.runtime.storage import write_report
from extraction_service.runtime_types import Sha256, StrictModel


class RunState(StrEnum):
    RUNNING = "running"
    COMPLETE = "complete"
    INCOMPLETE = "incomplete"
    INTERRUPTED = "interrupted"


class RunManifest(StrictModel):
    version: Literal["run-manifest-v1"] = "run-manifest-v1"
    run_id: str
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    stage: str
    state: RunState
    experiment: ExperimentConfig
    schema_sha256: Sha256
    jobs: list[dict[str, str]] = Field(min_length=1)
    records: dict[str, str] = Field(default_factory=dict)
    record_sha256: dict[str, Sha256] = Field(default_factory=dict)
    checkpoint_sha256: dict[str, Sha256] = Field(default_factory=dict)
    summary: BatchSummary | None = None
    error: str | None = None
    setup: dict[str, Any] = Field(default_factory=dict)


class Checkpoint(StrictModel):
    input_id: str
    model_id: str
    attempts: list[AttemptResult]
    admissions: list[AdmissionEvidence]
    reason: str | None


def item_key(input_id: str, model_id: str, prompt_id: str, sampling_id: str) -> str:
    identity = json.dumps([input_id, model_id, prompt_id, sampling_id])

    return hashlib.sha256(identity.encode()).hexdigest()


class RunStore:
    def __init__(
        self,
        project_dir: Path,
        scheduled: list[ScheduledExtraction],
        experiment: ExperimentConfig,
        contract: ExtractionContract,
        setup: dict[str, Any],
    ) -> None:
        if not scheduled:
            raise ValueError("Cannot persist an empty schedule")

        first = scheduled[0].job
        RunOptions(run_id=first.run_id)

        if any(item.job.run_id != first.run_id for item in scheduled):
            raise ValueError("Scheduled jobs must belong to one run")

        self.contract = contract
        self.directory = project_dir / "results" / "runs" / first.run_id
        self.directory.parent.mkdir(parents=True, exist_ok=True)
        self.directory.mkdir()
        (self.directory / "records").mkdir()
        (self.directory / "checkpoints").mkdir()
        schema = (project_dir / "schemas" / SCHEMA_FILENAME).read_bytes()
        (self.directory / SCHEMA_FILENAME).write_bytes(schema)
        identities = []
        keys: set[str] = set()

        for scheduled_item in scheduled:
            job = scheduled_item.job
            model_id = scheduled_item.target.adapter.identity.model_id
            key = item_key(job.input_id, model_id, job.prompt_id, job.sampling.id)

            if key in keys:
                raise ValueError("Duplicate scheduled variant")

            keys.add(key)
            identities.append(
                {
                    "key": key,
                    "input_id": job.input_id,
                    "model_id": model_id,
                    "prompt_id": job.prompt_id,
                    "sampling_id": job.sampling.id,
                    "input_sha256": job.input_sha256,
                    "prompt_sha256": job.prompt_sha256,
                    "experiment_sha256": job.experiment_sha256,
                }
            )

        self.manifest = RunManifest(
            run_id=first.run_id,
            stage=first.stage.value,
            state=RunState.RUNNING,
            experiment=experiment,
            schema_sha256=contract.identity.sha256,
            jobs=identities,
            setup=setup,
        )
        self._write_manifest()

    def _write_manifest(self, **updates: Any) -> None:
        self.manifest = RunManifest.model_validate({**self.manifest.model_dump(), **updates})
        write_report(self.directory / "manifest.json", self.manifest.model_dump(mode="json"))

    def checkpoint(self, progress: InputExecution) -> None:
        """Save the latest durable evidence even when this input never returns a record."""

        job = progress.scheduled.job
        model_id = progress.scheduled.target.adapter.identity.model_id
        key = item_key(job.input_id, model_id, job.prompt_id, job.sampling.id)
        write_report(
            self.directory / "checkpoints" / f"{key}.json",
            {
                "input_id": job.input_id,
                "model_id": model_id,
                "attempts": [attempt.model_dump(mode="json") for attempt in progress.attempts],
                "admissions": [
                    evidence.model_dump(mode="json") for evidence in progress.admissions
                ],
                "reason": progress.reason,
            },
        )
        content = (self.directory / "checkpoints" / f"{key}.json").read_bytes()
        hashes = {**self.manifest.checkpoint_sha256, key: hashlib.sha256(content).hexdigest()}
        self._write_manifest(checkpoint_sha256=hashes)

    def save(self, record: RunRecord) -> None:
        key = item_key(record.input_id, record.model_id, record.prompt_id, record.sampling_id)

        if key in self.manifest.records:
            raise FileExistsError("Input result already persisted")

        # Revalidate before serializing rather than trusting a mutated Pydantic instance.
        RunRecord.model_validate_json(record.model_dump_json(), context={"contract": self.contract})
        relative = f"records/{key}.json"
        write_report(self.directory / relative, record.model_dump(mode="json"))
        records = {**self.manifest.records, key: relative}
        digest = hashlib.sha256((self.directory / relative).read_bytes()).hexdigest()
        hashes = {**self.manifest.record_sha256, key: digest}
        self._write_manifest(records=records, record_sha256=hashes)

    def finish(self, summary: BatchSummary) -> None:
        state = RunState.COMPLETE if summary.comparison_complete else RunState.INCOMPLETE
        self._write_manifest(state=state, summary=summary)

    def interrupt(self, error: BaseException) -> None:
        """Retain the original exception; a broken filesystem may prevent finalization."""

        try:
            self._write_manifest(state=RunState.INTERRUPTED, error=type(error).__name__)
        except OSError:
            pass


def reload_records(directory: Path) -> tuple[RunManifest, list[RunRecord]]:
    """Revalidate saved bytes and their declared job/contract identities."""

    if (directory / "manifest.json").is_symlink() or (directory / SCHEMA_FILENAME).is_symlink():
        raise ValueError("Run metadata cannot be symlinked")

    manifest = RunManifest.model_validate_json((directory / "manifest.json").read_bytes())
    contract = ExtractionContract.load(
        directory / SCHEMA_FILENAME, expected_sha256=manifest.schema_sha256
    )
    records = []
    jobs = {job["key"]: job for job in manifest.jobs}

    if manifest.state in (RunState.COMPLETE, RunState.INCOMPLETE) and manifest.summary is None:
        raise ValueError("Finished run requires a summary")

    if len(jobs) != len(manifest.jobs) or set(manifest.records) != set(manifest.record_sha256):
        raise ValueError("Duplicate jobs or incomplete record hashes")

    for key in jobs:
        if re.fullmatch(r"[a-f0-9]{64}", key) is None:
            raise ValueError("Invalid job key")

    for key, digest in manifest.checkpoint_sha256.items():
        if key not in jobs:
            raise ValueError("Checkpoint has no declared job")

        path = directory / "checkpoints" / f"{key}.json"

        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Checkpoint escapes its run directory")

        content = path.read_bytes()

        if hashlib.sha256(content).hexdigest() != digest:
            raise ValueError("Checkpoint hash mismatch")

        checkpoint = Checkpoint.model_validate_json(content)

        if (
            checkpoint.input_id != jobs[key]["input_id"]
            or checkpoint.model_id != jobs[key]["model_id"]
        ):
            raise ValueError("Checkpoint identity differs from its job")

    for key, relative in manifest.records.items():
        if relative != f"records/{key}.json" or key not in jobs:
            raise ValueError("Invalid persisted record path or job identity")

        path = directory / relative

        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Record escapes its run directory")

        content = path.read_bytes()

        if hashlib.sha256(content).hexdigest() != manifest.record_sha256[key]:
            raise ValueError("Saved record hash mismatch")

        record = RunRecord.model_validate_json(content, context={"contract": contract})
        expected = jobs[key]

        actual = {
            "input_id": record.input_id,
            "model_id": record.model_id,
            "prompt_id": record.prompt_id,
            "sampling_id": record.sampling_id,
            "input_sha256": record.input_sha256,
            "prompt_sha256": record.prompt_sha256,
            "experiment_sha256": record.experiment_sha256,
        }

        if (
            any(actual[field] != expected[field] for field in actual)
            or record.run_id != manifest.run_id
            or record.stage.value != manifest.stage
        ):
            raise ValueError("Saved record differs from its declared run job")

        records.append(record)

    if manifest.summary is not None:
        summary = manifest.summary
        actual_counts = [
            sum(record.status.value == status for record in records)
            for status in ("succeeded", "failed", "not_attempted")
        ]

        if (
            len(records) != len(jobs)
            or actual_counts != [summary.succeeded, summary.failed, summary.not_attempted]
            or (manifest.state == RunState.COMPLETE) != summary.comparison_complete
        ):
            raise ValueError("Saved summary differs from persisted records")

    return manifest, records
