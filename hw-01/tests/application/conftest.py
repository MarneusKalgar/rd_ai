"""Loopback HTTP process tests; no installed model or external account."""

import json
import os
import subprocess
import sys
from collections.abc import Generator
from dataclasses import dataclass, field
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread
from typing import Any

import pytest
from pydantic import AnyHttpUrl

from extraction_service.application.admission import ProviderCoverage, request_fingerprint
from extraction_service.application.selection import RunOptions, selected_jobs
from extraction_service.configuration.loading import load_experiment
from extraction_service.corpus.loading import load_corpus
from extraction_service.execution.budget.pricing import VerifiedPricing
from extraction_service.execution.types import DependencyIdentity
from extraction_service.inference.types import GenerationRequest
from extraction_service.record_types import ModelRuntime
from extraction_service.runtime.configuration import load_model_pin


def tokenizer_info() -> dict[str, Any]:
    tokens = ["<unk>", "<bos>", "a", "b", "ab", "▁", "\n"]
    tokens.extend(f"<0x{byte:02X}>" for byte in range(256))

    return {
        "tokenizer.ggml.model": "gemma4",
        "tokenizer.ggml.tokens": tokens,
        "tokenizer.ggml.token_type": [2, 3, 1, 1, 1, 1, 1] + [6] * 256,
        "tokenizer.ggml.merges": ["a b"],
        "tokenizer.ggml.add_space_prefix": False,
    }


