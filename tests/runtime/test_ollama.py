"""Setup failures start from valid model metadata and change one relevant fact."""

import httpx
import pytest

from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.runtime.configuration import ModelPin, SetupSettings
from extraction_service.runtime.ollama import initialize_model, load_model, wait_for_server

from .conftest import OllamaServer


def test_pull_once_then_reuse_exact_installation(
    client: JsonHttpClient, server: OllamaServer, pin: ModelPin, setup_settings: SetupSettings
) -> None:
    installed, pulled = initialize_model(client, pin, setup_settings)
    reused, pulled_again = initialize_model(client, pin, setup_settings)

    assert pulled is True
    assert pulled_again is False
    assert installed == reused
    assert installed.digest == pin.digest
    assert [path for path, _ in server.requests].count("/api/pull") == 1
    pull_payload = server.requests[1][1]
    assert pull_payload == {"model": pin.model, "stream": False}


def test_changed_installed_digest_is_rejected_without_pull(
    client: JsonHttpClient, server: OllamaServer, pin: ModelPin, setup_settings: SetupSettings
) -> None:
    server.replacements["/api/tags"] = {
        "models": [{"name": pin.model, "digest": "b" * 64, "size": 100}]
    }

    with pytest.raises(ValueError, match="digest differs"):
        initialize_model(client, pin, setup_settings)

    assert [path for path, _ in server.requests] == ["/api/tags"]


@pytest.mark.parametrize("defect", ["failed_pull", "reported_failure", "still_missing"])
def test_initialization_never_accepts_partial_success(
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
    defect: str,
) -> None:
    expected: type[Exception]

    if defect == "failed_pull":
        server.status_codes["/api/pull"] = 500
        server.replacements["/api/pull"] = {"error": "registry unavailable"}
        expected = ModelTransportError
        message = "HTTP 500"
    elif defect == "reported_failure":
        server.replacements["/api/pull"] = {"status": "downloading"}
        expected = ValueError
        message = "pull did not complete"
    else:
        server.replacements["/api/tags"] = {"models": []}
        expected = ValueError
        message = "tag is missing"

    with pytest.raises(expected, match=message):
        initialize_model(client, pin, setup_settings)

    assert [path for path, _ in server.requests].count("/api/pull") == 1


@pytest.mark.parametrize("defect", ["missing", "digest", "context", "incomplete", "wrong_name"])
def test_loaded_readiness_requires_exact_model_and_applied_context(
    client: JsonHttpClient,
    server: OllamaServer,
    pin: ModelPin,
    setup_settings: SetupSettings,
    defect: str,
) -> None:
    model = {
        "name": pin.model,
        "digest": pin.digest,
        "size": 100,
        "size_vram": 0,
        "context_length": 16384,
    }
    server.replacements["/api/ps"] = {"models": [model]}
    message = ""

    if defect == "missing":
        server.replacements["/api/ps"] = {"models": []}
        message = "not loaded"
    elif defect == "digest":
        model["digest"] = "b" * 64
        message = "digest differs"
    elif defect == "context":
        model["context_length"] = 4096
        message = "context differs"
    else:
        server.replacements["/api/generate"] = {
            "model": "different" if defect == "wrong_name" else pin.model,
            "done": defect != "incomplete",
        }
        message = "confirm loading"

    with pytest.raises(ValueError, match=message):
        load_model(client, pin, setup_settings)


def test_empty_load_requests_real_context_without_inference(
    client: JsonHttpClient, server: OllamaServer, pin: ModelPin, setup_settings: SetupSettings
) -> None:
    loaded = load_model(client, pin, setup_settings)

    assert loaded.context_length == 16384
    assert loaded.size_vram == 0
    assert server.requests[0] == (
        "/api/generate",
        {
            "model": pin.model,
            "prompt": "",
            "stream": False,
            "keep_alive": 600,
            "options": {"num_ctx": 16384},
        },
    )


def test_unavailable_server_has_one_overall_wait_deadline(setup_settings: SetupSettings) -> None:
    seconds = 0.0
    calls = 0

    def clock() -> float:
        return seconds

    def pause(delay: float) -> None:
        nonlocal seconds
        seconds += delay

    def unavailable(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("not running", request=request)

    settings = setup_settings.model_copy(update={"wait_seconds": 2.5, "poll_seconds": 1.0})
    client = JsonHttpClient("http://controlled", transport=httpx.MockTransport(unavailable))

    try:
        with pytest.raises(ValueError, match="before setup deadline"):
            wait_for_server(client, settings, clock=clock, pause=pause)
    finally:
        client.close()

    assert seconds == 2.5
    assert calls == 3
