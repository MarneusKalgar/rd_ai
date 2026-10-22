"""Ollama structured-output adapter, with installed model/runtime identity."""

from copy import deepcopy
from typing import Any

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.messages import request_messages
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.ollama.payloads import parse_completion
from extraction_service.inference.transport.http import HttpPoster
from extraction_service.inference.types import GenerationRequest, ModelIdentity, ModelResponse


class OllamaAdapter:
    """Translate common sampling values into Ollama options for one generation."""

    def __init__(
        self,
        config: ModelConfig,
        runtime: OllamaRuntime,
        *,
        http_client: HttpPoster,
        native: bool = False,
        context_length: int | None = None,
    ) -> None:
        self._identity = runtime.identity(config, native=native)
        self._http = http_client
        self._context_length = context_length
        self._thinking = config.thinking

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    def generate(self, request: GenerationRequest) -> ModelResponse:
        """Send the full schema and explicit common options with streaming disabled."""

        payload: dict[str, Any] = {
            "model": self.identity.model_name,
            "messages": request_messages(request),
            "format": deepcopy(request.output_schema),
            "stream": False,
            "options": {
                "temperature": request.sampling.temperature,
                "top_p": request.sampling.top_p,
                "num_predict": request.sampling.max_output_tokens,
            },
        }

        if self._thinking is not None:
            payload["think"] = self._thinking

        if self._context_length is not None:
            payload["truncate"] = False
            payload["shift"] = False
            payload["options"]["num_ctx"] = self._context_length

        reply = self._http.post("api/chat", payload, request.timeout_seconds)

        return parse_completion(reply, self.identity)
