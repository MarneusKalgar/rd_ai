"""Runtime compatibility never relaxes Docker pins or crosses native release series."""

import json
from pathlib import Path

import pytest

from extraction_service.runtime.configuration import ModelPin, load_model_pin
from extraction_service.runtime.errors import SetupError


@pytest.mark.parametrize("version", ["0.40.7", "0.40.8", "0.40.12"])
def test_native_accepts_stable_patches(project_copy: Path, version: str) -> None:
    pin = load_model_pin(project_copy, native=True)

    pin.check_server_version(version)


@pytest.mark.parametrize(
    "version", ["0.40.6", "0.39.99", "0.41.0", "1.0.0", "0.40.8-rc1", "unknown", "0.40"]
)
def test_native_rejects_unreviewed_releases(project_copy: Path, version: str) -> None:
    pin = load_model_pin(project_copy, native=True)

    with pytest.raises(SetupError, match="outside the reviewed runtime patch series"):
        pin.check_server_version(version)


def test_docker_keeps_exact_version_even_for_patch_updates(pin: ModelPin) -> None:
    pin.check_server_version("0.40.6")

    with pytest.raises(SetupError, match="differs from the selected runtime version pin"):
        pin.check_server_version("0.40.7")


def test_docker_rejects_relaxed_policy_in_configuration(project_copy: Path) -> None:
    path = project_copy / "config/ollama-model.json"
    content = json.loads(path.read_text())
    content["server_version_policy"] = "compatible_patch"
    path.write_text(json.dumps(content))

    with pytest.raises(SetupError, match="Docker runtime requires an exact"):
        load_model_pin(project_copy)
