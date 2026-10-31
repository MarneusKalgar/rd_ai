"""Saved-baseline correction needs no gold values and verifies policy beyond checksums."""

import hashlib
import json
import shutil
import subprocess
import sys
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, cast

import pytest

from extraction_service.application.composition import PreparedTarget
from extraction_service.application.runner import execute_selected
from extraction_service.application.selection import RunOptions, selected_jobs
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.corrections import application
from extraction_service.corrections.application import run_corrections
from extraction_service.corrections.evaluation import evaluate_corrections
from extraction_service.corrections.storage import export_corrections, verify_corrections
from extraction_service.execution.types import ExecutionTarget
from extraction_service.extraction.validation import JsonObject
from extraction_service.inference.types import GenerationRequest, ModelResponse

from .test_identifier_correction import Adapter, Admission


class BaselineAdapter(Adapter):
    def __init__(self, outputs: list[str]) -> None:
        super().__init__("unused")
        self.outputs = outputs

    def generate(self, request: GenerationRequest) -> ModelResponse:
        self.response = self.outputs.pop(0)
        return super().generate(request)


class FeedbackAdapter(Adapter):
    def generate(self, request: GenerationRequest) -> ModelResponse:
        evidence = json.loads(request.instructions.rsplit("\n", 1)[1])
        candidate = evidence["previous_output"]
        for finding in evidence["identifier_findings"]:
            index = int(finding["path"].split("/")[2])
            candidate["lineItems"][index]["buyerProductIdentifier"] = finding["source_resolution"][
                "value"
            ]
        self.response = json.dumps(candidate)
        return super().generate(request)


type CorrectionFixture = tuple[Path, Path, Path, FeedbackAdapter]


@pytest.fixture
def saved_correction(project_copy: Path, monkeypatch: pytest.MonkeyPatch) -> CorrectionFixture:
    project = project_copy
    corpus = load_corpus(project)
    config = load_experiment(project / "config/gemma-scoped-roles.yaml")
    model = config.models[0].model_copy(update={"model": "test-native"})
    config = config.model_copy(update={"models": [model]})
    config_path = project / "config/unit-correction.json"
    config_path.write_text(config.model_dump_json())
    options = RunOptions(run_id="native-base", input_ids=list(corpus.gold), prompt_ids=["v2"])
    jobs = selected_jobs(
        project, corpus, config, options, hashlib.sha256(config_path.read_bytes()).hexdigest()
    )
    outputs = []
    for job in jobs:
        value = json.loads(json.dumps(corpus.gold[job.input_id]))
        if job.input_id == "B02-S002-PO01":
            value["lineItems"][0]["buyerProductIdentifier"] = "GEN-A"
        outputs.append(json.dumps(value))
    initial = BaselineAdapter(outputs)
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
    initial_target = PreparedTarget(
        target=ExecutionTarget(adapter=initial, endpoint="http://native.test/"),
        admission=Admission(),
    )
    status, store = execute_selected(
        project, corpus, config, jobs, {"local": initial_target}, {"local": setup}
    )
    assert status == 0
    adapter = FeedbackAdapter("unused")
    prepared = PreparedTarget(
        target=ExecutionTarget(adapter=adapter, endpoint="http://native.test/"),
        admission=Admission(),
    )

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
    directory = run_corrections(
        project,
        base_run_id="native-base",
        run_id="identifier-unit",
        config_file="config/unit-correction.json",
        source="runs",
    )
    assert len(adapter.requests) == 1
    return project, directory, store.directory, adapter


def test_no_gold_replay_export_and_real_offline_cli_verify(
    saved_correction: CorrectionFixture,
) -> None:
    project, directory, base, adapter = saved_correction
    header, cases = verify_corrections(directory, base)
    assert len(cases) == 10
    assert sum(case.decision == "guarded_correction_applied" for case in cases) == 1
    assert sum(case.attempt is not None for case in cases) == 1
    exported = project / "results/submission/identifier-unit"
    export_corrections(directory, base, exported)
    _, restored = verify_corrections(exported, base)
    assert cases == restored
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "extraction_service.corrections",
            "--project-dir",
            str(project),
            "verify",
            "identifier-unit",
            "--source",
            "submission",
            "--base-source",
            "runs",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["verified_cases"] == 10
    assert len(adapter.requests) == 1
    with pytest.raises(FileExistsError, match="automatic replay"):
        run_corrections(
            project,
            base_run_id="native-base",
            run_id="identifier-unit",
            config_file="config/unit-correction.json",
            source="runs",
        )


