"""Offline protocol commands with bounded execution and separate result publication."""

import argparse
import json
import signal
import tempfile
from pathlib import Path
from typing import Any

from extraction_service.archiving.files import canonical, confined, digest, read_json
from extraction_service.evaluation.comparison import compare_experiment
from extraction_service.evaluation.protocol import load_protocol, verify_sources

COMMANDS = ("validate-evaluation-protocol", "evaluate-experiment")
DEFAULT_PROTOCOL = "config/evaluation/P01-E01-v4.json"


def add_commands(commands: Any) -> None:
    """Expose evaluation without generation, setup or accounting options."""

    for name in COMMANDS:
        parser = commands.add_parser(name)
        parser.add_argument("--protocol", default=DEFAULT_PROTOCOL)
        parser.add_argument("--source", required=True)
        if name == "evaluate-experiment":
            parser.add_argument("--check-result")


def _expired(signum: int, frame: Any) -> None:
    raise TimeoutError("Offline evaluation deadline exceeded")


def dispatch(args: argparse.Namespace) -> int:
    """Execute only read-only evaluation and a new, confined output directory."""

    previous = signal.signal(signal.SIGALRM, _expired)
    signal.setitimer(signal.ITIMER_REAL, 900)
    try:
        protocol = load_protocol(args.project_dir, args.protocol)
        seconds = min(protocol.limits.verification_seconds, 900)
        if args.command == "validate-evaluation-protocol":
            signal.setitimer(signal.ITIMER_REAL, seconds)
            verify_sources(args.project_dir, protocol, args.source)
            print(
                json.dumps(
                    {"valid": True, "model_calls": 0, "experiment_id": protocol.experiment_id}
                )
            )
            return 0

        signal.setitimer(signal.ITIMER_REAL, min(protocol.limits.analysis_seconds, 300))
        report = compare_experiment(args.project_dir, args.protocol, args.source)
        if args.check_result:
            if read_json(confined(args.project_dir, args.check_result)) != report:
                raise ValueError("Saved paired result differs from regenerated evidence")
            print(json.dumps({"result_matches": True, "model_calls": 0}))
            return 0

        destination = confined(args.project_dir, protocol.output)
        if destination.exists():
            raise FileExistsError("Analysis destination already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent, prefix=".analysis-") as temporary:
            staging = Path(temporary) / "result"
            staging.mkdir()
            (staging / "report.json").write_bytes(canonical(report))
            (staging / "protocol.json").write_bytes(
                confined(args.project_dir, args.protocol).read_bytes()
            )
            inventory = {p.name: digest(p) for p in staging.iterdir()}
            (staging / "files.sha256.json").write_bytes(canonical(inventory))
            staging.rename(destination)
        print(
            json.dumps(
                {
                    "output": protocol.output,
                    "model_calls": 0,
                    "paired_cases": report["selected_inputs"],
                }
            )
        )
        return 0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
