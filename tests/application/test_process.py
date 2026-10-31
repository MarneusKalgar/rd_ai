"""Real CLI, real HTTP, real files; inference is supplied by a controlled service."""

import json
import signal
import subprocess
import sys
from typing import Any

import pytest
import yaml

from extraction_service.application.persistence import RunState, reload_records
from extraction_service.record_types import RunStatus

from .conftest import ControlledService

INPUT: str = "B02-S003-PO01"


def test_local_process_correction_and_export(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    service.responses = ["{}", json.dumps(gold)]

    result = service.invoke("run", "--run-id", "corrected", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/corrected")
    assert manifest.state == RunState.COMPLETE
    assert len(manifest.jobs) == len(records) == 1
    assert records[0].extraction == gold
    assert [attempt.outcome.value for attempt in records[0].attempts] == ["invalid", "valid"]
    assert [attempt.number for attempt in records[0].attempts] == [1, 2]
    chats = [payload for path, payload, _ in service.requests if path == "/api/chat"]
    assert len(chats) == 4
    assert [bool(payload and payload.get("_debug_render_only")) for payload in chats] == [
        True,
        False,
        True,
        False,
    ]
    initial, correction = chats[1], chats[3]
    assert initial is not None and correction is not None
    assert initial["format"] == correction["format"]
    assert initial["options"]["num_ctx"] == 32768
    assert initial["truncate"] is False and initial["shift"] is False
    assert "{}" in correction["messages"][0]["content"]
    assert initial["messages"][1] == correction["messages"][1]
    assert all(authorization is None for _, _, authorization in service.requests)
    assert not (service.project / "results/budget-ledger.json").exists()
    checkpoint = next((service.project / "results/runs/corrected/checkpoints").glob("*.json"))
    progress = json.loads(checkpoint.read_bytes())
    assert len(progress["admissions"]) == len(progress["attempts"]) == 2

    exported = service.invoke("export-run", "corrected")
    verified = service.invoke("verify-export", "corrected")
    repeated = service.invoke("export-run", "corrected")

    assert exported.returncode == verified.returncode == 0
    assert repeated.returncode == 2
    assert json.loads(verified.stdout)["verified_records"] == 1
    destination = service.project / "results/submission/corrected"
    record_path = next((destination / "records").glob("*.json"))
    record_path.write_bytes(record_path.read_bytes() + b" ")

    corrupted = service.invoke("verify-export", "corrected")

    assert corrupted.returncode == 2
    assert "ValueError" in corrupted.stdout


def test_failed_extraction_is_completed_work(service: ControlledService) -> None:
    service.responses = ["{}", "{}"]

    result = service.invoke("run", "--run-id", "invalid", "--input", INPUT)

    assert result.returncode == 1, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/invalid")
    assert manifest.state == RunState.COMPLETE
    assert manifest.summary is not None and manifest.summary.failed == 1
    assert records[0].status == RunStatus.FAILED
    assert records[0].attempts[-1].raw_response == "{}"
    assert records[0].attempts[-1].issues


@pytest.mark.parametrize(
    "defect", ["unknown-input", "duplicate-input", "provider-unapproved", "existing-run"]
)
def test_bad_selections_do_not_generate(service: ControlledService, defect: str) -> None:
    arguments = ["run", "--run-id", "bad", "--input", INPUT]

    if defect == "unknown-input":
        arguments[-1] = "not-an-input"
    elif defect == "duplicate-input":
        arguments.extend(["--input", INPUT])
    elif defect == "provider-unapproved":
        arguments.extend(["--model", "provider"])
    else:
        (service.project / "results/runs/bad").mkdir(parents=True)

    result = service.invoke(*arguments)

    assert result.returncode == 2
    assert not service.generation_started.is_set()


def test_context_rejection_is_not_an_inference_attempt(service: ControlledService) -> None:
    service.rendered_override = "a" * 32768

    result = service.invoke("run", "--run-id", "too-large", "--input", INPUT)

    assert result.returncode == 3, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/too-large")
    assert manifest.state == RunState.INCOMPLETE
    assert records[0].status == RunStatus.NOT_ATTEMPTED
    assert records[0].reason == "context_capacity_exceeded"
    assert records[0].attempts == []
    assert not service.generation_started.is_set()


def test_provider_process_and_cumulative_budget(
    service: ControlledService, gold: dict[str, Any]
) -> None:
    service.coverage([INPUT])
    service.responses = [json.dumps(gold), json.dumps(gold)]
    arguments = [
        "run",
        "--model",
        "provider",
        "--input",
        INPUT,
        "--allow-provider",
        "--coverage",
        "config/coverage.json",
    ]
    initialized = service.invoke(
        "budget-init", "--opening-spend", "0.2", "--evidence", "Controlled test prior spend"
    )
    overwritten = service.invoke("budget-init", "--opening-spend", "0", "--evidence", "Must refuse")

    first = service.invoke(*arguments, "--run-id", "paid-first")
    second = service.invoke(*arguments, "--run-id", "paid-second", "--stage", "smoke")
    budget = service.invoke("budget-show")

    assert initialized.returncode == 0
    assert overwritten.returncode == 2
    assert first.returncode == second.returncode == budget.returncode == 0, (
        first.stdout + second.stdout
    )
    assert json.loads(budget.stdout)["accounted_usd"] == "0.20002"
    assert json.loads(budget.stdout)["reservations"] == 2
    _, records = reload_records(service.project / "results/runs/paid-second")
    assert records[0].stage.value == "smoke"
    assert records[0].extraction == gold
    assert not any(
        path.startswith("/api/") and not path.startswith("/api/v1/")
        for path, _, _ in service.requests
    )
    completions = [
        (payload, authorization)
        for path, payload, authorization in service.requests
        if path.endswith("/chat/completions")
    ]
    assert len(completions) == 2
    assert all(authorization == "Bearer controlled-test-key" for _, authorization in completions)


@pytest.mark.parametrize("has_coverage", [True, False])
def test_missing_budget_or_pricing_blocks_paid_http(
    service: ControlledService, has_coverage: bool
) -> None:
    arguments = [
        "run",
        "--run-id",
        "no-budget",
        "--model",
        "provider",
        "--input",
        INPUT,
        "--allow-provider",
    ]

    if has_coverage:
        service.coverage([INPUT])
        arguments.extend(["--coverage", "config/coverage.json"])

    result = service.invoke(*arguments)

    assert result.returncode == 3, result.stdout + result.stderr
    _, records = reload_records(service.project / "results/runs/no-budget")
    expected = "budget_unavailable" if has_coverage else "unsafe_pricing"
    assert records[0].reason == expected
    assert records[0].attempts == []
    assert not service.generation_started.is_set()


@pytest.mark.parametrize("paid", [False, True])
def test_signal_retains_inflight_checkpoint(service: ControlledService, paid: bool) -> None:
    service.block_generation = True
    command = [
        sys.executable,
        "-m",
        "extraction_service",
        "--project-dir",
        str(service.project),
        "run",
        "--run-id",
        "interrupted",
        "--input",
        INPUT,
    ]

    if paid:
        service.coverage([INPUT])
        initialized = service.invoke(
            "budget-init", "--opening-spend", "0.1", "--evidence", "Test prior spending"
        )
        assert initialized.returncode == 0
        command.extend(
            ["--model", "provider", "--allow-provider", "--coverage", "config/coverage.json"]
        )
    process = subprocess.Popen(
        command,
        env=service.environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        assert service.generation_started.wait(10)
        process.send_signal(signal.SIGTERM)
        stdout, stderr = process.communicate(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()

    assert process.returncode == 130, stdout + stderr
    manifest, records = reload_records(service.project / "results/runs/interrupted")
    assert manifest.state == RunState.INTERRUPTED
    assert records == []
    checkpoints = list((service.project / "results/runs/interrupted/checkpoints").glob("*.json"))
    assert len(checkpoints) == 1
    progress = json.loads(checkpoints[0].read_bytes())
    assert len(progress["admissions"]) == 1
    assert progress["attempts"] == []

    if paid:
        ledger = json.loads((service.project / "results/budget-ledger.json").read_bytes())
        assert len(ledger["reservations"]) == 1
        reservation = ledger["reservations"][0]
        assert reservation["resolved"] is False
        assert reservation["billed_usd"] is None
        assert reservation["reserved_usd"] == "0.0040960"


def test_offline_plan_never_contacts_services(service: ControlledService) -> None:
    result = service.invoke("plan-run", "--model", "provider", "--input", INPUT)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["primary_requests"] == 1
    assert report["maximum_physical_requests"] == 4
    assert report["maximum_api_usd_by_model"] == {"provider": None}
    assert report["accounted_prior_usd"] is None
    assert service.requests == []
    assert not (service.project / "results/budget-ledger.json").exists()


def test_dependency_stop_survives_application_input_boundaries(service: ControlledService) -> None:
    service.generation_status = 503
    path = service.project / "config/experiments.yaml"
    config = yaml.safe_load(path.read_text())
    config["models"].append({**config["models"][1], "id": "local-alias"})
    config["prompts"].append({"id": "controlled", "file": "prompts/controlled.txt"})
    path.write_text(yaml.safe_dump(config))
    (service.project / "prompts/controlled.txt").write_text("Distinct controlled variant.")
    arguments = [
        "run",
        "--run-id",
        "shared-stop",
        "--model",
        "local",
        "--model",
        "local-alias",
        "--input",
        INPUT,
        "--input",
        "B02-S006-PO01",
        "--prompt",
        "v1",
        "--prompt",
        "controlled",
    ]

    result = service.invoke(*arguments)

    assert result.returncode == 3, result.stdout + result.stderr
    manifest, records = reload_records(service.project / "results/runs/shared-stop")
    assert [record.status.value for record in records] == ["failed"] * 3 + ["not_attempted"] * 5
    assert len(manifest.jobs) == len(records) == 8
    assert {record.prompt_id for record in records} == {"v1", "controlled"}
    assert {record.model_id for record in records} == {"local", "local-alias"}
    assert all(record.attempts == [] for record in records[3:])
    assert manifest.summary is not None and not manifest.summary.comparison_complete
    generations = [
        payload
        for path, payload, _ in service.requests
        if path == "/api/chat" and payload is not None and not payload.get("_debug_render_only")
    ]
    assert len(generations) == 6
