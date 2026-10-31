"""Explicit native split execution and offline export/verification/evaluation."""

import argparse
import json
from pathlib import Path

from extraction_service.application.selection import RunOptions
from extraction_service.staged.application import run_split
from extraction_service.staged.evaluation import evaluate_split
from extraction_service.staged.extractor import SplitResult
from extraction_service.staged.storage import export_split, verify_split


def progress(input_id: str, result: SplitResult) -> None:
    """Report per-stage requests and measured time without printing source or PO data."""

    print(
        json.dumps(
            {
                "input_id": input_id,
                "valid": result.extraction is not None,
                "stages": {
                    s.value: {
                        "status": r.status.value,
                        "calls": len(r.attempts),
                        "seconds": r.duration_ms / 1000,
                    }
                    for s, r in result.records.items()
                },
                "seconds": result.duration_ms / 1000,
            }
        ),
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--base-run-id", required=True)
    run.add_argument("--run-id", required=True)
    run.add_argument("--config", default="config/gemma-scoped-roles.yaml")
    for name in ("verify", "export", "evaluate"):
        command = commands.add_parser(name)
        command.add_argument("run_id")
        command.add_argument("--source", choices=("split", "submission"), default="split")
    args = parser.parse_args()
    try:
        if args.command == "run":
            directory = run_split(
                args.project_dir,
                base_run_id=args.base_run_id,
                run_id=args.run_id,
                config_file=args.config,
                on_case=progress,
            )
            header, cases, _ = verify_split(
                directory, args.project_dir / "results/submission" / args.base_run_id
            )
            print(json.dumps({"run_id": header["run_id"], "cases": len(cases)}))
            return int(any(case.extraction is None for case in cases))
        RunOptions(run_id=args.run_id)
        directory = args.project_dir / f"results/{args.source}" / args.run_id
        metadata = json.loads((directory / "split-run.json").read_bytes())
        base_id = metadata["base_run_id"]
        RunOptions(run_id=base_id)
        base = args.project_dir / "results/submission" / base_id
        if args.command == "export":
            result = export_split(
                directory, base, args.project_dir / "results/submission" / args.run_id
            )
        elif args.command == "evaluate":
            result = evaluate_split(args.project_dir, directory, base)
        else:
            _, cases, _ = verify_split(directory, base)
            result = {"verified_cases": len(cases)}
        print(json.dumps(result))
    except (ValueError, OSError) as error:
        print(json.dumps({"split_error": type(error).__name__, "reason": str(error)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
