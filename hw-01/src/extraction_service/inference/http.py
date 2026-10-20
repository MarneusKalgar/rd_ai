"""HTTP ownership, timing and typed failures with automatic retries disabled."""

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any, Literal, Protocol

import httpx

from extraction_service.extraction.json_parsing import parse_json
from extraction_service.inference.errors import (
    FailureEvidence,
    FailureKind,
    ModelTransportError,
    classify_error_body,
    error_usage,
)


@dataclass(frozen=True)
class HttpReply:
    """Decoded remote envelope alongside the original, credential-safe body."""

    body: dict[str, Any]
    raw_body: str
    duration_ms: float
    credentials_redacted: bool


class HttpPoster(Protocol):
    """Borrowed request capability; client ownership stays with application setup."""

    def post(self, path: str, payload: dict[str, Any], timeout_seconds: float) -> HttpReply: ...


class _ControlledTransport(httpx.AsyncBaseTransport):
    """Adapt injected synchronous test transports to the client's private event loop.

    Production uses AsyncHTTPTransport directly. Controlled handlers must return
    promptly; they are an I/O substitute, not a worker for arbitrary blocking code.
    """

    def __init__(self, transport: httpx.BaseTransport) -> None:
        self._transport = transport

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        response = self._transport.handle_request(request)

        try:
            return httpx.Response(
                response.status_code,
                headers=response.headers,
                content=response.read(),
                extensions=response.extensions,
            )
        finally:
            response.close()

    async def aclose(self) -> None:
        self._transport.close()


class JsonHttpClient:
    """Own a client that sends one request, follows no redirects and ignores host proxies.

    A test transport can replace HTTP I/O. The production transport has retries=0;
    retry policy belongs to the coordinator. Only the owner closes this client,
    after all adapters borrowing it have finished.
    """

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        headers = {}

        if api_key is not None:
            headers["Authorization"] = f"Bearer {api_key}"

        self._runner = asyncio.Runner()
        self._closed = False
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/") + "/",
            headers=headers,
            transport=(
                _ControlledTransport(transport)
                if transport is not None
                else httpx.AsyncHTTPTransport(retries=0)
            ),
            follow_redirects=False,
            trust_env=False,
        )

    def close(self) -> None:
        if self._closed:
            return

        self._closed = True

        try:
            self._runner.run(self._client.aclose())
        finally:
            self._runner.close()

    def _redact(self, text: str) -> str:
        if self._api_key is None:
            return text

        return text.replace(self._api_key, "[REDACTED]")

    def post(self, path: str, payload: dict[str, Any], timeout_seconds: float) -> HttpReply:
        """Send one POST; preserve available failures without logging request headers."""

        return self._request("POST", path, payload, timeout_seconds)

    def get(self, path: str, timeout_seconds: float) -> HttpReply:
        """Read model metadata without performing inference."""

        return self._request("GET", path, None, timeout_seconds)

    def _request(
        self,
        method: Literal["GET", "POST"],
        path: str,
        payload: dict[str, Any] | None,
        timeout_seconds: float,
    ) -> HttpReply:
        if self._closed:
            raise RuntimeError("Cannot send requests on a closed HTTP client")

        started = perf_counter()

        try:
            response = self._runner.run(self._send(method, path, payload, timeout_seconds))
        except (httpx.RequestError, TimeoutError) as error:
            if isinstance(error, (httpx.TimeoutException, TimeoutError)):
                kind = FailureKind.TIMEOUT
            else:
                kind = FailureKind.CONNECTION

            original_message = str(error) or "Total request deadline exceeded"
            message = self._redact(original_message)
            evidence = FailureEvidence(
                kind=kind,
                retryable=True,
                message=message,
                duration_ms=(perf_counter() - started) * 1000,
                credentials_redacted=message != original_message,
            )

            raise ModelTransportError(evidence) from None

        duration_ms = (perf_counter() - started) * 1000

        return self._decode_response(response, duration_ms)

    async def _send(
        self,
        method: Literal["GET", "POST"],
        path: str,
        payload: dict[str, Any] | None,
        timeout_seconds: float,
    ) -> httpx.Response:
        """Cancel network I/O at a total deadline, including a slowly streamed body."""

        async with asyncio.timeout(timeout_seconds):
            return await self._client.request(method, path, json=payload, timeout=timeout_seconds)

    def _decode_response(self, response: httpx.Response, duration_ms: float) -> HttpReply:
        """Separate HTTP failure evidence from strict envelope decoding."""

        original_body = response.text
        raw_body = self._redact(original_body)
        original_retry_after = response.headers.get("Retry-After", "")
        retry_after = self._redact(original_retry_after)
        redacted = original_body != raw_body or original_retry_after != retry_after

        if response.status_code != 200:
            kind, retryable = classify_error_body(response.status_code, raw_body)
            usage = error_usage(raw_body)
            evidence = FailureEvidence(
                kind=kind,
                retryable=retryable,
                message=f"HTTP {response.status_code}",
                status_code=response.status_code,
                raw_http_body=raw_body,
                duration_ms=duration_ms,
                retry_after=retry_after or None,
                credentials_redacted=redacted,
                input_tokens=usage.prompt_tokens,
                output_tokens=usage.completion_tokens,
                cost_usd=usage.cost,
            )

            raise ModelTransportError(evidence)

        try:
            parsed = parse_json(raw_body)

            if not isinstance(parsed, dict):
                raise ValueError("Response envelope must be a JSON object")
        except ValueError, RecursionError:
            raise protocol_error(raw_body, duration_ms, redacted) from None

        return HttpReply(parsed, raw_body, duration_ms, redacted)


def protocol_error(
    raw_body: str, duration_ms: float, redacted: bool = False
) -> ModelTransportError:
    """Keep malformed response envelopes as evidence without trying to repair them."""

    return ModelTransportError(
        FailureEvidence(
            kind=FailureKind.PROTOCOL_ERROR,
            retryable=False,
            message="Unusable model response envelope",
            raw_http_body=raw_body,
            duration_ms=duration_ms,
            credentials_redacted=redacted,
        )
    )
