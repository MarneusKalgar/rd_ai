"""One-shot financial recovery using the unchanged, frozen E03 application runner.

This operational entrypoint stays outside src so adding it cannot mutate the
preregistered application-source inventory. Its own manifest binds this tool,
tests, profile and Compose overlay. It grants no automatic replacement approval.
"""

import argparse
import fcntl
import json
import os
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import Field

from extraction_service.answering.cli import RUN_DIRECTORY, metadata
from extraction_service.answering.contract import AnswerJob
from extraction_service.answering.execution import AnswerRunner, Journal
from extraction_service.answering.protocol import Profile, select_phase, verified_jobs
from extraction_service.application.admission import ProviderAdmission
from extraction_service.application.composition import PreparedTarget
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetSnapshot
from extraction_service.execution.policy import SystemClock
from extraction_service.execution.types import ExecutionTarget
from extraction_service.inference.openrouter.adapter import OpenRouterAdapter
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.transport.client_setup import openrouter_client
from extraction_service.retrieval.core import MAX_ARTIFACT_BYTES, digest, read_confined
from extraction_service.runtime_types import Sha256, StrictModel

PROFILE = "config/retrieval/P03-E03-R01-profile.json"
MANIFEST = "config/retrieval/P03-E03-R01.json"
JOURNAL = f"{RUN_DIRECTORY}/pilot-recovery-R01.jsonl"
BINDINGS = (
    PROFILE,
    "tools/answer-recovery/recover.py",
    "tools/answer-recovery/test_recover.py",
    "compose.e03-recovery.yaml",
)


class Recovery(StrictModel):
    id: Literal["P03-E03-R01"]
    parent_manifest_sha256: Sha256
    parent_journal_sha256: Sha256
    tail_keys: list[str]
    total_pilot_exposure_usd: Decimal = Field(gt=0, le=10, allow_inf_nan=False)
    purpose: str


def parent_tail(
    events: list[dict[str, Any]],
    jobs: list[AnswerJob],
    expected_keys: list[str],
) -> tuple[list[AnswerJob], Decimal, set[str]]:
    """Select only unattempted allowance stops; never retry a physical observation."""

    if not events or events[0].get("event") != "start":
        raise ValueError("Missing original start record")
    end = events[-1]
    if end.get("event") != "complete" or end.get("stop_reason") != "phase_allowance_insufficient":
        raise ValueError("Only a completed financial stop is eligible")
    outcomes = [event for event in events if event["event"] == "outcome"]
    if events[0].get("jobs") != [job.model_dump(mode="json") for job in jobs] or [
        row["job"] for row in outcomes
    ] != [job.model_dump(mode="json") for job in jobs]:
        raise ValueError("Original job membership differs")
    physical = [row for row in events if row["event"] == "physical_result"]
    reserved = [row for row in events if row["event"] == "reserved"]
    if (
        [row["reservation_id"] for row in physical]
        != [row["reservation"]["id"] for row in reserved]
        or len({row["reservation_id"] for row in physical}) != len(physical)
        or end["physical_calls"] != len(physical)
    ):
        raise ValueError("Original physical accounting differs")
    sent_keys = {row["key"] for row in physical} | {row["key"] for row in reserved}
    tail = []
    for job, row in zip(jobs, outcomes, strict=True):
        if row["outcome"] == "not_attempted":
            if (
                row["reason"] != "phase_allowance_insufficient"
                or row["physical_calls"] != 0
                or job.key in sent_keys
                or job.skip_reason is not None
            ):
                raise ValueError("Recovery candidate was sent or is not a financial stop")
            tail.append(job)
    if [job.key for job in tail] != expected_keys:
        raise ValueError("Recovery must select the exact two unsent jobs")
    return tail, Decimal(end["accounted_usd"]), {row["reservation_id"] for row in physical}


def check_ledger(snapshot: BudgetSnapshot, ids: set[str], cost: Decimal, prefix: str) -> None:
    """Require settled original charges and reject another recovery invocation."""

    original = [entry for entry in snapshot.reservations if entry.id in ids]
    if (
        len(original) != len(ids)
        or any(not entry.resolved or entry.billed_usd is None for entry in original)
        or sum((entry.accounted_usd for entry in original), Decimal("0")) != cost
    ):
        raise ValueError("Original charges are missing, unknown or changed")
    if any(entry.request_key.startswith(prefix) for entry in snapshot.reservations):
        raise ValueError("Recovery already has paid reservations")


def prepare(
    root: Path, *, frozen: bool = True
) -> tuple[Recovery, Profile, list[AnswerJob], Decimal, set[str]]:
    """Verify both identities without changing any stopped-parent byte."""

    recovery = Recovery.model_validate_json(read_confined(root, PROFILE, 65536))
    profile, jobs, manifest = verified_jobs(root)
    if manifest != recovery.parent_manifest_sha256:
        raise ValueError("Original manifest identity differs")
    raw = read_confined(root, f"{RUN_DIRECTORY}/pilot.jsonl", MAX_ARTIFACT_BYTES)
    if digest(raw) != recovery.parent_journal_sha256:
        raise ValueError("Original journal identity differs")
    if frozen:
        expected = json.loads(read_confined(root, MANIFEST, 65536))
        actual = {path: digest(read_confined(root, path, MAX_ARTIFACT_BYTES)) for path in BINDINGS}
        if expected != {"id": recovery.id, "bindings": actual}:
            raise ValueError("Recovery bindings differ")
    events = [json.loads(line) for line in raw.splitlines()]
    tail, cost, ids = parent_tail(events, select_phase(jobs, profile, "pilot"), recovery.tail_keys)
    if cost >= recovery.total_pilot_exposure_usd:
        raise ValueError("Recovery exposure does not cover prior cost")
    return recovery, profile, tail, cost, ids


