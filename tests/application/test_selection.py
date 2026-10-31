"""Nondefault variants must change both the request and the saved identity."""

import hashlib
import json
from typing import Any

import yaml

from extraction_service.application.persistence import reload_records

from .conftest import ControlledService


def test_explicit_nondefault_variants(service: ControlledService, gold: dict[str, Any]) -> None:
    path = service.project / "config/experiments.yaml"
    config = yaml.safe_load(path.read_text())
    instructions = "Distinct controlled test instructions."
    config["prompts"].append({"id": "controlled", "file": "prompts/controlled.txt"})
    config["sampling"].append(
        {"id": "alt", "temperature": 0.2, "top_p": 0.9, "max_output_tokens": 1000}
    )
    path.write_text(yaml.safe_dump(config))
    (service.project / "prompts/controlled.txt").write_text(instructions)
    service.responses = [json.dumps(gold)]

    result = service.invoke(
        "run",
        "--run-id",
        "variant",
        "--input",
        "B02-S003-PO01",
        "--prompt",
        "controlled",
        "--sampling",
        "alt",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    _, records = reload_records(service.project / "results/runs/variant")
    assert len(records) == 1
    assert records[0].prompt_id == "controlled"
    assert records[0].prompt_sha256 == hashlib.sha256(instructions.encode()).hexdigest()
    assert records[0].sampling_id == "alt"
    payloads = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload is not None and not payload.get("_debug_render_only")
    ]
    assert len(payloads) == 1
    assert payloads[0]["messages"][0]["content"].startswith(instructions)
    assert payloads[0]["options"]["temperature"] == 0.2
    assert payloads[0]["options"]["top_p"] == 0.9
    assert payloads[0]["options"]["num_predict"] == 1000
