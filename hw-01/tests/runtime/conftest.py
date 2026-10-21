"""Controlled Ollama service; ordinary tests never contact a model runtime."""

import json
from collections.abc import Generator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pytest

from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.runtime.configuration import ModelPin, SetupSettings, load_model_pin


@dataclass
class OllamaServer:
    pin: ModelPin
    installed: bool = False
    unload_fails: bool = False
    requests: list[tuple[str, dict[str, Any] | None]] = field(default_factory=list)
    replacements: dict[str, dict[str, Any]] = field(default_factory=dict)
    status_codes: dict[str, int] = field(default_factory=dict)

    def handle(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        payload = json.loads(request.content) if request.method == "POST" else None
        self.requests.append((path, payload))

        if path == "/api/generate" and payload is not None:
            if payload.get("keep_alive") == 0 and self.unload_fails:
                return httpx.Response(500, json={"error": "simulated unload failure"})

        model = {"name": self.pin.model, "digest": self.pin.digest, "size": 6_100_000_000}
        responses: dict[str, dict[str, Any]] = {
            "/api/version": {"version": self.pin.server_version},
            "/api/tags": {"models": [model] if self.installed else []},
            "/api/show": {"capabilities": ["completion", "vision"]},
            "/api/pull": {"status": "success"},
            "/api/generate": {"model": self.pin.model, "done": True},
            "/api/ps": {"models": [dict(model, size_vram=0, context_length=16384)]},
            "/api/chat": {"model": self.pin.model, "done": True, "prompt_eval_count": 1000},
        }

        if path == "/api/pull" and self.status_codes.get(path, 200) == 200:
            self.installed = True

        return httpx.Response(
            self.status_codes.get(path, 200),
            json=self.replacements.get(path, responses[path]),
        )


@pytest.fixture
def setup_settings() -> SetupSettings:
    return SetupSettings(image="ollama/ollama@sha256:" + "a" * 64, context_length=16384)


@pytest.fixture
def pin(project_copy: Path) -> ModelPin:
    return load_model_pin(project_copy)


@pytest.fixture
def server(pin: ModelPin) -> OllamaServer:
    return OllamaServer(pin)


@pytest.fixture
def client(server: OllamaServer) -> Generator[JsonHttpClient]:
    client = JsonHttpClient(
        "http://controlled-ollama", transport=httpx.MockTransport(server.handle)
    )

    try:
        yield client
    finally:
        client.close()
