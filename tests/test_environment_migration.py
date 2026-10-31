"""Exercise namespace migration at the actual Pydantic settings boundaries."""

from pathlib import Path
from typing import Any

import pytest
from pydantic_settings import BaseSettings

from extraction_service.archiving.storage import StorageSettings
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.runtime.configuration import OllamaSetupSettings

CASES = [
    (ApplicationSettings, "OLLAMA_BASE_URL", "http://localhost:12345", "ollama_base_url", {}),
    (OllamaSetupSettings, "SETUP_CONTEXT_LENGTH", "49152", "context_length", {}),
    (
        StorageSettings,
        "ARCHIVE_REGION",
        "migration-test",
        "region",
        {
            "endpoint_url": "http://localhost:3900",
            "bucket": "di-test",
            "access_key": "synthetic-access",
            "secret_key": "synthetic-secret",
        },
    ),
]


@pytest.mark.parametrize("settings_cls,suffix,value,field,kwargs", CASES)
@pytest.mark.parametrize("source", ["process", "dotenv"])
def test_new_names_load_nondefault_values(
    settings_cls: type[BaseSettings],
    suffix: str,
    value: str,
    field: str,
    kwargs: dict[str, Any],
    source: str,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    environment = tmp_path / ".env"

    if source == "process":
        monkeypatch.setenv(f"DI_{suffix}", value)
    else:
        environment.write_text(f"DI_{suffix}={value}\n")

    result = settings_cls(_env_file=environment, **kwargs)

    observed = str(getattr(result, field)).rstrip("/")
    assert observed == value


@pytest.mark.parametrize("settings_cls,suffix,value,field,kwargs", CASES)
@pytest.mark.parametrize("source", ["process", "dotenv"])
@pytest.mark.parametrize("conflict", [False, True])
def test_retired_or_conflicting_names_fail_without_values(
    settings_cls: type[BaseSettings],
    suffix: str,
    value: str,
    field: str,
    kwargs: dict[str, Any],
    source: str,
    conflict: bool,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    environment = tmp_path / ".env"
    private_value = "private-migration-marker"

    if source == "process":
        monkeypatch.setenv(f"HW01_{suffix}", private_value)
    else:
        environment.write_text(f"HW01_{suffix}={private_value}\n")

    if conflict:
        monkeypatch.setenv(f"DI_{suffix}", value)

    with pytest.raises(ValueError, match="Retired HW01_ settings") as failure:
        settings_cls(_env_file=environment, **kwargs)

    assert private_value not in str(failure.value)
