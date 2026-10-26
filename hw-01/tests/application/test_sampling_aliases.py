"""Offline aliases preserve controls, immutable sources and duplicate rejection."""

import hashlib
import json
from typing import Any

import pytest

from extraction_service.configuration.loading import load_experiment
from extraction_service.evaluation.sampling_aliases import SamplingAliases
from extraction_service.extraction.validation import JsonObject

from .conftest import ControlledService


def alias_document(source: dict[str, Any], target_id: str) -> dict[str, Any]:
    return {
        "version": "sampling-aliases-v1",
        "aliases": [{"source": source, "target": {**source, "id": target_id}}],
    }


@pytest.mark.parametrize(
    "name,value", [("temperature", 0.5), ("top_p", 0.5), ("max_output_tokens", 8192)]
)
def test_alias_rejects_changed_controls(name: str, value: float) -> None:
    document = alias_document(
        {"id": "diagnostic", "temperature": 0.2, "top_p": 0.9, "max_output_tokens": 16384},
        "exploratory",
    )
    document["aliases"][0]["target"][name] = value

    with pytest.raises(ValueError, match="cannot change generation controls"):
        SamplingAliases.model_validate(document)


def test_alias_rejects_wrong_saved_source_and_chains() -> None:
    from extraction_service.configuration.models import SamplingConfig

    source = {"id": "diagnostic", "temperature": 0.2, "top_p": 0.9, "max_output_tokens": 16384}
    document = alias_document(source, "exploratory")
    aliases = SamplingAliases.model_validate(document)

    with pytest.raises(ValueError, match="Saved sampling differs"):
        aliases.canonical(SamplingConfig.model_validate({**source, "top_p": 1.0}))

    with pytest.raises(ValueError, match="declared alias target"):
        aliases.canonical(
            SamplingConfig.model_validate({**source, "id": "exploratory", "top_p": 1.0})
        )

    document["aliases"].append(
        {"source": {**source, "id": "exploratory"}, "target": {**source, "id": "other"}}
    )
    with pytest.raises(ValueError, match="no chains"):
        SamplingAliases.model_validate(document)


@pytest.mark.parametrize("defect", ["duplicate-source", "conflicting-target", "same-id"])
def test_alias_rejects_ambiguous_definitions(defect: str) -> None:
    source = {"id": "diagnostic", "temperature": 0.2, "top_p": 0.9, "max_output_tokens": 16384}
    document = alias_document(source, "exploratory")
    if defect == "duplicate-source":
        document["aliases"].append(document["aliases"][0])
        expected = "unique sources"
    elif defect == "same-id":
        document["aliases"][0]["target"]["id"] = source["id"]
        expected = "different IDs"
    else:
        other = {**source, "id": "other", "temperature": 0.5}
        document["aliases"].append({"source": other, "target": {**other, "id": "exploratory"}})
        expected = "conflicting controls"

    with pytest.raises(ValueError, match=expected):
        SamplingAliases.model_validate(document)


@pytest.mark.parametrize("overlap", [False, True])
def test_real_cli_alias_grouping_preserves_sources_and_rejects_overlap(
    service: ControlledService, gold: JsonObject, overlap: bool
) -> None:
    config = load_experiment(service.project / "config/experiments.yaml")
    source = config.sampling[0].model_dump()
    document = alias_document(source, "canonical")
    (service.project / "config/sampling-aliases.json").write_text(json.dumps(document))
    config.sampling.append(config.sampling[0].model_copy(update={"id": "canonical"}))
    (service.project / "config/alias-experiment.json").write_text(config.model_dump_json())
    service.responses = [json.dumps(gold), json.dumps(gold)]
    first_id = "B02-S003-PO01"
    second_id = first_id if overlap else "B02-S002-PO01"
    first = service.invoke(
        "run", "--run-id", "alias-source", "--input", first_id, "--sampling", source["id"]
    )
    second = service.invoke(
        "run",
        "--config",
        "config/alias-experiment.json",
        "--run-id",
        "alias-target",
        "--input",
        second_id,
        "--sampling",
        "canonical",
    )
    assert first.returncode == second.returncode == 0
    directory = service.project / "results/runs"
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.rglob("*.json")
    }
    count = len(service.requests)

    plain = service.invoke("evaluate", "alias-source", "alias-target")
    result = service.invoke(
        "evaluate",
        "alias-source",
        "alias-target",
        "--sampling-aliases",
        "config/sampling-aliases.json",
    )

    assert plain.returncode == 0 and len(json.loads(plain.stdout)["variants"]) == 2
    if overlap:
        assert result.returncode == 2
        assert json.loads(result.stdout) == {"setup_error": "ValueError"}
    else:
        assert result.returncode == 0, result.stdout + result.stderr
        report = json.loads(result.stdout)
        assert len(report["variants"]) == 1
        variant = report["variants"][0]
        assert variant["operational"]["selected_inputs"] == 2
        assert variant["identity"]["sampling"]["id"] == "canonical"
        assert {item["sampling"]["id"] for item in variant["source_sampling"]} == {
            source["id"],
            "canonical",
        }
    assert len(service.requests) == count
    assert before == {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in directory.rglob("*.json")
    }
