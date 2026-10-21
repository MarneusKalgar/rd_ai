"""Token admission uses complete rendered requests and the full output allowance."""

from pathlib import Path

import pytest

from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.preflight import preflight
from extraction_service.runtime.capacity import measure_capacity
from extraction_service.runtime.configuration import ModelPin, SetupSettings
from extraction_service.runtime.context import context_inventory, prepared_requests

from .conftest import OllamaServer


def test_inventory_includes_all_sources_and_complete_correction_evidence(
    project_copy: Path,
) -> None:
    experiment = preflight(project_copy).experiment
    requests = list(prepared_requests(project_copy, experiment))

    inventory = context_inventory(project_copy, experiment)

    assert len(requests) == 60
    assert len({request.input_id for request in requests}) == 30
    assert inventory["token_capacity_verified"] is False
    assert inventory["future_corrections_require_actual_request_admission"] is True
    assert inventory["largest_by_bytes"]["message_utf8_bytes"] > 54000
    initial, correction = requests[:2]
    assert initial.request.source_text == correction.request.source_text
    assert "Correction evidence:" not in initial.request.instructions
    assert '"invalid_response": "{}"' in correction.request.instructions
    assert '"validation_issues": [{' in correction.request.instructions
    assert initial.request.output_schema == correction.request.output_schema


def test_capacity_checks_every_prepared_request_not_only_largest_byte_count(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
) -> None:
    requests = list(prepared_requests(project_copy, preflight(project_copy).experiment))

    report = measure_capacity(client, requests, pin, setup_settings)

    assert report["token_capacity_verified"] is True
    assert len(report["measurements"]) == 60
    payload = server.requests[0][1]
    assert payload is not None
    assert payload["truncate"] is False
    assert payload["shift"] is False
    assert payload["options"] == {
        "num_ctx": 16384,
        "num_predict": 1,
        "temperature": 0.0,
        "top_p": 1.0,
    }
    assert payload["format"] == requests[0].request.output_schema
    assert payload["messages"][0]["content"].startswith(requests[0].request.instructions)
    assert "JSON Schema:" in payload["messages"][0]["content"]
    assert payload["messages"][1]["content"] == requests[0].request.source_text
    correction_payload = server.requests[1][1]
    assert correction_payload is not None
    assert '"validation_issues"' in correction_payload["messages"][0]["content"]
    assert report["measurements"][0]["required_context_tokens"] == 5096


def test_capacity_reserves_actual_output_allowance_and_accepts_exact_boundary(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
) -> None:
    requests = list(prepared_requests(project_copy, preflight(project_copy).experiment))[:1]
    server.replacements["/api/chat"] = {
        "model": pin.model,
        "done": True,
        "prompt_eval_count": 12288,
    }

    exact = measure_capacity(client, requests, pin, setup_settings)
    server.replacements["/api/chat"]["prompt_eval_count"] = 12289
    overflow = measure_capacity(client, requests, pin, setup_settings)

    assert exact["token_capacity_verified"] is True
    assert overflow["token_capacity_verified"] is False
    assert overflow["blocker"] == "insufficient_context"
    assert overflow["largest_measured"]["required_context_tokens"] == 16385


@pytest.mark.parametrize("defect", ["missing_count", "zero_count", "incomplete", "wrong_model"])
def test_capacity_does_not_infer_success_from_http_200(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
    defect: str,
) -> None:
    requests = list(prepared_requests(project_copy, preflight(project_copy).experiment))[:1]
    body: dict[str, object] = {"model": pin.model, "done": True, "prompt_eval_count": 1000}

    if defect == "missing_count":
        del body["prompt_eval_count"]
    elif defect == "zero_count":
        body["prompt_eval_count"] = 0
    elif defect == "incomplete":
        body["done"] = False
    else:
        body["model"] = "different-model"

    server.replacements["/api/chat"] = body

    with pytest.raises(ValueError):
        measure_capacity(client, requests, pin, setup_settings)


def test_capacity_has_overall_deadline_before_next_request(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
) -> None:
    readings = iter([0.0, 901.0])
    requests = prepared_requests(project_copy, preflight(project_copy).experiment)

    report = measure_capacity(client, requests, pin, setup_settings, clock=lambda: next(readings))

    assert report["token_capacity_verified"] is False
    assert report["blocker"] == "capacity_deadline_exceeded"
    assert server.requests == []


def test_capacity_failure_keeps_the_affected_request_and_partial_measurements(
    project_copy: Path,
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
) -> None:
    requests = list(prepared_requests(project_copy, preflight(project_copy).experiment))[:1]
    server.status_codes["/api/chat"] = 400
    server.replacements["/api/chat"] = {"error": "request exceeds the available context size"}

    report = measure_capacity(client, requests, pin, setup_settings)

    assert report["token_capacity_verified"] is False
    assert report["blocker"] == "local_capacity_request_failed"
    assert report["failed_request"]["input_id"] == requests[0].input_id
    assert report["http_status"] == 400
    assert "exceeds the available context" in report["body"]
    assert report["measurements"] == []
