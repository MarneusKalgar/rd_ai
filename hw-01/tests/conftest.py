import json
import shutil
from pathlib import Path
from typing import Final, cast

import pytest

from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.validation import JsonObject

PROJECT_DIR: Final[Path] = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def contract() -> ExtractionContract:
    manifest = json.loads((PROJECT_DIR / "data/manifest.json").read_text())
    schema_path = PROJECT_DIR / "schemas/purchase-order-extraction.v1.schema.json"

    return ExtractionContract.load(
        schema_path,
        expected_sha256=manifest["schemaSha256"],
    )


@pytest.fixture
def gold() -> JsonObject:
    path = PROJECT_DIR / "data/gold/B02-S003-PO01.json"
    parsed_gold = json.loads(path.read_text())

    return cast(JsonObject, parsed_gold)


def first_line(value: JsonObject) -> JsonObject:
    lines = value["lineItems"]

    assert isinstance(lines, list)
    assert isinstance(lines[0], dict)

    return lines[0]


@pytest.fixture
def project_copy(tmp_path: Path) -> Path:
    """Copy public HW artifacts for isolated configuration and tampering tests."""

    project = tmp_path / "project"
    for directory in ("schemas", "data", "config", "prompts"):
        shutil.copytree(PROJECT_DIR / directory, project / directory)

    return project
