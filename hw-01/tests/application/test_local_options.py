"""Explicit diagnostic pins and options survive admission, generation and grouping."""

import json

import pytest

from extraction_service.application.admission import request_fingerprint
from extraction_service.application.persistence import reload_records
from extraction_service.configuration.loading import load_experiment
from extraction_service.configuration.models import ModelConfig, OllamaOptions
from extraction_service.runtime.configuration import load_model_pin

from .conftest import ControlledService


def test_local_options_apply_to_render_and_generation_and_split_variants(
    service: ControlledService, gold: dict[str, object]
) -> None:
    service.native = True
    config = load_experiment(service.project / "config/experiments.yaml")
    local = next(model for model in config.models if model.id == "local")
    local = local.model_copy(update={"local_pin_file": "config/diagnostic-pin.json"})
    pin = load_model_pin(service.project, native=True)
    (service.project / "config/diagnostic-pin.json").write_text(pin.model_dump_json())
    service.responses = [json.dumps(gold), json.dumps(gold)]

    for index, penalty in enumerate((0.0, 1.5)):
        options = OllamaOptions(top_k=20, presence_penalty=penalty)
        local = local.model_copy(update={"ollama_options": options})
        config.models[config.models.index(next(m for m in config.models if m.id == "local"))] = (
            local
        )
        path = service.project / "config/options.json"
        path.write_text(config.model_dump_json())
        result = service.invoke(
            "run",
            "--config",
            "config/options.json",
            "--run-id",
            f"options-{index}",
            "--input",
            "B02-S003-PO01",
        )
        assert result.returncode == 0, result.stdout + result.stderr
        manifest, records = reload_records(service.project / f"results/runs/options-{index}")
        assert manifest.setup["local"]["ollama_options"] == options.model_dump()
        assert records[0].dependency is not None
        assert records[0].dependency.model_digest == pin.digest

    chats = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(chats) == 4
    assert all(payload is not None and payload["options"]["top_k"] == 20 for payload in chats)
    assert [payload["options"]["presence_penalty"] for payload in chats if payload] == [
        0.0,
        0.0,
        1.5,
        1.5,
    ]
    evaluated = service.invoke("evaluate", "options-0", "options-1")
    assert evaluated.returncode == 0, evaluated.stdout + evaluated.stderr
    assert len(json.loads(evaluated.stdout)["variants"]) == 2


def test_local_option_fingerprint_changes_with_controls(service: ControlledService) -> None:
    from extraction_service.corpus.loading import load_corpus
    from extraction_service.inference.types import GenerationRequest

    corpus = load_corpus(service.project)
    config = load_experiment(service.project / "config/experiments.yaml")
    request = GenerationRequest.from_contract(
        instructions="Extract",
        source_text="Source",
        contract=corpus.contract,
        sampling=config.sampling[0],
        timeout_seconds=10.0,
    )
    original = request_fingerprint(request)
    first = request_fingerprint(request, ollama_options=OllamaOptions())
    second = request_fingerprint(request, ollama_options=OllamaOptions(top_k=20))

    assert len({original, first, second}) == 3


def test_custom_pin_still_checks_selected_identity(service: ControlledService) -> None:
    service.native = True
    config = load_experiment(service.project / "config/experiments.yaml")
    local = next(model for model in config.models if model.id == "local")
    local = local.model_copy(update={"local_pin_file": "config/diagnostic-pin.json"})
    config.models[config.models.index(next(m for m in config.models if m.id == "local"))] = local
    pin = load_model_pin(service.project, native=True).model_copy(update={"model": "other"})
    (service.project / "config/diagnostic-pin.json").write_text(pin.model_dump_json())
    (service.project / "config/options.json").write_text(config.model_dump_json())

    result = service.invoke("run", "--config", "config/options.json", "--run-id", "bad-pin")

    assert result.returncode == 2
    assert service.requests == []


@pytest.mark.parametrize(
    "field,value", [("local_pin_file", "config/pin.json"), ("ollama_options", {})]
)
def test_provider_rejects_local_only_controls(field: str, value: object) -> None:
    with pytest.raises(ValueError, match="only for Ollama"):
        ModelConfig.model_validate(
            {"id": "provider", "backend": "openrouter", "model": "provider/model", field: value}
        )
