"""Explicit execution, accounting and export commands; no inference on import."""

import argparse
import json
import signal
import sys
from collections.abc import Generator
from contextlib import contextmanager
from decimal import Decimal
from types import FrameType
from typing import Final

from extraction_service.application.exporting import export_run, verify_export
from extraction_service.application.planning import describe_run
from extraction_service.application.runner import run
from extraction_service.application.selection import RunOptions
from extraction_service.artifacts import artifact_path
from extraction_service.configuration.loading import load_experiment
from extraction_service.diagnostics.reporting import diagnose_runs
from extraction_service.evaluation.reporting import evaluate_runs
from extraction_service.execution.budget.ledger import BudgetLedger
from extraction_service.exit_status import ExitStatus
from extraction_service.preflight import DEFAULT_EXPERIMENT_FILE
from extraction_service.record_types import ExecutionStage
from extraction_service.records import RunRecord

COMMANDS: Final[frozenset[str]] = frozenset(
    {
        "run",
        "smoke",
        "plan-run",
        "budget-init",
        "budget-show",
        "budget-raise",
        "export-run",
        "verify-export",
        "evaluate",
        "diagnose-rows",
    }
)
SMOKE_INPUTS: Final[tuple[str, ...]] = ("B02-S030-PO01", "B02-S026-PO01", "B02-S008-PO01")


def add_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Attach application commands to the existing project CLI."""

    for name in ("run", "smoke", "plan-run"):
        parser = commands.add_parser(
            name,
            help="Execute selected extractions" if name != "plan-run" else "Describe work offline",
        )
        parser.add_argument("--config", default=DEFAULT_EXPERIMENT_FILE)
        parser.add_argument("--run-id")
        parser.add_argument("--model", action="append", default=[])
        parser.add_argument("--input", action="append", default=[])
        parser.add_argument("--prompt", action="append", default=[])
        parser.add_argument("--sampling", action="append", default=[])
        parser.add_argument(
            "--stage", choices=[stage.value for stage in ExecutionStage], default="matrix"
        )
        parser.add_argument(
            "--coverage", help="Project-relative verified provider token/pricing evidence"
        )
        parser.add_argument(
            "--allow-provider",
            action="store_true",
            help="Use only after human approval of this invocation",
        )
        parser.add_argument(
            "--allow-server-context",
            action="store_true",
            help="Approved stage coverage: accept provider-enforced context limits",
        )

    for name in ("budget-init", "budget-show", "budget-raise"):
        parser = commands.add_parser(name, help="Explicit cumulative budget administration")
        parser.add_argument("--config", default=DEFAULT_EXPERIMENT_FILE)

        if name == "budget-init":
            parser.add_argument("--opening-spend", required=True, type=Decimal)
            parser.add_argument("--evidence", required=True)

        if name == "budget-raise":
            parser.add_argument("--expected-budget", required=True, type=Decimal)
            parser.add_argument("--evidence", required=True)

    for name in ("export-run", "verify-export"):
        parser = commands.add_parser(name, help="Copy/check saved evidence without inference")
        parser.add_argument("run_id")

    evaluation = commands.add_parser("evaluate", help="Score saved terminal runs offline")
    evaluation.add_argument("run_ids", nargs="+")
    evaluation.add_argument("--allow-budget-revision", action="store_true")
    evaluation.add_argument("--source-dir", default="results/runs")

    diagnostic = commands.add_parser("diagnose-rows", help="Inspect saved row selection offline")
    diagnostic.add_argument("run_ids", nargs="+")
    diagnostic.add_argument("--source", choices=("runs", "submission"), default="submission")


def _options(args: argparse.Namespace) -> RunOptions:
    values = {
        "model_ids": args.model,
        "input_ids": args.input or (list(SMOKE_INPUTS) if args.command == "smoke" else []),
        "prompt_ids": args.prompt,
        "sampling_ids": args.sampling,
        "stage": ExecutionStage.SMOKE if args.command == "smoke" else ExecutionStage(args.stage),
        "allow_provider": args.allow_provider,
        "allow_server_context": args.allow_server_context,
        "coverage_file": args.coverage,
    }

    if args.run_id is not None:
        values["run_id"] = args.run_id

    return RunOptions.model_validate(values)


@contextmanager
def interruption_boundary() -> Generator[None]:
    """Allow the runner to checkpoint SIGTERM using its ordinary unwind path."""

    def terminate(signum: int, frame: FrameType | None) -> None:
        raise KeyboardInterrupt

    previous = signal.signal(signal.SIGTERM, terminate)

    try:
        yield
    finally:
        signal.signal(signal.SIGTERM, previous)


def dispatch(args: argparse.Namespace) -> int:
    """Execute one explicit command; outer CLI owns safe error reporting."""

    project_dir = args.project_dir

    if args.command == "diagnose-rows":
        report = diagnose_runs(project_dir, args.run_ids, source=args.source)
        print(json.dumps(report, ensure_ascii=False, indent=2))

        return ExitStatus.SUCCESS

    if args.command == "evaluate":
        report = evaluate_runs(
            project_dir,
            args.run_ids,
            allow_budget_revision=args.allow_budget_revision,
            source_dir=args.source_dir,
        )
        print(json.dumps(report, indent=2))

        return ExitStatus.SUCCESS

    if args.command in ("run", "smoke", "plan-run"):
        options = _options(args)

        if args.command == "plan-run":
            report = describe_run(project_dir, options, args.config)
            print(json.dumps(report, indent=2))

            return ExitStatus.SUCCESS

        with interruption_boundary():
            status, directory = run(project_dir, options, args.config, on_record=_progress)

        print(json.dumps({"exit_status": status, "run_directory": str(directory)}))

        return status

    if args.command in ("budget-init", "budget-show", "budget-raise"):
        config = load_experiment(artifact_path(project_dir, args.config))
        ledger = BudgetLedger(project_dir, config.execution)

        if args.command == "budget-init":
            ledger.initialize(opening_spend_usd=args.opening_spend, evidence=args.evidence)

        if args.command == "budget-raise":
            ledger.raise_cap(expected_budget_usd=args.expected_budget, evidence=args.evidence)

        snapshot = ledger.snapshot()
        print(
            json.dumps(
                {
                    "accounted_usd": str(snapshot.accounted_usd),
                    "budget_usd": str(snapshot.budget_usd),
                    "protected_matrix_usd": str(snapshot.protected_matrix_usd),
                    "reservations": len(snapshot.reservations),
                    "policy_revisions": [
                        revision.model_dump(mode="json") for revision in snapshot.policy_revisions
                    ],
                }
            )
        )

        return ExitStatus.SUCCESS

    RunOptions(run_id=args.run_id)
    destination = project_dir / "results/submission" / args.run_id

    if args.command == "export-run":
        source = project_dir / "results/runs" / args.run_id
        report = export_run(source, destination)
    else:
        report = verify_export(destination)

    print(json.dumps(report))

    return ExitStatus.SUCCESS


def _progress(record: RunRecord) -> None:
    """Expose completed-input progress without printing raw model responses."""

    print(
        json.dumps(
            {
                "event": "input_saved",
                "run_id": record.run_id,
                "input_id": record.input_id,
                "model_id": record.model_id,
                "status": record.status.value,
                "attempts": len(record.attempts),
                "duration_ms": record.duration_ms,
            }
        ),
        file=sys.stderr,
        flush=True,
    )
