import json
from pathlib import Path
from typing import cast

import pytest

from hw01.extraction import ExtractionContract
from hw01.extraction.validation import JsonObject

PROJECT_DIR = Path(__file__).resolve().parents[1]


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
