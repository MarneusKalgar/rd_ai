"""Bounded local service discovery, exact installation and load diagnostics."""

from collections.abc import Callable
from time import monotonic, sleep

from extraction_service.inference.errors import FailureKind, ModelTransportError
from extraction_service.inference.ollama.capabilities import OllamaRuntime
from extraction_service.inference.transport.http import JsonHttpClient
from extraction_service.inference.wire_models import WireModel
from extraction_service.runtime.configuration import ModelPin, OllamaSetupSettings
from extraction_service.runtime.errors import SetupError
from extraction_service.runtime_types import NonEmptyText, NonNegativeInt, PositiveInt, Sha256


class Version(WireModel):
    version: NonEmptyText


class InstalledModel(WireModel):
    name: NonEmptyText
    digest: Sha256
    size: NonNegativeInt


class Tags(WireModel):
    models: list[InstalledModel]


class Details(WireModel):
    capabilities: list[str]


class LoadedModel(InstalledModel):
    size_vram: NonNegativeInt
    context_length: PositiveInt


class Processes(WireModel):
    models: list[LoadedModel]


class PullResult(WireModel):
    status: NonEmptyText


class LoadResult(WireModel):
    model: NonEmptyText
    done: bool


def wait_for_server(
    client: JsonHttpClient,
    settings: OllamaSetupSettings,
    *,
    clock: Callable[[], float] = monotonic,
    pause: Callable[[float], None] = sleep,
) -> str:
    """Retry only transient service availability until a single overall deadline."""

    deadline = clock() + settings.wait_seconds

    while True:
        remaining = deadline - clock()

        if remaining <= 0:
            raise SetupError("Ollama did not respond before setup deadline; check its logs")

        try:
            reply = client.get("api/version", min(settings.request_seconds, remaining))
            return Version.model_validate(reply.body).version
        except ModelTransportError as error:
            if error.evidence.kind not in {FailureKind.CONNECTION, FailureKind.TIMEOUT}:
                raise

        pause(min(settings.poll_seconds, max(0.0, deadline - clock())))


def installed_model(
    client: JsonHttpClient, pin: ModelPin, settings: OllamaSetupSettings
) -> InstalledModel | None:
    """Reject a tag that now resolves to different bytes; never repair it by pulling."""

    reply = client.get("api/tags", settings.request_seconds)
    tags = Tags.model_validate(reply.body)

    for model in tags.models:
        if model.name == pin.model:
            if model.digest != pin.digest:
                raise SetupError("Installed model digest differs from the reviewed model pin")

            return model

    return None


def initialize_model(
    client: JsonHttpClient, pin: ModelPin, settings: OllamaSetupSettings
) -> tuple[InstalledModel, bool]:
    """Pull only an absent, explicitly selected model and verify its resolved digest."""

    installed = installed_model(client, pin, settings)

    if installed is not None:
        return installed, False

    reply = client.post("api/pull", {"model": pin.model, "stream": False}, settings.pull_seconds)
    result = PullResult.model_validate(reply.body)

    if result.status != "success":
        raise SetupError("Ollama model pull did not complete; retry explicit local setup")

    installed = installed_model(client, pin, settings)

    if installed is None:
        raise SetupError("Model pull returned success but the configured tag is missing")

    return installed, True


def model_runtime(
    client: JsonHttpClient, pin: ModelPin, version: str, settings: OllamaSetupSettings
) -> OllamaRuntime:
    """Verify completion capability separately from installation and memory fit."""

    reply = client.post("api/show", {"model": pin.model}, settings.request_seconds)
    details = Details.model_validate(reply.body)

    if "completion" not in details.capabilities:
        raise SetupError("Selected model lacks text completion capability")

    return OllamaRuntime(
        version=version,
        model_name=pin.model,
        model_digest=pin.digest,
        capabilities=frozenset(details.capabilities),
    )


def load_model(client: JsonHttpClient, pin: ModelPin, settings: OllamaSetupSettings) -> LoadedModel:
    """Load without a prompt, then verify the applied context and memory placement."""

    reply = client.post(
        "api/generate",
        {
            "model": pin.model,
            "prompt": "",
            "stream": False,
            "keep_alive": settings.keep_alive_seconds,
            "options": {"num_ctx": settings.context_length},
        },
        settings.load_seconds,
    )
    result = LoadResult.model_validate(reply.body)

    if not result.done or result.model != pin.model:
        raise SetupError("Ollama did not confirm loading the exact configured model")

    reply = client.get("api/ps", settings.request_seconds)
    processes = Processes.model_validate(reply.body)

    for model in processes.models:
        if model.name == pin.model:
            if model.digest != pin.digest:
                raise SetupError("Loaded model digest differs from initialization")

            if model.context_length != settings.context_length:
                raise SetupError("Loaded context differs from requested setup context")

            return model

    raise SetupError("Ollama responded but the configured model is not loaded")


def unload_model(client: JsonHttpClient, pin: ModelPin, settings: OllamaSetupSettings) -> None:
    """Release a blocked setup's model without removing its persistent weights."""

    reply = client.post(
        "api/generate",
        {"model": pin.model, "prompt": "", "stream": False, "keep_alive": 0},
        settings.request_seconds,
    )
    result = LoadResult.model_validate(reply.body)

    if not result.done or result.model != pin.model:
        raise SetupError("Ollama did not confirm unloading the blocked setup model")
