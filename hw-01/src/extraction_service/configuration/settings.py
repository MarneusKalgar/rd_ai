"""Environment settings with explicit credential requirements and safe output."""

from enum import StrEnum
from pathlib import Path
from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from extraction_service.configuration.constants import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OPENROUTER_BASE_URL,
    ENVIRONMENT_ENCODING,
    ENVIRONMENT_FILENAME,
    ENVIRONMENT_PREFIX,
    PROVIDER_API_KEY_VARIABLE,
)


class OllamaMode(StrEnum):
    """Explicit local deployment selection; never infer it from connectivity."""

    DOCKER = "docker"
    NATIVE = "native"


class ApplicationSettings(BaseSettings):
    """Parse only service URLs and secrets from the environment or HW .env file.

    Environment strings intentionally become URL and secret objects here.
    Numeric experiment values are validated separately in strict models.
    """

    model_config = SettingsConfigDict(
        env_prefix=ENVIRONMENT_PREFIX,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    openrouter_api_key: SecretStr | None = Field(
        default=None,
        validation_alias=PROVIDER_API_KEY_VARIABLE,
        exclude=True,
        repr=False,
    )
    openrouter_base_url: AnyHttpUrl = AnyHttpUrl(DEFAULT_OPENROUTER_BASE_URL)
    ollama_base_url: AnyHttpUrl = AnyHttpUrl(DEFAULT_OLLAMA_BASE_URL)
    ollama_mode: OllamaMode = OllamaMode.DOCKER

    @field_validator("openrouter_base_url", "ollama_base_url")
    @classmethod
    def check_service_url(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        """Keep credentials, query strings and fragments out of service URLs."""

        if value.username or value.password or value.query or value.fragment:
            raise ValueError("Service URLs cannot include credentials, queries or fragments")

        return value

    @field_validator("openrouter_api_key")
    @classmethod
    def check_key(cls, value: SecretStr | None) -> SecretStr | None:
        """Reject a supplied blank credential without including it in errors."""

        if value is not None and not value.get_secret_value().strip():
            raise ValueError("Provider credential cannot be blank")

        return value

    @classmethod
    def load(cls, project_dir: Path) -> Self:
        """Read settings from process variables and the project's optional .env."""

        return cls(
            _env_file=project_dir / ENVIRONMENT_FILENAME,
            _env_file_encoding=ENVIRONMENT_ENCODING,
        )

    def require_provider_credentials(self) -> SecretStr:
        """Require a key only when starting provider execution, not preflight."""

        if self.openrouter_api_key is None:
            raise ValueError(f"Provider execution requires {PROVIDER_API_KEY_VARIABLE}")

        return self.openrouter_api_key
