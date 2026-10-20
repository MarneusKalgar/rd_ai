"""Explicit client scopes owned by application setup, independent of model adapters."""

from collections.abc import Generator
from contextlib import closing, contextmanager

import httpx

from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.inference.http import JsonHttpClient


@contextmanager
def openrouter_client(
    settings: ApplicationSettings,
    *,
    transport: httpx.BaseTransport | None = None,
) -> Generator[JsonHttpClient]:
    """Own one authenticated client scope, reusable by compatible provider adapters.

    Enter this scope once per service URL and credential configuration in a run.
    Construct adapters inside it so setup failures also release the client.
    No metadata, inference or model-pull request occurs during construction.
    """

    credential = settings.require_provider_credentials()
    client = JsonHttpClient(
        str(settings.openrouter_base_url),
        api_key=credential.get_secret_value(),
        transport=transport,
    )

    with closing(client):
        yield client


@contextmanager
def openrouter_metadata_client(
    settings: ApplicationSettings,
    *,
    transport: httpx.BaseTransport | None = None,
) -> Generator[JsonHttpClient]:
    """Own a separate unauthenticated client scope for explicit public catalog probes."""

    client = JsonHttpClient(str(settings.openrouter_base_url), transport=transport)

    with closing(client):
        yield client


@contextmanager
def ollama_client(
    settings: ApplicationSettings,
    *,
    transport: httpx.BaseTransport | None = None,
) -> Generator[JsonHttpClient]:
    """Own one unauthenticated scope for an explicitly configured Ollama service URL.

    Adapters can share this client while the scope remains open. A different
    service URL, including a native runtime, requires a separate client scope.
    """

    client = JsonHttpClient(str(settings.ollama_base_url), transport=transport)

    with closing(client):
        yield client
