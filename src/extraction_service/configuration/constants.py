"""Environment contract and service defaults for document intelligence."""

from typing import Final

ENVIRONMENT_PREFIX: Final[str] = "DI_"
PROVIDER_API_KEY_VARIABLE: Final[str] = "OPENROUTER_API_KEY"
ENVIRONMENT_FILENAME: Final[str] = ".env"
ENVIRONMENT_ENCODING: Final[str] = "utf-8"

DEFAULT_OPENROUTER_BASE_URL: Final[str] = "https://openrouter.ai/api/v1"
DEFAULT_OLLAMA_BASE_URL: Final[str] = "http://ollama:11434"
