import json
from typing import Any

import pytest
import yaml

from extraction_service import cli
from extraction_service.application.admission import LocalAdmission
from extraction_service.application.runner import run
from extraction_service.application.selection import RunOptions
from extraction_service.inference.transport.http import JsonHttpClient

from .conftest import ControlledService


def test_correction_through_composed_clients(
    service: ControlledService,
    gold: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service.responses = ["{}", json.dumps(gold)]

    for key, value in service.environment().items():
        monkeypatch.setenv(key, value)

    status, directory = run(
        service.project,
        RunOptions(run_id="direct-correction", input_ids=["B02-S003-PO01"]),
    )

    assert status == 0
    assert (directory / "manifest.json").exists()


def test_provider_aliases_share_one_authenticated_client(
    service: ControlledService,
    gold: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = service.project / "config/experiments.yaml"
    config = yaml.safe_load(config_path.read_text())
    config["models"].append({**config["models"][0], "id": "provider-alias"})
    config_path.write_text(yaml.safe_dump(config))
    service.coverage(["B02-S003-PO01"])
    coverage_path = service.project / "config/coverage.json"
    coverage = json.loads(coverage_path.read_bytes())
    coverage["provider-alias"] = coverage["provider"]
    coverage_path.write_text(json.dumps(coverage))
    initialized = service.invoke("budget-init", "--opening-spend", "0", "--evidence", "Test only")
    assert initialized.returncode == 0
    service.responses = [json.dumps(gold)] * 2
    original_post = JsonHttpClient.post
    original_close = JsonHttpClient.close
    generation_clients: list[JsonHttpClient] = []
    closed: list[JsonHttpClient] = []

    def post(
        client: JsonHttpClient, path: str, payload: dict[str, Any], timeout_seconds: float
    ) -> Any:
        if path == "chat/completions":
            generation_clients.append(client)

        return original_post(client, path, payload, timeout_seconds)

    def close(client: JsonHttpClient) -> None:
        closed.append(client)
        original_close(client)

    for key, value in service.environment().items():
        monkeypatch.setenv(key, value)

    monkeypatch.setattr(JsonHttpClient, "post", post)
    monkeypatch.setattr(JsonHttpClient, "close", close)
    options = RunOptions(
        run_id="shared-client",
        model_ids=["provider", "provider-alias"],
        input_ids=["B02-S003-PO01"],
        allow_provider=True,
        coverage_file="config/coverage.json",
    )

    status, _ = run(service.project, options)

    assert status == 0
    assert len(generation_clients) == 2
    assert generation_clients[0] is generation_clients[1]
    assert closed.count(generation_clients[0]) == 1
    assert len(closed) == len(set(closed)) == 3


def test_cleanup_failure_preserves_original_execution_error(
    service: ControlledService,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_close = JsonHttpClient.close
    closes = []

    def broken_close(client: JsonHttpClient) -> None:
        closes.append(client)
        original_close(client)
        raise OSError("secondary cleanup failure")

    def broken_check(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("primary execution failure")

    for key, value in service.environment().items():
        monkeypatch.setenv(key, value)

    monkeypatch.setattr(JsonHttpClient, "close", broken_close)
    monkeypatch.setattr(LocalAdmission, "check", broken_check)

    with pytest.raises(RuntimeError, match="primary execution failure"):
        run(service.project, RunOptions(run_id="primary-error", input_ids=["B02-S003-PO01"]))

    assert len(closes) == 1
    assert not service.generation_started.is_set()
    manifest = json.loads(
        (service.project / "results/runs/primary-error/manifest.json").read_bytes()
    )
    assert manifest["state"] == "interrupted"
    assert manifest["error"] == "RuntimeError"


def test_cli_redacts_unexpected_exception(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def broken_dispatch(arguments: Any) -> int:
        raise RuntimeError("controlled-sensitive-marker")

    monkeypatch.setattr(cli, "_dispatch", broken_dispatch)

    status = cli.main(["run"])

    output = capsys.readouterr().out
    assert status == 2
    assert "controlled-sensitive-marker" not in output
    assert json.loads(output) == {"unexpected_error": "RuntimeError"}