def run(root: Path) -> dict[str, Any]:
    """Make at most two approved calls through the existing metered AnswerRunner."""

    recovery, profile, jobs, prior_cost, ids = prepare(root)
    observed = metadata(root, profile)
    endpoint = OpenRouterEndpoint.model_validate_json(json.dumps(observed))
    settings = ApplicationSettings.load(root)
    settings.require_provider_credentials()
    policy = ExecutionConfig(
        request_timeout_seconds=profile.request_seconds,
        input_timeout_seconds=profile.request_seconds,
        transport_retries=0,
        api_budget_usd=10.0,
        matrix_reserve_usd=3.5,
    )
    ledger = BudgetLedger(root, policy)
    directory = root / RUN_DIRECTORY
    with (directory / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check_ledger(ledger.snapshot(), ids, prior_cost, f"{recovery.id}/")
        journal = Journal(root / JOURNAL)
        journal.append(
            dict(
                event="start",
                recovery=recovery.model_dump(mode="json"),
                parent_manifest=recovery.parent_manifest_sha256,
                parent_journal=recovery.parent_journal_sha256,
                metadata=observed,
                jobs=[job.model_dump(mode="json") for job in jobs],
                prior_pilot_cost_usd=str(prior_cost),
            )
        )
        with openrouter_client(settings) as client:
            adapter = OpenRouterAdapter(
                profile.model, endpoint, http_client=client, server_context=True
            )
            prepared = PreparedTarget(
                target=ExecutionTarget(adapter=adapter, endpoint=str(settings.openrouter_base_url)),
                admission=ProviderAdmission(profile.coverage),
                pricing=profile.coverage.pricing,
            )
            runner = AnswerRunner(
                prepared=prepared,
                ledger=ledger,
                journal=journal,
                clock=SystemClock(),
                allowance=recovery.total_pilot_exposure_usd,
                deadline_seconds=profile.phase_seconds,
                reported_provider=profile.reported_provider,
            )
            # Count the original paid observations in the revised exposure envelope.
            # They are not reserved or billed again.
            runner.accounted = prior_cost
            instructions = read_confined(root, profile.prompt, 65536).decode()
            outcomes = []
            for job in jobs:

                def revalidate() -> None:
                    prepare(root)

                result = runner.run(
                    job,
                    instructions=instructions,
                    sampling=profile.sampling,
                    timeout=profile.request_seconds,
                    request_key=f"{recovery.id}/{job.key}",
                    revalidate=revalidate,
                )
                outcomes.append(result)
                print(
                    json.dumps(
                        dict(key=job.key, outcome=result["outcome"], stop=runner.stop_reason)
                    ),
                    flush=True,
                )
            summary = dict(
                event="complete",
                physical_calls=runner.physical_calls,
                outcomes=dict(Counter(row["outcome"] for row in outcomes)),
                recovery_cost_usd=str(runner.accounted - prior_cost),
                total_pilot_cost_usd=str(runner.accounted),
                stop_reason=runner.stop_reason,
                semantic_review="unreviewed",
                remaining28_authorized=False,
            )
            journal.append(summary)
    return {**summary, "journal_sha256": digest((root / JOURNAL).read_bytes())}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "plan", "run", "export"))
    parser.add_argument("--allow-provider", action="store_true")
    parser.add_argument("--allow-server-context", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.command == "run":
        if not args.allow_provider or not args.allow_server_context:
            parser.error("Recovery requires separate paid/context approval")
        result = run(root)
    elif args.command == "export":
        prepare(root)
        with (root / RUN_DIRECTORY / "execution.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            raw = read_confined(root, JOURNAL, MAX_ARTIFACT_BYTES)
            path = Path("/app/e03-export/pilot-recovery-R01.jsonl")
            if path.exists() and path.read_bytes() != raw:
                raise ValueError("Recovery export differs; refusing overwrite")
            if not path.exists():
                with path.open("xb") as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
        result = dict(journal_sha256=digest(raw), generation_calls=0)
    else:
        recovery, profile, jobs, cost, _ = prepare(root, frozen=args.command != "freeze")
        if args.command == "freeze":
            manifest = dict(
                id=recovery.id,
                bindings={
                    path: digest(read_confined(root, path, MAX_ARTIFACT_BYTES)) for path in BINDINGS
                },
            )
            with (root / MANIFEST).open("x") as output:
                output.write(json.dumps(manifest, indent=2) + "\n")
        request = jobs[0].request(
            read_confined(root, profile.prompt, 65536).decode(),
            profile.sampling,
            profile.request_seconds,
        )
        reservation = profile.coverage.pricing.reserve_for(
            request, profile.coverage.pricing.dependency
        )
        result = dict(
            recovery=recovery.id,
            jobs=[job.key for job in jobs],
            physical_ceiling=len(jobs),
            original_cost_usd=str(cost),
            exposure_ceiling_usd=str(recovery.total_pilot_exposure_usd),
            next_reservation_usd=str(reservation),
            generation_calls=0,
            parent_still_stopped=True,
            remaining28_authorized=False,
        )
    print(json.dumps(result, indent=2))
    return 3 if result.get("stop_reason") is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
