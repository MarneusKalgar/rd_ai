"""Saved stage evidence, gold-independent execution, assembly tampering and offline CLI."""

import hashlib
import json
import shutil
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from extraction_service.application.composition import PreparedTarget
from extraction_service.application.exporting import export_run
from extraction_service.application.runner import execute_selected
from extraction_service.application.selection import RunOptions, selected_jobs
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.types import ExecutionTarget
from extraction_service.staged import application
from extraction_service.staged.application import run_split
from extraction_service.staged.contracts import SplitStage
from extraction_service.staged.evaluation import evaluate_split
from extraction_service.staged.storage import export_split, verify_split

from .test_identifier_correction import Admission
from .test_split_extraction import QueueAdapter, parts

type SplitFixture = tuple[Path, Path, Path, QueueAdapter]


@pytest.fixture
def saved_split(project_copy: Path, monkeypatch: pytest.MonkeyPatch) -> SplitFixture:
    project = project_copy
    corpus = load_corpus(project)
    config = load_experiment(project / "config/gemma-scoped-roles.yaml")
    config = config.model_copy(
        update={"models": [config.models[0].model_copy(update={"model": "test-native"})]}
    )
    config_path = project / "config/unit-split.json"
    config_path.write_text(config.model_dump_json())
    jobs = selected_jobs(
        project,
        corpus,
        config,
        RunOptions(run_id="split-base", input_ids=list(corpus.gold)),
        hashlib.sha256(config_path.read_bytes()).hexdigest(),
    )
    baseline_outputs = []
    split_outputs = []
    for job in jobs:
        value = json.loads(json.dumps(corpus.gold[job.input_id]))
        headers, lines = parts(value)
        split_outputs.extend([json.dumps(headers), json.dumps(lines)])
        value["buyerName"] = "BASELINE-PREDICTION-MUST-NOT-ENTER-REQUEST"
        baseline_outputs.append(json.dumps(value))
    initial = QueueAdapter(baseline_outputs)
    setup: dict[str, Any] = {
        "runtime": {
            "version": "test",
            "model_name": "test-native",
            "model_digest": "a" * 64,
            "capabilities": ["completion"],
        },
        "thinking": False,
        "tokenizer_sha256": "b" * 64,
        "loaded": {"context_length": 49152},
    }
    target = PreparedTarget(ExecutionTarget(initial, "http://native.test/"), Admission())
    status, store = execute_selected(
        project, corpus, config, jobs, {"local": target}, {"local": setup}
    )
    assert status == 0
    base = project / "results/submission/split-base"
    export_run(store.directory, base)
    adapter = QueueAdapter(split_outputs)
    prepared = PreparedTarget(ExecutionTarget(adapter, "http://native.test/"), Admission())

    @contextmanager
    def composed(
        *args: object, **kwargs: object
    ) -> Generator[tuple[dict[str, PreparedTarget], dict[str, Any]]]:
        yield {"local": prepared}, {"local": setup}

    monkeypatch.setattr(application, "compose_targets", composed)
    monkeypatch.setenv("DI_OLLAMA_MODE", "native")
    for folder in ("gold", "annotations"):
        for path in (project / "data" / folder).glob("*.json"):
            path.unlink()
    directory = run_split(
        project,
        base_run_id="split-base",
        run_id="split-result",
        config_file="config/unit-split.json",
    )
    return project, directory, base, adapter


def test_gold_independent_execution_export_and_cli(saved_split: SplitFixture) -> None:
    project, directory, base, adapter = saved_split
    header, cases, records = verify_split(directory, base)
    assert len(cases) == 10
    assert len(adapter.requests) == 20
    assert all(case.extraction is not None for case in cases)
    assert all(len(records[stage]) == 10 for stage in SplitStage)
    assert all(
        "BASELINE-PREDICTION-MUST-NOT-ENTER-REQUEST" not in request.instructions
        for request in adapter.requests
    )
    for headers, lines in zip(adapter.requests[::2], adapter.requests[1::2], strict=True):
        assert headers.source_text == lines.source_text
    exported = project / "results/submission/split-result"
    export_split(directory, base, exported)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "extraction_service.staged",
            "--project-dir",
            str(project),
            "verify",
            "split-result",
            "--source",
            "submission",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout) == {"verified_cases": 10}
    with pytest.raises(FileExistsError, match="automatic replay"):
        run_split(
            project,
            base_run_id="split-base",
            run_id=header["run_id"],
            config_file="config/unit-split.json",
        )
    assert len(adapter.requests) == 20


@pytest.mark.parametrize(
    "defect", ["assembly", "projection", "source", "admission", "missing-stage", "policy", "prefix"]
)
def test_split_artifact_tampering_rejected(saved_split: SplitFixture, defect: str) -> None:
    _, directory, base, _ = saved_split
    metadata = json.loads((directory / "split-run.json").read_bytes())
    input_id = next(iter(metadata["cases"]))
    case_path = directory / metadata["cases"][input_id]
    case = json.loads(case_path.read_bytes())
    checkpoint_path = directory / metadata["checkpoints"][input_id]["headers"]
    checkpoint = json.loads(checkpoint_path.read_bytes())
    if defect == "assembly":
        case["extraction"]["buyerName"] = "tamper"
        case_path.write_text(json.dumps(case))
        expected = "disjoint assembly"
    elif defect == "projection":
        path = directory / metadata["projections"]["headers"]["file"]
        schema = json.loads(path.read_bytes())
        schema["properties"]["buyerName"] = {"type": "string"}
        path.write_text(json.dumps(schema))
        expected = "stage projection"
    elif defect in ("source", "admission"):
        if defect == "source":
            checkpoint["job"]["source_text"] += "extra source"
            expected = "checkpoint differs"
        else:
            checkpoint["admissions"][0]["request_sha256"] = "f" * 64
            expected = "admission does not bind"
        checkpoint_path.write_text(json.dumps(checkpoint))
    elif defect == "missing-stage":
        del case["stage_records"]["lines"]
        case_path.write_text(json.dumps(case))
        expected = "both stage records"
    else:
        if defect == "policy":
            metadata["policy"]["stage_feedback"] = True
            expected = "declared policy"
        else:
            metadata["base_instructions"] += "new rule"
            expected = "instruction prefix"
        (directory / "split-run.json").write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match=expected):
        verify_split(directory, base)


def test_split_evaluator_scores_assembled_population_and_counts_both_stages(
    saved_split: SplitFixture,
) -> None:
    project, directory, base, _ = saved_split
    original_project = Path(__file__).resolve().parents[2]
    for folder in ("gold", "annotations"):
        shutil.copytree(
            original_project / "data" / folder, project / "data" / folder, dirs_exist_ok=True
        )
    report = evaluate_split(project, directory, base)

    assert report["quality"]["exact_documents"] == 10
    assert report["quality"]["overall"]["correct"] == 342
    assert report["quality"]["overall"]["total"] == 342
    assert report["physical_requests"] == report["new_primary_stage_jobs"] == 20
    assert report["assembled_documents"] == 10
    assert report["quality"]["headers"]["total"] == 70
    assert report["quality"]["lines"]["total"] == 272
    assert report["stage_operations"]["headers"]["selected_inputs"] == 10
    assert report["stage_operations"]["lines"]["selected_inputs"] == 10
    assert report["api_cost_usd"] == "0"
