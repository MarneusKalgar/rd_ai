"""Explicit E03 planning, metadata and separately approved pilot/continuation commands."""

import argparse
import fcntl
import json
import os
from collections import Counter
from pathlib import Path
from typing import Any

from extraction_service.answering.contract import AnswerJob
from extraction_service.answering.execution import AnswerRunner, Journal, Outcome
from extraction_service.answering.protocol import (
    Profile,
    build_jobs,
    freeze,
    load_profile,
    select_phase,
    verified_jobs,
)
from extraction_service.application.admission import ProviderAdmission
from extraction_service.application.composition import PreparedTarget
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.execution.policy import SystemClock
from extraction_service.execution.types import DependencyIdentity, ExecutionTarget
from extraction_service.inference.openrouter.adapter import OpenRouterAdapter
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.openrouter.metadata import verify_openrouter
from extraction_service.inference.transport.client_setup import openrouter_client
from extraction_service.inference.types import ModelIdentity
from extraction_service.record_types import ModelRuntime
from extraction_service.retrieval.core import MAX_ARTIFACT_BYTES, canonical, digest, read_confined

RUN_DIRECTORY = "results/answer-runs/P03-E03-v1"


def metadata(root: Path, profile: Profile) -> dict[str, Any]:
    """Public GET only; neither a provider key nor an inference request is required."""

    settings = ApplicationSettings.load(root)
    endpoint = verify_openrouter(profile.model, settings, timeout_seconds=10.0)
    profile.coverage.check_catalog(endpoint)
    if (
        endpoint.max_output_tokens is None
        or profile.sampling.max_output_tokens > endpoint.max_output_tokens
        or endpoint.provider_name != profile.reported_provider
    ):
        raise ValueError("E03 endpoint/output/provider changed")
    dependency = DependencyIdentity.from_model(
        str(settings.openrouter_base_url),
        # Client creation is outside metadata; only construct the adapter later.
        profile_identity(profile),
    )
    if dependency != profile.coverage.pricing.dependency:
        raise ValueError("E03 endpoint identity differs from frozen coverage")
    return endpoint.model_dump(mode="json")


def profile_identity(profile: Profile) -> ModelIdentity:
    """Build the requested paid identity without constructing an authenticated client."""

    return ModelIdentity(
        model_id=profile.model.id,
        model_name=profile.model.model,
        runtime=ModelRuntime.OPENROUTER,
        serving_provider=profile.model.serving_provider,
    )


def verify_pilot(root: Path, jobs: list[AnswerJob], expected_hash: str, manifest: str) -> set[str]:
    """A stopped, partial or altered pilot cannot unlock the remaining cases."""

    relative = f"{RUN_DIRECTORY}/pilot.jsonl"
    raw = read_confined(root, relative, MAX_ARTIFACT_BYTES)
    if digest(raw) != expected_hash:
        raise ValueError("Pilot receipt hash mismatch")
    events = [json.loads(line) for line in raw.splitlines()]
    header, summary = events[0], events[-1]
    if (
        header.get("event") != "start"
        or header.get("manifest") != manifest
        or header.get("phase") != "pilot"
        or summary.get("event") != "complete"
        or summary.get("stop_reason") is not None
    ):
        raise ValueError("Pilot integrity/operational stop blocks continuation")
    outcomes = [row for row in events if row["event"] == "outcome"]
    if [row["job"] for row in outcomes] != [job.model_dump(mode="json") for job in jobs] or any(
        row["outcome"] == Outcome.NOT_ATTEMPTED or row.get("stop_reason") is not None
        for row in outcomes
    ):
        raise ValueError("Pilot membership or completeness mismatch")
    physical = [row for row in events if row["event"] == "physical_result"]
    reserved = [row for row in events if row["event"] == "reserved"]
    if (
        summary["physical_calls"] != sum(row["physical_calls"] for row in outcomes)
        or len(physical) != len(reserved)
        or [row["reservation_id"] for row in physical]
        != [row["reservation"]["id"] for row in reserved]
    ):
        raise ValueError("Pilot physical accounting mismatch")
    if header.get("jobs") != [job.model_dump(mode="json") for job in jobs]:
        raise ValueError("Pilot scheduled membership mismatch")
    return {str(row["reservation_id"]) for row in physical}


