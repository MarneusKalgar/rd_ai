"""Export guards must be distinguishable from record reload validation."""

import json
from typing import Any

import pytest

from extraction_service.application.exporting import verify_export

from .conftest import ControlledService


@pytest.mark.parametrize("defect", ["manifest-bytes", "inventory"])
def test_export_own_integrity_checks(
    service: ControlledService, gold: dict[str, Any], defect: str
) -> None:
    service.responses = [json.dumps(gold)]
    result = service.invoke("run", "--run-id", "exported", "--input", "B02-S003-PO01")
    exported = service.invoke("export-run", "exported")
    assert result.returncode == exported.returncode == 0
    directory = service.project / "results/submission/exported"

    if defect == "manifest-bytes":
        path = directory / "manifest.json"
        path.write_bytes(path.read_bytes() + b" ")
        expected = "Export byte hash mismatch"
    else:
        (directory / "unexpected.json").write_text("{}")
        expected = "Export file inventory differs"

    with pytest.raises(ValueError, match=expected):
        verify_export(directory)
