"""Joint-receipt-aware continuation through the unchanged E03 AnswerRunner."""

import argparse
import fcntl
import json
import os
from collections import Counter
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

import recover
from pydantic import Field

from extraction_service.answering.cli import RUN_DIRECTORY, metadata, profile_identity
from extraction_service.answering.contract import AnswerJob, validate_answer
from extraction_service.answering.execution import AnswerRunner, Journal, Outcome
from extraction_service.answering.protocol import Profile, select_phase, verified_jobs
from extraction_service.application.admission import ProviderAdmission
from extraction_service.application.composition import PreparedTarget
from extraction_service.configuration.models import ExecutionConfig
from extraction_service.configuration.settings import ApplicationSettings
from extraction_service.execution.budget.ledger import BudgetLedger, BudgetSnapshot
from extraction_service.execution.policy import SystemClock
from extraction_service.execution.types import ExecutionTarget
from extraction_service.inference.errors import FailureEvidence
from extraction_service.inference.openrouter.adapter import OpenRouterAdapter
from extraction_service.inference.openrouter.capabilities import OpenRouterEndpoint
from extraction_service.inference.transport.client_setup import openrouter_client
from extraction_service.inference.types import GenerationRequest, ModelResponse
from extraction_service.retrieval.core import MAX_ARTIFACT_BYTES, canonical, digest, read_confined
from extraction_service.runtime_types import NonEmptyText, Sha256, StrictModel

PROFILE = "config/retrieval/P03-E03-C01-profile.json"
MANIFEST = "config/retrieval/P03-E03-C01.json"
JOINT = "pilot-joint-receipt.json"
JOURNAL = f"{RUN_DIRECTORY}/remaining-C01.jsonl"
BINDINGS = (
    PROFILE,
    JOINT,
    "tools/answer-continuation/continue_run.py",
    "tools/answer-continuation/test_continue.py",
    "compose.e03-continuation.yaml",
)


class Continuation(StrictModel):
    id: Literal["P03-E03-C01"]
    joint_receipt_sha256: Sha256
    recovery_journal_sha256: Sha256
    phase_allowance_usd: Decimal = Field(gt=0, le=10, allow_inf_nan=False)
    purpose: NonEmptyText


class JointReceipt(StrictModel):
    experiment: Literal["P03-E03-v1"]
    financial_addendum: Literal["P03-E03-R01"]
    parent_manifest_sha256: Sha256
    receipts: dict[str, Sha256]
    jobs: list[str]
    physical_calls: int
    deterministic_skips: int
    total_cost_usd: Decimal = Field(ge=0, allow_inf_nan=False)
    remaining28_authorized: Literal[False]
    original_continuation_command_eligible: Literal[False]
    review: NonEmptyText


def join_outcomes(
    original: list[dict[str, Any]],
    recovered: list[dict[str, Any]],
    pilot: list[AnswerJob],
) -> dict[str, dict[str, Any]]:
    """Fill only unsent slots without replacing any actual observation or skip."""

    expected = {job.key: job for job in pilot}
    if len(expected) != len(pilot):
        raise ValueError("Duplicate pilot identity")
    combined: dict[str, dict[str, Any]] = {}
    missing: set[str] = set()
    if [row["job"] for row in original] != [job.model_dump(mode="json") for job in pilot]:
        raise ValueError("Original pilot population differs")
    for row, job in zip(original, pilot, strict=True):
        if row["key"] != job.key:
            raise ValueError("Original pilot key differs")
        if row["outcome"] == Outcome.NOT_ATTEMPTED:
            if row["reason"] != "phase_allowance_insufficient" or row["physical_calls"] != 0:
                raise ValueError("Only unsent financial stops can be filled")
            missing.add(row["key"])
        else:
            combined[row["key"]] = row
    for row in recovered:
        key = row["key"]
        if key not in missing or key in combined or row["outcome"] == Outcome.NOT_ATTEMPTED:
            raise ValueError("Recovery duplicates a sent job or remains incomplete")
        if (
            row["job"] != expected[key].model_dump(mode="json")
            or row.get("stop_reason") is not None
        ):
            raise ValueError("Recovery settings or operational outcome differ")
        combined[key] = row
    if set(combined) != set(expected):
        raise ValueError("Joint pilot remains incomplete")
    for key, row in combined.items():
        job = expected[key]
        if job.skip_reason is not None:
            if (
                row["outcome"] != Outcome.SKIPPED
                or row["reason"] != job.skip_reason
                or row["physical_calls"] != 0
            ):
                raise ValueError("Deterministic skip accounting differs")
        elif row["physical_calls"] != 1 or row["outcome"] not in (
            Outcome.VALID,
            Outcome.INVALID,
            Outcome.RESPONSE_FAILURE,
            Outcome.TRANSPORT_FAILURE,
        ):
            raise ValueError("Non-skipped pilot job lacks physical evidence")
    return combined


