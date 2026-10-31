"""OpenRouter structured-output adapter with explicit provider and parameter routing."""

from copy import deepcopy
from typing import Any

from extraction_service.configuration.models import ModelConfig
from extraction_service.inference.errors import ModelConfigurationError
from extraction_service.inference.messages import request_messages
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.openrouter.payloads import parse_completion
from extraction_service.inference.transport.http import HttpPoster
from extraction_service.inference.types import GenerationRequest, ModelIdentity, ModelResponse
from extraction_service.record_types import ModelRuntime


class OpenRouterAdapter:
    """One non-streaming generation; callers own validation, retries and paid budgets."""

    def __init__(
        self,
        config: ModelConfig,
        endpoint: OpenRouterEndpoint,
        *,
        http_client: HttpPoster,
        server_context: bool = False,
    ) -> None:
        endpoint.check(config)
        self._endpoint = endpoint
        self._identity = ModelIdentity(
            model_id=config.id,
            model_name=config.model,
            runtime=ModelRuntime.OPENROUTER,
            serving_provider=endpoint.provider_slug,
        )
        self._http = http_client
        self._server_context = server_context

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    def _payload(self, request: GenerationRequest) -> dict[str, Any]:
        maximum = self._endpoint.max_output_tokens

        if maximum is not None and request.sampling.max_output_tokens > maximum:
            raise ModelConfigurationError(
                "Requested output tokens exceed the verified endpoint limit"
            )

        payload: dict[str, Any] = {
            "model": self.identity.model_name,
            "messages": request_messages(request),
            "stream": False,
            "temperature": request.sampling.temperature,
            "top_p": request.sampling.top_p,
            "max_tokens": request.sampling.max_output_tokens,
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "purchase_order_extraction",
                    "strict": True,
                    "schema": deepcopy(request.output_schema),
                },
            },
            "provider": {
                "only": [self._endpoint.provider_slug],
                "allow_fallbacks": False,
                "require_parameters": True,
            },
            "plugins": [],
        }

        if self._server_context:
            # Explicit disabling overrides compression defaults; the full input
            # must be rejected when oversized, never shortened to fit.
            payload["plugins"] = [{"id": "context-compression", "enabled": False}]
            payload["service_tier"] = "default"

        return payload

    def generate(self, request: GenerationRequest) -> ModelResponse:
        """Send exactly one inference request and preserve the returned evidence."""

        payload = self._payload(request)
        reply = self._http.post("chat/completions", payload, request.timeout_seconds)

        return parse_completion(reply, self.identity)
