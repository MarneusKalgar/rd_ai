"""OpenRouter structured-output adapter with explicit provider and parameter routing."""

from copy import deepcopy
from typing import Any

import httpx

from extraction_service.configuration.models import ModelConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.capabilities import OpenRouterEndpoint
from extraction_service.inference.http import JsonHttpClient
from extraction_service.inference.messages import request_messages
from extraction_service.inference.openrouter_payloads import parse_completion
from extraction_service.inference.types import GenerationRequest, ModelIdentity, ModelResponse


class OpenRouterAdapter:
    """One non-streaming generation; callers own validation, retries and paid budgets."""

    def __init__(
        self,
        config: ModelConfig,
        settings: ApplicationSettings,
        endpoint: OpenRouterEndpoint,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        endpoint.check(config)
        key = settings.require_provider_credentials()
        self._endpoint = endpoint
        self._identity = ModelIdentity(
            model_id=config.id,
            model_name=config.model,
            runtime="openrouter",
            serving_provider=endpoint.provider_slug,
        )
        self._http = JsonHttpClient(
            str(settings.openrouter_base_url),
            api_key=key.get_secret_value(),
            transport=transport,
        )

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    def close(self) -> None:
        self._http.close()

    def _payload(self, request: GenerationRequest) -> dict[str, Any]:
        maximum = self._endpoint.max_output_tokens

        if maximum is not None and request.sampling.max_output_tokens > maximum:
            raise ValueError("Requested output tokens exceed the verified endpoint limit")

        return {
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

    def generate(self, request: GenerationRequest) -> ModelResponse:
        """Send exactly one inference request and preserve the returned evidence."""

        payload = self._payload(request)
        reply = self._http.post("chat/completions", payload, request.timeout_seconds)

        return parse_completion(reply, self.identity)
