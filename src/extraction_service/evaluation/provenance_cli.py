"""Bounded offline provenance commands and copy-only result publication."""

import argparse
import json
import signal
import tempfile
import time
from pathlib import Path
from typing import Any

from extraction_service.archiving.files import canonical, confined, digest, read_json
from extraction_service.evaluation.experiment import _expired
from extraction_service.evaluation.provenance import assess_provenance, load_provenance_protocol

COMMANDS = ("validate-provenance-protocol", "assess-provenance")


def add_commands(commands: Any) -> None:
    """Register explicitly offline entrypoints without provider switches."""

    for name in COMMANDS:
        parser = commands.add_parser(name)
        parser.add_argument("--protocol", default="config/evaluation/P02-E01-v3.json")
        parser.add_argument("--source", required=True)
        if name == "assess-provenance":
            parser.add_argument("--check-result")


def dispatch(args: argparse.Namespace) -> int:
    """Verify sources before atomic publication; never replace an existing result."""

    previous = signal.signal(signal.SIGALRM, _expired)
    signal.setitimer(signal.ITIMER_REAL, 300)
    try:
        started = time.monotonic()
        protocol = load_provenance_protocol(args.project_dir, args.protocol)
        report = assess_provenance(args.project_dir, args.protocol, args.source)
        if args.command == "validate-provenance-protocol":
            print(json.dumps({"valid": True, "model_calls": 0, "records": len(report["records"])}))
            return 0
        if args.check_result:
            if read_json(confined(args.project_dir, args.check_result)) != report:
                raise ValueError("Saved provenance differs from regenerated evidence")
            print(json.dumps({"result_matches": True, "model_calls": 0}))
            return 0
        destination = confined(args.project_dir, protocol.output)
        if destination.exists():
            raise FileExistsError("Provenance output already exists")
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            dir=destination.parent, prefix=".provenance-"
        ) as temporary:
            staging = Path(temporary) / "result"
            staging.mkdir()
            (staging / "report.json").write_bytes(canonical(report))
            (staging / "protocol.json").write_bytes(
                confined(args.project_dir, args.protocol).read_bytes()
            )
            (staging / "files.sha256.json").write_bytes(
                canonical({path.name: digest(path) for path in staging.iterdir()})
            )
            staging.rename(destination)
        print(
            json.dumps(
                {
                    "output": protocol.output,
                    "counts": report["counts"],
                    "model_calls": 0,
                    "assessment_seconds": time.monotonic() - started,
                }
            )
        )
        return 0
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
