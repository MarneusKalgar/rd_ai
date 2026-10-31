"""Skill loading changes actual requests and retains independently checkable evidence."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from extraction_service.application.exporting import export_run, verify_export
from extraction_service.application.persistence import reload_records
from extraction_service.application.selection import RunOptions, selected_jobs
from extraction_service.artifacts import ArtifactError
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.models import PromptConfig
from extraction_service.corpus.loading import load_corpus
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.messages import request_messages
from extraction_service.inference.types import GenerationRequest
from extraction_service.preflight import preflight
from extraction_service.prompting.resources import load_prompt, validate_prompt_evidence

from .conftest import ControlledService


def config(project: Path) -> PromptConfig:
    return load_experiment(project / "config/gemma-examples.yaml").prompts[0]


def test_plain_prompt_serialization_and_instruction_bytes_are_unchanged(project_copy: Path) -> None:
    prompt = PromptConfig(id="v2", file="prompts/v2.txt")
    loaded = load_prompt(project_copy, prompt)

    assert prompt.model_dump() == {"id": "v2", "file": "prompts/v2.txt"}
    assert loaded.evidence is None
    assert loaded.instructions.encode() == (project_copy / "prompts/v2.txt").read_bytes()


def test_loaded_bytes_order_and_archive_reconstruction(project_copy: Path) -> None:
    prompt = config(project_copy)
    loaded = load_prompt(project_copy, prompt)
    base = (project_copy / "prompts/v2.txt").read_text()
    package = project_copy / "prompts/skills/extraction-examples"
    expected = (
        base
        + "\n\nAPPLICATION-LOADED PROMPT RESOURCES\n"
        + (package / "SKILL.md").read_text()
        + "\n\n"
        + (package / "examples.json").read_text()
    )

    assert loaded.instructions == expected
    assert loaded.evidence is not None
    evidence = loaded.evidence.model_dump(mode="json")
    # Restoration must not read whichever resource bytes happen to be installed now.
    (package / "examples.json").unlink()
    reconstructed = validate_prompt_evidence(evidence, prompt)

    assert reconstructed == expected
    assert loaded.evidence.rendered_sha256 == hashlib.sha256(expected.encode()).hexdigest()
    assert "README.md" not in [r.file for r in loaded.evidence.loaded]


@pytest.mark.parametrize(
    "defect", ["missing", "changed", "empty", "escape", "absolute", "alias", "symlink"]
)
def test_bad_resource_fails_at_loading(project_copy: Path, defect: str) -> None:
    raw = config(project_copy).model_dump()
    path = project_copy / raw["skill"]["resources"][0]["file"]
    if defect == "missing":
        path.unlink()
    elif defect == "changed":
        path.write_text("altered content")
    elif defect == "empty":
        path.write_text(" ")
        raw["skill"]["resources"][0]["sha256"] = hashlib.sha256(b" ").hexdigest()
    elif defect in ("escape", "absolute"):
        raw["skill"]["resources"][0]["file"] = "prompts/v2.txt" if defect == "escape" else str(path)
    elif defect == "alias":
        raw["skill"]["resources"][0]["file"] = "prompts/skills/extraction-examples/./SKILL.md"
    else:
        path.unlink()
        path.symlink_to(project_copy / "prompts/v2.txt")
    prompt = PromptConfig.model_validate(raw)

    with pytest.raises(ArtifactError):
        load_prompt(project_copy, prompt)


@pytest.mark.parametrize(
    "defect", ["content", "order", "rendered", "selection", "base", "coherent-resource"]
)
def test_saved_resource_tampering_is_rejected(project_copy: Path, defect: str) -> None:
    prompt = config(project_copy)
    loaded = load_prompt(project_copy, prompt)
    assert loaded.evidence is not None
    evidence = loaded.evidence.model_dump(mode="json")
    if defect == "content":
        evidence["loaded"][1]["content"] += "altered"
    elif defect == "order":
        evidence["loaded"].reverse()
    elif defect == "rendered":
        evidence["rendered_text"] += "altered"
    elif defect == "selection":
        evidence["loaded"][1]["file"] = "prompts/skills/extraction-examples/not-loaded.json"
    elif defect == "base":
        evidence["base"]["content"] += "altered"
    else:
        evidence["loaded"][1]["content"] += "altered"
        evidence["loaded"][1]["sha256"] = hashlib.sha256(
            evidence["loaded"][1]["content"].encode()
        ).hexdigest()

    with pytest.raises(ValueError):
        validate_prompt_evidence(evidence, prompt)


def test_preflight_jobs_and_shared_messages_use_complete_rendering(project_copy: Path) -> None:
    report = preflight(project_copy, "config/gemma-examples.yaml")
    corpus = load_corpus(project_copy)
    jobs = selected_jobs(
        project_copy,
        corpus,
        report.experiment,
        RunOptions(input_ids=["B02-S003-PO01"]),
        "a" * 64,
    )
    job = jobs[0]
    request = GenerationRequest.from_contract(
        instructions=job.instructions,
        source_text=job.source_text,
        contract=corpus.contract,
        sampling=job.sampling,
        timeout_seconds=1.0,
    )
    messages = request_messages(request)

    assert report.prompts[0].sha256 == job.prompt_sha256
    assert job.prompt_sha256 == hashlib.sha256(job.instructions.encode()).hexdigest()
    assert "FIC-9301" in messages[0]["content"]
    assert "APPLICATION-LOADED PROMPT RESOURCES" in messages[0]["content"]
    assert "FIC-9301" not in messages[1]["content"]
    assert messages[1]["content"] == job.source_text
    assert request.output_schema == corpus.contract.schema_for_provider()


def test_fictional_example_outputs_use_the_authoritative_contract(
    project_copy: Path, contract: ExtractionContract
) -> None:
    examples = json.loads(
        (project_copy / "prompts/skills/extraction-examples/examples.json").read_bytes()
    )
    for example in examples:
        result = contract.validate_json(json.dumps(example["expected"]))
        assert result.is_valid, result.issues
        assert "B02-" not in example["source"]
    assert examples[0]["expected"]["lineItems"][0]["buyerProductQuantity"] == "2"
    assert examples[1]["expected"]["lineItems"][0]["buyerProductIdentifier"] == "00073-Z"
    assert len(examples[1]["expected"]["lineItems"]) == 2
    assert examples[2]["expected"]["lineItems"][0]["buyerProductQuantity"] is None


def test_actual_cli_admission_generation_export_and_reload_preserve_resources(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    service.native = True
    experiment = load_experiment(service.project / "config/gemma-examples.yaml")
    sampling = experiment.sampling[0].model_copy(update={"max_output_tokens": 4096})
    experiment = experiment.model_copy(update={"sampling": [sampling]})
    (service.project / "config/unit-examples.json").write_text(experiment.model_dump_json())
    service.responses = [json.dumps(gold)]

    result = service.invoke(
        "run",
        "--config",
        "config/unit-examples.json",
        "--run-id",
        "examples-cli",
        "--input",
        "B02-S003-PO01",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    directory = service.project / "results/runs/examples-cli"
    manifest, records = reload_records(directory)
    evidence = manifest.setup["prompt_resources"]["v2-examples"]
    assert evidence["rendered_sha256"] == records[0].prompt_sha256
    chats = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(chats) == 2
    assert chats[0] is not None and chats[1] is not None
    assert chats[0]["_debug_render_only"] is True
    assert chats[0]["messages"] == chats[1]["messages"]
    assert evidence["rendered_text"] in chats[1]["messages"][0]["content"]
    assert records[0].extraction == gold
    assert not (service.project / "results/budget-ledger.json").exists()
    destination = service.project / "results/submission/examples-cli"
    export_run(directory, destination)
    verify_export(destination)
    metadata = json.loads((destination / "manifest.json").read_bytes())
    metadata["setup"]["prompt_resources"]["v2-examples"]["loaded"][1]["content"] += "tamper"
    (destination / "manifest.json").write_text(json.dumps(metadata))

    with pytest.raises(ValueError, match="content hash"):
        reload_records(destination)


def test_changed_resource_stops_cli_before_any_http(service: ControlledService) -> None:
    (service.project / "prompts/skills/extraction-examples/examples.json").write_text("[]")

    result = service.invoke(
        "run",
        "--config",
        "config/gemma-examples.yaml",
        "--run-id",
        "bad-resources",
        "--input",
        "B02-S003-PO01",
    )

    assert result.returncode == 2
    assert json.loads(result.stdout) == {"setup_error": "ArtifactError"}
    assert service.requests == []
    assert not (service.project / "results/runs/bad-resources").exists()
