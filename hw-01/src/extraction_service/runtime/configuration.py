"""Validated local setup controls, separate from experiment sampling and credentials."""

import re
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Final

from pydantic import Field, StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

from extraction_service.configuration.models import ModelConfig
from extraction_service.runtime.errors import SetupError
from extraction_service.runtime_types import (
    NonEmptyText,
    PositiveFloat,
    PositiveInt,
    Sha256,
    StrictModel,
)

MODEL_PIN_FILE: Final[str] = "config/ollama-model.json"
NATIVE_MODEL_PIN_FILE: Final[str] = "config/ollama-native.json"


class CapacityScope(StrEnum):
    REPRESENTATIVE = "representative"
    EXHAUSTIVE = "exhaustive"


class ServerVersionPolicy(StrEnum):
    EXACT = "exact"
    COMPATIBLE_PATCH = "compatible_patch"


def _release_parts(version: str) -> tuple[int, int, int] | None:
    """Accept stable numeric releases; prerelease/build suffixes require review."""

    if re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version) is None:
        return None

    major, minor, patch = version.split(".")

    return int(major), int(minor), int(patch)


class ModelPin(StrictModel):
    """Reviewed registry identity; a mutable tag alone is insufficient."""

    model: NonEmptyText
    digest: Sha256
    server_version: NonEmptyText
    server_version_policy: ServerVersionPolicy = ServerVersionPolicy.EXACT

    def check_server_version(self, version: str) -> None:
        """Apply an exact pin or a minimum patch within the reviewed release series."""

        if self.server_version_policy == ServerVersionPolicy.EXACT:
            if version != self.server_version:
                raise SetupError("Local server differs from the selected runtime version pin")

            return

        baseline = _release_parts(self.server_version)
        observed = _release_parts(version)

        if (
            baseline is None
            or observed is None
            or observed[:2] != baseline[:2]
            or observed[2] < baseline[2]
        ):
            raise SetupError("Local server is outside the reviewed runtime patch series")

    def check(self, config: ModelConfig) -> None:
        """Reject an unpinned selection before any download or model request."""

        if config.backend != "ollama" or config.model != self.model:
            raise SetupError("Selected local model differs from config/ollama-model.json")


class OllamaSetupSettings(BaseSettings):
    """Shared controls for either explicitly selected local server."""

    model_config = SettingsConfigDict(
        env_prefix="HW01_SETUP_", extra="forbid", frozen=True, hide_input_in_errors=True
    )

    context_length: PositiveInt = 32768
    wait_seconds: PositiveFloat = 60.0
    poll_seconds: PositiveFloat = 1.0
    request_seconds: PositiveFloat = 5.0
    pull_seconds: PositiveFloat = 1800.0
    load_seconds: PositiveFloat = 300.0
    keep_alive_seconds: Annotated[int, Field(gt=0)] = 600
    capacity_seconds: PositiveFloat = 900.0
    measurement_seconds: PositiveFloat = 600.0


class SetupSettings(OllamaSetupSettings):
    """Docker initialization additionally requires an immutable image identity."""

    image: Annotated[str, StringConstraints(pattern=r"^ollama/ollama@sha256:[a-f0-9]{64}$")]


def load_model_pin(project_dir: Path, *, native: bool = False) -> ModelPin:
    """Load the public, versioned model lock without consulting model catalogs."""

    filename = NATIVE_MODEL_PIN_FILE if native else MODEL_PIN_FILE

    pin = ModelPin.model_validate_json((project_dir / filename).read_text())

    if not native and pin.server_version_policy != ServerVersionPolicy.EXACT:
        raise SetupError("Docker runtime requires an exact server version policy")

    return pin
