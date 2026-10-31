"""Explicit local thinking controls stay aligned across admission and generation."""

import json
from typing import Any

import pytest
from pydantic import ValidationError

from extraction_service.application.admission import request_fingerprint
from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.models import ModelConfig, SamplingConfig
from extraction_service.extraction import ExtractionContract
from extraction_service.inference.types import GenerationRequest

from .conftest import ControlledService

INPUT = "B02-S003-PO01"


def set_thinking(service: ControlledService, thinking: bool | None) -> None:
    path = service.project / "config/experiments.yaml"
    config = load_experiment(path)
    models = [
        model.model_copy(update={"thinking": thinking}) if model.id == "local" else model
        for model in config.models
    ]
    path.write_text(config.model_copy(update={"models": models}).model_dump_json())


@pytest.mark.parametrize("thinking", [False, True, None])
def test_thinking_matches_render_generation_correction_and_saved_evidence(
    service: ControlledService, gold: dict[str, Any], thinking: bool | None
) -> None:
    service.native = True
    set_thinking(service, thinking)
    service.responses = ["{}", json.dumps(gold)]

    result = service.invoke("run", "--run-id", "thinking", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/thinking")
    assert [attempt.outcome.value for attempt in records[0].attempts] == ["invalid", "valid"]
    chats = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(chats) == 4

    for payload in chats:
        assert payload is not None

        if thinking is None:
            assert "think" not in payload
        else:
            assert payload["think"] is thinking

    control = manifest.setup["local"]["thinking"]
    assert control["requested"] is thinking
    assert control["effective"] is (True if thinking is None else thinking)
    checkpoint = next((service.project / "results/runs/thinking/checkpoints").glob("*.json"))
    admissions = json.loads(checkpoint.read_bytes())["admissions"]
    assert len(admissions) == 2
    assert all(admission["thinking"] is thinking for admission in admissions)
    assert admissions[0]["request_sha256"] != admissions[1]["request_sha256"]


@pytest.mark.parametrize("metadata", [None, {"values": [True]}, {"values": [0, 1]}])
def test_unadvertised_thinking_control_stops_before_loading_or_generation(
    service: ControlledService, metadata: dict[str, Any] | None
) -> None:
    _, details = service.reply("/api/show", {})
    details["thinking"] = metadata
    service.replacements["/api/show"] = details

    result = service.invoke("run", "--run-id", "unsupported-thinking", "--input", INPUT)

    assert result.returncode == 2, result.stdout + result.stderr
    assert not service.generation_started.is_set()
    assert not any(path in ("/api/chat", "/api/generate") for path, _, _ in service.requests)


def test_thinking_profiles_do_not_pool_overlapping_observations(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    service.native = True
    service.responses = [json.dumps(gold)] * 2
    set_thinking(service, False)
    first = service.invoke("run", "--run-id", "off", "--input", INPUT)
    set_thinking(service, True)
    second = service.invoke("run", "--run-id", "on", "--input", INPUT)

    evaluated = service.invoke("evaluate", "off", "on")

    assert first.returncode == second.returncode == evaluated.returncode == 0, (
        first.stdout + second.stdout + evaluated.stdout + evaluated.stderr
    )
    variants = json.loads(evaluated.stdout)["variants"]
    assert len(variants) == 2
    assert {variant["identity"]["context"]["thinking"]["effective"] for variant in variants} == {
        False,
        True,
    }
    assert all(variant["quality"]["exact_documents"] == 1 for variant in variants)
    assert all(variant["operational"]["physical_requests"] == 1 for variant in variants)


def test_fingerprint_binds_explicit_thinking_without_changing_legacy_provider_hash(
    contract: ExtractionContract,
) -> None:
    generation = GenerationRequest.from_contract(
        instructions="Extract the order.",
        source_text="Order PO-1",
        contract=contract,
        sampling=SamplingConfig(id="test", temperature=0.0, top_p=1.0, max_output_tokens=512),
        timeout_seconds=1.0,
    )
    legacy = request_fingerprint(generation)

    assert request_fingerprint(generation, thinking=None) == legacy
    fingerprints = {
        legacy,
        request_fingerprint(generation, thinking=False),
        request_fingerprint(generation, thinking=True),
    }
    assert len(fingerprints) == 3


@pytest.mark.parametrize("value", ["false", 0, 1])
def test_thinking_requires_a_strict_boolean(value: Any) -> None:
    with pytest.raises(ValidationError):
        ModelConfig(id="local", backend="ollama", model="test", thinking=value)


def test_ollama_thinking_is_not_a_provider_reasoning_setting() -> None:
    with pytest.raises(ValidationError, match="only for Ollama"):
        ModelConfig(id="provider", backend="openrouter", model="test", thinking=False)