def verify_joint(
    root: Path, config: Continuation, profile: Profile, pilot: list[AnswerJob]
) -> tuple[set[str], Decimal]:
    """Reconstruct the reviewed receipts, physical requests and known charges."""

    recovery, _, tail, _, _ = recover.prepare(root)
    raw_joint = read_confined(root, JOINT, 65536)
    if digest(raw_joint) != config.joint_receipt_sha256:
        raise ValueError("Joint receipt hash differs")
    joint = JointReceipt.model_validate_json(raw_joint)
    if (
        joint.jobs != [job.key for job in pilot]
        or joint.parent_manifest_sha256 != recovery.parent_manifest_sha256
    ):
        raise ValueError("Joint pilot identity differs")
    filenames = ("pilot.jsonl", "pilot-recovery-R01.jsonl")
    expected_hashes = (recovery.parent_journal_sha256, config.recovery_journal_sha256)
    journals = []
    for filename, expected_hash in zip(filenames, expected_hashes, strict=True):
        raw = read_confined(root, f"{RUN_DIRECTORY}/{filename}", MAX_ARTIFACT_BYTES)
        if digest(raw) != expected_hash or joint.receipts.get(filename) != expected_hash:
            raise ValueError("Pilot journal hash differs")
        journals.append([json.loads(line) for line in raw.splitlines()])
    original, recovered = journals
    if recovered[-1].get("event") != "complete" or recovered[-1].get("stop_reason") is not None:
        raise ValueError("Recovery has an operational stop")
    if recovered[0].get("recovery") != recovery.model_dump(mode="json") or recovered[0].get(
        "jobs"
    ) != [job.model_dump(mode="json") for job in tail]:
        raise ValueError("Recovery header identity differs")
    outcomes = [[row for row in events if row["event"] == "outcome"] for events in journals]
    combined = join_outcomes(outcomes[0], outcomes[1], pilot)
    expected = {job.key: job for job in pilot}
    ids: set[str] = set()
    cost = Decimal("0")
    instructions = read_confined(root, profile.prompt, 65536).decode()
    identity = profile_identity(profile)
    snapshot = BudgetSnapshot.model_validate_json(
        read_confined(root, "results/budget-ledger.json", MAX_ARTIFACT_BYTES)
    )
    ledger = {entry.id: entry for entry in snapshot.reservations}
    for events in journals:
        reserved = {row["key"]: row for row in events if row["event"] == "reserved"}
        physical = [row for row in events if row["event"] == "physical_result"]
        if len(physical) != len(reserved) or events[-1]["physical_calls"] != len(physical):
            raise ValueError("Physical population differs")
        for row in physical:
            key = row["key"]
            entry = reserved[key]
            reservation_id = row["reservation_id"]
            if (
                reservation_id in ids
                or reservation_id != entry["reservation"]["id"]
                or combined[key].get("reservation_id") != reservation_id
            ):
                raise ValueError("Physical reservation identity differs")
            ids.add(reservation_id)
            request = GenerationRequest.model_validate_json(json.dumps(entry["request"]))
            if request != expected[key].request(
                instructions, profile.sampling, request.timeout_seconds
            ):
                raise ValueError("Pilot generation controls differ")
            if (
                request.timeout_seconds > profile.request_seconds
                or ProviderAdmission(profile.coverage)
                .check(request, identity)
                .model_dump(mode="json")
                != entry["admission"]
            ):
                raise ValueError("Pilot admission differs")
            if "response" in row:
                response = ModelResponse.model_validate_json(json.dumps(row["response"]))
                if (
                    response.identity != identity
                    or response.reported_model != profile.model.model
                    or response.serving_provider != profile.reported_provider
                    or row["response"] != combined[key].get("response")
                ):
                    raise ValueError("Pilot response identity differs")
                billed = response.cost_usd
                if combined[key]["outcome"] == Outcome.VALID:
                    if response.raw_response is None:
                        raise ValueError("Missing valid answer text")
                    answer = validate_answer(response.raw_response, expected[key])
                    if answer.model_dump(mode="json") != combined[key]["answer"]:
                        raise ValueError("Pilot mechanical validation differs")
            else:
                failure = FailureEvidence.model_validate_json(json.dumps(row["failure"]))
                billed = failure.cost_usd
            if billed is None:
                raise ValueError("Unknown pilot charge blocks continuation")
            paid = ledger.get(reservation_id)
            if (
                paid is None
                or not paid.resolved
                or paid.billed_usd != Decimal(str(billed))
                or paid.reserved_usd
                != profile.coverage.pricing.reserve_for(
                    request, profile.coverage.pricing.dependency
                )
            ):
                raise ValueError("Pilot ledger entry differs")
            cost += Decimal(str(billed))
    if (
        len(ids) != joint.physical_calls
        or cost != joint.total_cost_usd
        or sum(job.skip_reason is not None for job in pilot) != joint.deterministic_skips
    ):
        raise ValueError("Joint cost or population differs")
    return ids, cost