@dataclass
class ControlledService:
    project: Path
    base_url: str = ""
    responses: list[str] = field(default_factory=list)
    requests: list[tuple[str, dict[str, Any] | None, str | None]] = field(default_factory=list)
    generation_status: int = 200
    generation_started: Event = field(default_factory=Event)
    release_generation: Event = field(default_factory=Event)
    block_generation: bool = False
    rendered_override: str | None = None

    def reply(self, path: str, payload: dict[str, Any] | None) -> tuple[int, dict[str, Any]]:
        pin = load_model_pin(self.project)
        model = {
            "name": pin.model,
            "digest": pin.digest,
            "size": 100,
            "size_vram": 0,
            "context_length": 32768,
        }

        if path.endswith("/endpoints"):
            return 200, {
                "data": {
                    "id": "google/gemini-3.8-flash",
                    "endpoints": [
                        {
                            "model_id": "google/gemini-3.8-flash",
                            "tag": "google-ai-studio",
                            "provider_name": "Google AI Studio",
                            "supported_parameters": [
                                "temperature",
                                "top_p",
                                "max_tokens",
                                "response_format",
                                "structured_outputs",
                            ],
                            "max_completion_tokens": 65536,
                            "pricing": {"prompt": "0.0000001", "completion": "0.0000002"},
                        }
                    ],
                }
            }

        metadata: dict[str, dict[str, Any]] = {
            "/api/version": {"version": pin.server_version},
            "/api/tags": {"models": [model]},
            "/api/show": {"capabilities": ["completion"], "model_info": tokenizer_info()},
            "/api/generate": {"model": pin.model, "done": True},
            "/api/ps": {"models": [model]},
        }

        if path in metadata:
            return 200, metadata[path]

        assert payload is not None

        if payload.get("_debug_render_only"):
            rendered = self.rendered_override

            if rendered is None:
                rendered = "<bos>" + "\n".join(
                    message["content"] for message in payload["messages"]
                )

            return 200, {"model": pin.model, "_debug_info": {"rendered_template": rendered}}

        self.generation_started.set()

        if self.block_generation:
            self.release_generation.wait(10)

        if self.generation_status != 200:
            return self.generation_status, {"error": "controlled temporary failure"}

        content = self.responses.pop(0) if self.responses else "{}"

        if path == "/api/v1/chat/completions":
            return 200, {
                "model": "google/gemini-3.8-flash",
                "provider": "Google AI Studio",
                "choices": [
                    {"finish_reason": "stop", "message": {"role": "assistant", "content": content}}
                ],
                "usage": {"prompt_tokens": 20, "completion_tokens": 10, "cost": 0.00001},
            }

        assert path == "/api/chat"

        return 200, {
            "model": pin.model,
            "done": True,
            "done_reason": "stop",
            "message": {"role": "assistant", "content": content},
            "prompt_eval_count": 20,
            "eval_count": 10,
            "total_duration": 1000,
            "load_duration": 0,
        }

    def environment(self) -> dict[str, str]:
        return {
            **os.environ,
            "PYTHONPATH": str(Path(__file__).resolve().parents[2] / "src"),
            "HW01_OLLAMA_BASE_URL": self.base_url,
            "HW01_OPENROUTER_BASE_URL": self.base_url + "/api/v1",
            "OPENROUTER_API_KEY": "controlled-test-key",
            "HW01_SETUP_IMAGE": "ollama/ollama@sha256:" + "a" * 64,
        }

    def invoke(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                "-m",
                "extraction_service",
                "--project-dir",
                str(self.project),
                *arguments,
            ],
            env=self.environment(),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def coverage(self, input_ids: list[str]) -> None:
        experiment = load_experiment(self.project / "config/experiments.yaml")
        corpus = load_corpus(self.project)
        jobs = selected_jobs(
            self.project, corpus, experiment, RunOptions(input_ids=input_ids), "a" * 64
        )
        bounds = {}

        for job in jobs:
            request = GenerationRequest.from_contract(
                instructions=job.instructions,
                source_text=job.source_text,
                contract=corpus.contract,
                sampling=job.sampling,
                timeout_seconds=1.0,
            )
            bounds[request_fingerprint(request)] = 20000

        coverage = ProviderCoverage(
            pricing=VerifiedPricing(
                dependency=DependencyIdentity(
                    runtime=ModelRuntime.OPENROUTER,
                    endpoint=AnyHttpUrl(self.base_url + "/api/v1/"),
                    model_name="google/gemini-3.8-flash",
                    serving_provider="google-ai-studio",
                ),
                input_token_ceiling=32768,
                output_token_ceiling=4096,
                input_usd_per_token=Decimal("0.0000001"),
                output_usd_per_token=Decimal("0.0000002"),
                request_usd=Decimal("0"),
                evidence="Fictional loopback test prices only",
            ),
            context_length=32768,
            request_token_bounds=bounds,
            evidence="Controlled test bound only; not live provider evidence",
        )
        content = json.dumps({"provider": coverage.model_dump(mode="json")})
        (self.project / "config/coverage.json").write_text(content)


@pytest.fixture
def service(project_copy: Path) -> Generator[ControlledService]:
    service = ControlledService(project_copy)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.respond(None)

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length))
            self.respond(payload)

        def respond(self, payload: dict[str, Any] | None) -> None:
            service.requests.append((self.path, payload, self.headers.get("Authorization")))
            status, body = service.reply(self.path, payload)
            content = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()

            try:
                self.wfile.write(content)
            except BrokenPipeError:
                pass

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    service.base_url = f"http://127.0.0.1:{server.server_port}"
    worker = Thread(target=server.serve_forever, daemon=True)
    worker.start()
    pin = load_model_pin(project_copy)
    directory = project_copy / "results/setup"
    directory.mkdir(parents=True)
    (directory / "installation.json").write_text(
        json.dumps(
            {
                "image": "ollama/ollama@sha256:" + "a" * 64,
                "runtime": {
                    "version": pin.server_version,
                    "model_name": pin.model,
                    "model_digest": pin.digest,
                    "capabilities": ["completion"],
                },
                "initialized_at": "2026-10-21T00:00:00Z",
                "installed_bytes": 100,
                "initialization_duration_ms": 0.0,
            }
        )
    )

    try:
        yield service
    finally:
        service.release_generation.set()
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
