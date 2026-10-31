"""Explicit native correction, offline verification and public export commands."""

import argparse
import json
from pathlib import Path

from extraction_service.application.selection import RunOptions
from extraction_service.corrections.application import run_corrections
from extraction_service.corrections.evaluation import evaluate_corrections
from extraction_service.corrections.storage import export_corrections, verify_corrections
from extraction_service.corrections.types import CorrectionCase


def _progress(input_id: str, result: CorrectionCase) -> None:
    print(
        json.dumps(
            {
                "input_id": input_id,
                "decision": result.decision.value,
                "targets": len(result.targets),
                "new_requests": int(result.attempt is not None),
                "duration_ms": result.duration_ms,
            }
        ),
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--base-run-id", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--config", default="config/gemma-scoped-roles.yaml")
    run.add_argument("--source", choices=("runs", "submission"), default="submission")
    for name in ("verify", "export", "evaluate"):
        command = sub.add_parser(name)
        command.add_argument("run_id")
        command.add_argument(
            "--source", choices=("corrections", "submission"), default="corrections"
        )
        command.add_argument("--base-source", choices=("runs", "submission"), default="submission")
    args = parser.parse_args()
    try:
        if args.command == "run":
            directory = run_corrections(
                args.project_dir,
                base_run_id=args.base_run_id,
                run_id=args.run_id,
                config_file=args.config,
                source=args.source,
                on_case=_progress,
            )
            print(json.dumps({"directory": str(directory)}))
        else:
            RunOptions(run_id=args.run_id)
            directory = args.project_dir / f"results/{args.source}" / args.run_id
            metadata = json.loads((directory / "correction-run.json").read_bytes())
            base_id = metadata["base_run_id"]
            RunOptions(run_id=base_id)
            base = args.project_dir / f"results/{args.base_source}" / base_id
            if args.command == "export":
                report = export_corrections(
                    directory, base, args.project_dir / "results/submission" / args.run_id
                )
            elif args.command == "evaluate":
                report = evaluate_corrections(args.project_dir, directory, base)
            else:
                _, cases = verify_corrections(directory, base)
                report = {"verified_cases": len(cases)}
            print(json.dumps(report))
    except (ValueError, OSError) as error:
        print(json.dumps({"correction_error": type(error).__name__, "reason": str(error)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