def prepare(
    root: Path, *, frozen: bool = True
) -> tuple[Continuation, Profile, list[AnswerJob], set[str], Decimal]:
    """Admit only the disjoint fixed remaining28 population after joint verification."""

    config = Continuation.model_validate_json(read_confined(root, PROFILE, 65536))
    profile, all_jobs, _ = verified_jobs(root)
    pilot = select_phase(all_jobs, profile, "pilot")
    ids, cost = verify_joint(root, config, profile, pilot)
    jobs = select_phase(all_jobs, profile, "remaining")
    if (
        len(pilot) != 36
        or len(jobs) != 84
        or {job.key for job in pilot} & {job.key for job in jobs}
        or sum(job.skip_reason is None for job in jobs) != 77
    ):
        raise ValueError("Remaining population differs")
    if frozen:
        manifest = json.loads(read_confined(root, MANIFEST, 65536))
        if manifest != make_manifest(root, config, jobs):
            raise ValueError("Continuation bindings or jobs differ")
    return config, profile, jobs, ids, cost


def make_manifest(root: Path, config: Continuation, jobs: list[AnswerJob]) -> dict[str, Any]:
    return dict(
        id=config.id,
        bindings={path: digest(read_confined(root, path, MAX_ARTIFACT_BYTES)) for path in BINDINGS},
        jobs_sha256=digest(canonical([job.model_dump(mode="json") for job in jobs])),
    )


def run(root: Path) -> dict[str, Any]:
    """Own clients for one separately approved invocation; never resume or replace it."""

    config, profile, jobs, pilot_ids, pilot_cost = prepare(root)
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
    with (root / RUN_DIRECTORY / "execution.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        recover.check_ledger(ledger.snapshot(), pilot_ids, pilot_cost, f"{config.id}/")
        journal = Journal(root / JOURNAL)
        journal.append(
            dict(
                event="start",
                continuation=config.model_dump(mode="json"),
                metadata=observed,
                jobs=[job.model_dump(mode="json") for job in jobs],
                pilot_joint_receipt=config.joint_receipt_sha256,
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
                allowance=config.phase_allowance_usd,
                deadline_seconds=profile.phase_seconds,
                reported_provider=profile.reported_provider,
            )
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
                    request_key=f"{config.id}/{job.key}",
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
                jobs=len(jobs),
                physical_calls=runner.physical_calls,
                outcomes=dict(Counter(row["outcome"] for row in outcomes)),
                accounted_usd=str(runner.accounted),
                stop_reason=runner.stop_reason,
                semantic_review="unreviewed",
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
            parser.error("Continuation requires separate paid/context approval")
        result = run(root)
    elif args.command == "export":
        prepare(root)
        with (root / RUN_DIRECTORY / "execution.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            raw = read_confined(root, JOURNAL, MAX_ARTIFACT_BYTES)
            destination = Path("/app/e03-export/remaining-C01.jsonl")
            if destination.exists() and destination.read_bytes() != raw:
                raise ValueError("Existing continuation export differs")
            if not destination.exists():
                with destination.open("xb") as output:
                    output.write(raw)
                    output.flush()
                    os.fsync(output.fileno())
        result = dict(journal_sha256=digest(raw), generation_calls=0)
    else:
        config, profile, jobs, ids, cost = prepare(root, frozen=args.command != "freeze")
        snapshot = BudgetSnapshot.model_validate_json(
            read_confined(root, "results/budget-ledger.json", MAX_ARTIFACT_BYTES)
        )
        recover.check_ledger(snapshot, ids, cost, f"{config.id}/")
        if args.command == "freeze":
            with (root / MANIFEST).open("x") as output:
                output.write(json.dumps(make_manifest(root, config, jobs), indent=2) + "\n")
        result = dict(
            continuation=config.id,
            jobs=len(jobs),
            physical_ceiling=77,
            deterministic_skips=7,
            pilot_jobs_reused=36,
            allowance_usd=str(config.phase_allowance_usd),
            cumulative_remaining_usd=str(snapshot.budget_usd - snapshot.accounted_usd),
            generation_calls=0,
            membership=[job.key for job in jobs],
            model=profile.model.model,
            sampling=profile.sampling.model_dump(mode="json"),
        )
    print(json.dumps(result, indent=2))
    return 3 if result.get("stop_reason") is not None else 0


if __name__ == "__main__":
    raise SystemExit(main())
