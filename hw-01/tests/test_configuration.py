import os
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from conftest import PROJECT_DIR
from pydantic import ValidationError

from extraction_service.configuration.loading import ConfigurationError, load_experiment
from extraction_service.configuration.models import ExperimentConfig
from extraction_service.configuration.settings import ApplicationSettings


@pytest.fixture(autouse=True)
def isolated_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in list(os.environ):
        if name.startswith("HW01_") or name == "OPENROUTER_API_KEY":
            monkeypatch.delenv(name)


@pytest.fixture
def configuration() -> dict[str, Any]:
    raw = (PROJECT_DIR / "config/experiments.yaml").read_text()

    return dict(yaml.safe_load(raw))


def test_real_configuration_preserves_explicit_parameters() -> None:
    result = load_experiment(PROJECT_DIR / "config/experiments.yaml")

    assert result.selection.model_id == "local"
    assert result.sampling[0].temperature == 0.0
    assert result.sampling[0].max_output_tokens == 4096
    assert result.execution.transport_retries == 1
    assert result.execution.api_budget_usd == 4.5


@pytest.mark.parametrize(
    "field,value",
    [
        ("request_timeout_seconds", 0),
        ("request_timeout_seconds", "120"),
        ("request_timeout_seconds", True),
        ("request_timeout_seconds", float("inf")),
        ("input_timeout_seconds", 1.0),
        ("transport_retries", -1),
        ("transport_retries", 6),
        ("transport_retries", 1.5),
        ("api_budget_usd", 0.0),
        ("api_budget_usd", 5.0),
        ("api_budget_usd", float("nan")),
        ("dependency_failure_limit", 0),
        ("dependency_failure_limit", -1),
        ("dependency_failure_limit", True),
        ("dependency_failure_limit", "3"),
        ("dependency_failure_limit", 1.5),
        ("matrix_reserve_usd", -1.0),
        ("matrix_reserve_usd", 4.5),
        ("matrix_reserve_usd", "3.5"),
        ("backoff_initial_seconds", 0.0),
        ("backoff_initial_seconds", 31.0),
        ("backoff_max_seconds", float("nan")),
        ("typo", 1),
    ],
)
def test_execution_bounds_reject_malformed_configuration(
    configuration: dict[str, Any],
    field: str,
    value: object,
) -> None:
    baseline = ExperimentConfig.model_validate(configuration)
    configuration["execution"][field] = value

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(configuration)

    assert baseline.execution.request_timeout_seconds == 120.0


@pytest.mark.parametrize(
    "field,value",
    [
        ("temperature", -0.1),
        ("temperature", 2.1),
        ("temperature", "0"),
        ("top_p", 0.0),
        ("top_p", 1.1),
        ("max_output_tokens", 0),
        ("max_output_tokens", True),
        ("seed", 1),
    ],
)
def test_sampling_values_are_strict_and_unknown_parameters_are_rejected(
    configuration: dict[str, Any],
    field: str,
    value: object,
) -> None:
    configuration["sampling"][0][field] = value

    with pytest.raises(ValidationError):
        ExperimentConfig.model_validate(configuration)


@pytest.mark.parametrize("group", ["models", "prompts", "sampling"])
def test_duplicate_variant_ids_are_not_silently_overwritten(
    configuration: dict[str, Any], group: str
) -> None:
    configuration[group].append(deepcopy(configuration[group][0]))

    with pytest.raises(ValidationError, match="Duplicate"):
        ExperimentConfig.model_validate(configuration)


@pytest.mark.parametrize("field", ["model_id", "prompt_id", "sampling_id"])
def test_unknown_selection_ids_fail_before_execution(
    configuration: dict[str, Any], field: str
) -> None:
    configuration["selection"][field] = "missing"

    with pytest.raises(ValidationError, match="not configured"):
        ExperimentConfig.model_validate(configuration)


@pytest.mark.parametrize(
    "text",
    [
        "version: experiment-v1\nversion: overwritten\n",
        "nested:\n  temperature: 0.0\n  temperature: 1.0\n",
        "!!python/object/apply:builtins.print ['unexpected']",
        "version: [",
    ],
)
def test_unsafe_duplicate_or_malformed_yaml_is_rejected(tmp_path: Path, text: str) -> None:
    path = tmp_path / "experiment.yaml"
    path.write_text(text)

    with pytest.raises(ConfigurationError):
        load_experiment(path)


def test_settings_need_no_key_offline_but_require_one_for_provider_execution(
    tmp_path: Path,
) -> None:
    settings = ApplicationSettings.load(tmp_path)

    assert settings.openrouter_api_key is None
    assert str(settings.ollama_base_url) == "http://ollama:11434/"

    with pytest.raises(ValueError, match="requires OPENROUTER_API_KEY"):
        settings.require_provider_credentials()


def test_environment_overrides_dotenv_and_secret_is_not_serialized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".env").write_text(
        "OPENROUTER_API_KEY=dotenv-private-value\nHW01_OLLAMA_BASE_URL=http://host.docker.internal:11434\n"
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "environment-private-value")

    settings = ApplicationSettings.load(tmp_path)
    key = settings.require_provider_credentials()

    assert key.get_secret_value() == "environment-private-value"
    assert str(settings.ollama_base_url) == "http://host.docker.internal:11434/"
    assert "private-value" not in repr(settings)
    assert "private-value" not in settings.model_dump_json()
    assert "openrouter_api_key" not in settings.model_dump()


@pytest.mark.parametrize(
    "entry",
    [
        "UNKNOWN_SECRET=private-marker",
        "HW01_OLLAMA_BASE_URL=ftp://private-marker",
        "HW01_OLLAMA_BASE_URL=http://private-marker:password@localhost:11434",
        "OPENROUTER_API_KEY=   ",
    ],
)
def test_settings_errors_reject_bad_values_without_disclosing_input(
    tmp_path: Path, entry: str
) -> None:
    (tmp_path / ".env").write_text(entry)

    with pytest.raises(ValidationError) as captured:
        ApplicationSettings.load(tmp_path)

    assert "private-marker" not in str(captured.value)


@pytest.mark.parametrize("field", ["openrouter_base_url", "ollama_base_url"])
@pytest.mark.parametrize("suffix", ["?token=private-url-marker", "#private-url-marker"])
def test_service_urls_reject_queries_and_fragments(tmp_path: Path, field: str, suffix: str) -> None:
    environment_name = f"HW01_{field.upper()}"
    environment_file = tmp_path / ".env"
    base_url = "http://localhost:11434/"
    environment_file.write_text(f"{environment_name}={base_url}")

    baseline = ApplicationSettings.load(tmp_path)

    assert str(getattr(baseline, field)) == base_url

    environment_file.write_text(f"{environment_name}={base_url}{suffix}")

    with pytest.raises(ValidationError, match="queries or fragments") as captured:
        ApplicationSettings.load(tmp_path)

    errors = captured.value.errors(include_input=False)

    assert errors[0]["loc"] == (field,)
    assert errors[0]["type"] == "value_error"
    assert "private-url-marker" not in str(captured.value)
