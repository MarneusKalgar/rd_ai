"""Validated local setup controls, separate from experiment sampling and credentials."""

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


class CapacityScope(StrEnum):
    REPRESENTATIVE = "representative"
    EXHAUSTIVE = "exhaustive"


class ModelPin(StrictModel):
    """Reviewed registry identity; a mutable tag alone is insufficient."""

    model: NonEmptyText
    digest: Sha256
    server_version: NonEmptyText

    def check(self, config: ModelConfig) -> None:
        """Reject an unpinned selection before any download or model request."""

        if config.backend != "ollama" or config.model != self.model:
            raise SetupError("Selected local model differs from config/ollama-model.json")


class SetupSettings(BaseSettings):
    """Read explicit process variables, never credentials or a second dotenv file."""

    model_config = SettingsConfigDict(
        env_prefix="HW01_SETUP_", extra="forbid", frozen=True, hide_input_in_errors=True
    )

    image: Annotated[str, StringConstraints(pattern=r"^ollama/ollama@sha256:[a-f0-9]{64}$")]
    context_length: PositiveInt = 32768
    wait_seconds: PositiveFloat = 60.0
    poll_seconds: PositiveFloat = 1.0
    request_seconds: PositiveFloat = 5.0
    pull_seconds: PositiveFloat = 1800.0
    load_seconds: PositiveFloat = 300.0
    keep_alive_seconds: Annotated[int, Field(gt=0)] = 600
    capacity_seconds: PositiveFloat = 900.0
    measurement_seconds: PositiveFloat = 600.0


def load_model_pin(project_dir: Path) -> ModelPin:
    """Load the public, versioned model lock without consulting model catalogs."""

    return ModelPin.model_validate_json((project_dir / MODEL_PIN_FILE).read_text())