def execute(root: Path, phase: str, pilot_hash: str | None) -> dict[str, Any]:
    """Run once with persistent reservations and no resume, retry, repair or fallback."""

    profile, jobs, manifest = verified_jobs(root)
    pilot_reservations: set[str] = set()
    if phase == "remaining":
        if pilot_hash is None:
            raise ValueError("Remaining phase requires an explicitly reviewed pilot hash")
        pilot_reservations = verify_pilot(
            root, select_phase(jobs, profile, "pilot"), pilot_hash, manifest
        )
    selected = select_phase(jobs, profile, phase)
    observed = metadata(root, profile)
    endpoint = OpenRouterEndpoint.model_validate_json(json.dumps(observed))
    settings = ApplicationSettings.load(root)
    settings.require_provider_credentials()
    # Read the existing policy; never initialize/reset/raise the cumulative ledger.
    policy = ExecutionConfig(
        request_timeout_seconds=profile.request_seconds,
        input_timeout_seconds=profile.request_seconds,
        transport_retries=0,
        api_budget_usd=10.0,
        matrix_reserve_usd=3.5,
    )
    ledger = BudgetLedger(root, policy)
    directory = root / RUN_DIRECTORY
    directory.mkdir(parents=True, exist_ok=True)
    with (directory / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        before = ledger.snapshot()
        settled = {
            entry.id
            for entry in before.reservations
            if entry.resolved and entry.billed_usd is not None
        }
        if not pilot_reservations <= settled:
            raise ValueError(
                "Pilot reservations are missing or unresolved in the cumulative ledger"
            )
        prefix = f"{profile.id}/{phase}/"
        if any(entry.request_key.startswith(prefix) for entry in before.reservations):
            raise ValueError(
                "Phase already has paid reservations; automatic replacement is forbidden"
            )
        # The fixed phase filename also prevents a second invocation under a fresh run ID.
        journal = Journal(directory / f"{phase}.jsonl")
        journal.append(
            dict(
                event="start",
                experiment=profile.id,
                phase=phase,
                manifest=manifest,
                profile=profile.model_dump(mode="json"),
                metadata=observed,
                jobs=[job.model_dump(mode="json") for job in selected],
                prior_accounted_usd=str(before.accounted_usd),
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
                allowance=profile.phase_allowance_usd,
                deadline_seconds=profile.phase_seconds,
                reported_provider=profile.reported_provider,
            )
            outcomes = []
            instructions = read_confined(root, profile.prompt, 65536).decode()
            for job in selected:

                def revalidate() -> None:
                    verified_jobs(root)

                outcome = runner.run(
                    job,
                    instructions=instructions,
                    sampling=profile.sampling,
                    timeout=profile.request_seconds,
                    request_key=f"{profile.id}/{phase}/{job.key}",
                    revalidate=revalidate,
                )
                outcomes.append(outcome)
                print(
                    json.dumps(
                        dict(key=job.key, outcome=outcome["outcome"], stop=runner.stop_reason)
                    ),
                    flush=True,
                )
            summary = dict(
                event="complete",
                phase=phase,
                jobs=len(selected),
                outcomes=dict(Counter(row["outcome"] for row in outcomes)),
                physical_calls=runner.physical_calls,
                accounted_usd=str(runner.accounted),
                stop_reason=runner.stop_reason,
                semantic_review="unreviewed",
            )
            journal.append(summary)
    return {**summary, "journal_sha256": digest(journal.path.read_bytes())}


def export_phase(root: Path, phase: str, output: Path = Path("/app/e03-export")) -> dict[str, Any]:
    """Copy bounded exact evidence to the dedicated export mount without model access."""

    profile, _, manifest = verified_jobs(root)
    directory = root / RUN_DIRECTORY
    with (directory / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        raw = read_confined(root, f"{RUN_DIRECTORY}/{phase}.jsonl", MAX_ARTIFACT_BYTES)
        events = [json.loads(line) for line in raw.splitlines()]
        if events[0].get("manifest") != manifest:
            raise ValueError("Export manifest differs from saved invocation")
        if not output.is_dir():
            raise ValueError("Dedicated E03 export mount is required")
        target = output / f"{phase}.jsonl"
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError("Existing export differs; refusing overwrite")
        else:
            with target.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
        return dict(
            experiment=profile.id,
            phase=phase,
            journal_sha256=digest(raw),
            complete=events[-1].get("event") == "complete",
            generation_calls=0,
        )


def main() -> int:
    """Keep public metadata and network-disabled planning distinct from inference."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("freeze", "plan", "metadata", "run", "export"))
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--phase", choices=("pilot", "remaining"), default="pilot")
    parser.add_argument("--pilot-sha256")
    parser.add_argument("--allow-provider", action="store_true")
    parser.add_argument("--allow-server-context", action="store_true")
    args = parser.parse_args()
    root = args.project_dir
    if args.command == "freeze":
        frozen = freeze(root)
        result = dict(
            experiment=frozen["id"],
            bindings=len(frozen["bindings"]),
            jobs_sha256=frozen["jobs_sha256"],
            generation_calls=0,
        )
    elif args.command == "metadata":
        result = metadata(root, load_profile(root))
    elif args.command == "plan":
        profile = load_profile(root)
        jobs = build_jobs(root, profile)
        selected = select_phase(jobs, profile, args.phase)
        result = dict(
            phase=args.phase,
            jobs=len(selected),
            deterministic_skips=sum(job.skip_reason is not None for job in selected),
            physical_ceiling=sum(job.skip_reason is None for job in selected),
            membership=[job.key for job in selected],
            phase_allowance_usd=str(profile.phase_allowance_usd),
            generation_calls=0,
            schema_sha256=digest(
                canonical(
                    jobs[0]
                    .request(
                        read_confined(root, profile.prompt, 65536).decode(),
                        profile.sampling,
                        profile.request_seconds,
                    )
                    .output_schema
                )
            ),
        )
    elif args.command == "export":
        result = export_phase(root, args.phase)
    else:
        if not args.allow_provider or not args.allow_server_context:
            parser.error("E03 requires separately approved --allow-provider --allow-server-context")
        result = execute(root, args.phase, args.pilot_sha256)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 3 if result.get("stop_reason") is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
