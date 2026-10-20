"""Ollama structured-output adapter, with installed model/runtime identity."""

from copy import deepcopy

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.capabilities import OllamaRuntime
from extraction_service.inference.http import HttpPoster
from extraction_service.inference.messages import request_messages
from extraction_service.inference.ollama_payloads import parse_completion
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
    ) -> None:
        self._identity = runtime.identity(config, native=native)
        self._http = http_client

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    def generate(self, request: GenerationRequest) -> ModelResponse:
        """Send the full schema and explicit common options with streaming disabled."""

        payload = {
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

        reply = self._http.post("api/chat", payload, request.timeout_seconds)

        return parse_completion(reply, self.identity)
