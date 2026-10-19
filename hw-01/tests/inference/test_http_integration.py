"""Exercise the production HTTP transport against a loopback server, without inference."""

import json
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any

import pytest
from pydantic import AnyHttpUrl

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.capabilities import OllamaRuntime
from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.ollama import OllamaAdapter
from extraction_service.inference.types import GenerationRequest


@pytest.mark.parametrize("status", [200, 503])
def test_real_http_transport_sends_one_request_and_ignores_host_proxy(
    status: int,
    monkeypatch: pytest.MonkeyPatch,
    settings: ApplicationSettings,
    local_config: ModelConfig,
    runtime: OllamaRuntime,
    generation: GenerationRequest,
    response_body: Callable[[str], dict[str, Any]],
) -> None:
    captured: list[tuple[str, dict[str, Any]]] = []
    raw_body = json.dumps(response_body("ollama")).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:
            length = int(self.headers["Content-Length"])
            payload = json.loads(self.rfile.read(length))
            captured.append((self.path, payload))
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw_body)))
            self.end_headers()
            self.wfile.write(raw_body)

        def log_message(self, format: str, *args: object) -> None:
            pass

    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("ALL_PROXY", "http://127.0.0.1:1")
    monkeypatch.setenv("NO_PROXY", "")

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        worker = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        worker.start()
        base_url = AnyHttpUrl(f"http://127.0.0.1:{server.server_port}")
        local_settings = settings.model_copy(update={"ollama_base_url": base_url})
        adapter = OllamaAdapter(local_config, local_settings, runtime)

        try:
            if status == 200:
                result = adapter.generate(generation)
                assert result.raw_response == "  {invalid PO}\n"
            else:
                with pytest.raises(ModelTransportError) as failure:
                    adapter.generate(generation)

                assert failure.value.evidence.kind == "server_error"
                assert failure.value.evidence.raw_http_body == raw_body.decode()
        finally:
            adapter.close()
            server.shutdown()
            worker.join(timeout=1)

    assert len(captured) == 1
    assert captured[0][0] == "/api/chat"
    assert captured[0][1]["options"]["num_predict"] == 512