@pytest.mark.parametrize(
    "defect,reason",
    [
        ("retained", "Retained extraction"),
        ("source", "original source differs"),
        ("target", "findings/targets differ"),
        ("schema", "declared policy"),
        ("intent", "request intent differs"),
        ("raw_candidate", "candidate differs"),
    ],
)
def test_artifact_tampering_is_rejected_at_the_policy_boundary(
    saved_correction: CorrectionFixture, defect: str, reason: str
) -> None:
    _, directory, base, _ = saved_correction
    verify_corrections(directory, base)
    path = directory / "cases/B02-S002-PO01.json"
    data = json.loads(path.read_bytes())
    if defect == "retained":
        data["result"]["retained"]["buyerName"] = "Forged"
    elif defect == "source":
        data["original_source"] += "Changed source"
    elif defect == "target":
        data["result"]["targets"][0]["source_resolution"]["value"] = "FORGED"
    elif defect == "schema":
        data["result"]["request"]["output_schema"]["required"] = []
        intent = directory / "requests/B02-S002-PO01.json"
        content = json.loads(intent.read_bytes())
        content["output_schema"]["required"] = []
        intent.write_text(json.dumps(content))
    elif defect == "intent":
        intent = directory / "requests/B02-S002-PO01.json"
        content = json.loads(intent.read_bytes())
        content["source_text"] = "Forged request source"
        intent.write_text(json.dumps(content))
    else:
        data["result"]["candidate"]["buyerName"] = "Forged candidate"
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match=reason):
        verify_corrections(directory, base)


def test_cannot_claim_application_after_a_coherent_off_target_response(
    saved_correction: CorrectionFixture,
) -> None:
    _, directory, base, _ = saved_correction
    verify_corrections(directory, base)
    path = directory / "cases/B02-S002-PO01.json"
    data = json.loads(path.read_bytes())
    candidate = cast(JsonObject, data["result"]["candidate"])
    candidate["buyerName"] = "Off-target change"
    raw = json.dumps(candidate)
    data["result"]["attempt"]["raw_response"] = raw
    data["result"]["attempt"]["response"]["raw_response"] = raw
    data["result"]["attempt"]["response"]["raw_http_body"] = json.dumps({"content": raw})
    data["result"]["retained"] = candidate
    path.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="acceptance guard"):
        verify_corrections(directory, base)


def test_offline_evaluation_distinguishes_reused_and_new_work(
    saved_correction: CorrectionFixture,
) -> None:
    project, directory, base, _ = saved_correction
    original = Path(__file__).resolve().parents[2]
    for name in ("gold", "annotations"):
        shutil.copytree(original / "data" / name, project / "data" / name, dirs_exist_ok=True)
    report = evaluate_corrections(project, directory, base)

    assert report["new_primaries"] == 0
    assert report["new_physical_requests"] == 1 and report["reused_primary_requests"] == 10
    assert report["baseline"]["exact_documents"] == 9
    assert report["retained_pipeline"]["exact_documents"] == 10
    assert (
        report["retained_pipeline"]["overall"]["correct"]
        == report["baseline"]["overall"]["correct"] + 1
    )
    assert report["live_end_to_end_measured"] is False
    assert report["whole_po_certified"] is False


def test_docker_mode_cannot_start_another_correction_invocation(
    saved_correction: CorrectionFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project, _, _, adapter = saved_correction
    monkeypatch.setenv("DI_OLLAMA_MODE", "docker")
    with pytest.raises(ValueError, match="native Ollama mode"):
        run_corrections(
            project,
            base_run_id="native-base",
            run_id="forbidden-mode",
            config_file="config/unit-correction.json",
            source="runs",
        )
    assert len(adapter.requests) == 1
