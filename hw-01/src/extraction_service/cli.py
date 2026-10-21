"""Contract checks and explicitly selected extraction/accounting commands."""

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final

from extraction_service.application import cli as application_cli
from extraction_service.artifacts import read_checked
from extraction_service.corpus.constants import GOLD_MANIFEST_FILENAME
from extraction_service.exit_status import ExitStatus
from extraction_service.extraction import ExtractionContract
from extraction_service.extraction.constants import SCHEMA_FILENAME
from extraction_service.preflight import DEFAULT_EXPERIMENT_FILE, preflight

EXIT_SUCCESS: Final[int] = ExitStatus.SUCCESS
EXIT_VALIDATION_FAILURE: Final[int] = ExitStatus.EXTRACTION_FAILURE
EXIT_SETUP_FAILURE: Final[int] = ExitStatus.SETUP_FAILURE
JSON_INDENT: Final[int] = 2

VALIDATE_GOLD_COMMAND: Final[str] = "validate-gold"
VALIDATE_RESPONSE_COMMAND: Final[str] = "validate-response"
PREFLIGHT_COMMAND: Final[str] = "preflight"


def _print_json(value: object, *, indent: int | None = JSON_INDENT) -> None:
    formatted = json.dumps(value, ensure_ascii=False, indent=indent)

    print(formatted)


def _gold_failures(
    project_dir: Path,
    contract: ExtractionContract,
    cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    failures: list[dict[str, Any]] = []

    for case in cases:
        path = project_dir / "data" / case["goldFile"]
        raw_response = read_checked(path, case["goldSha256"])
        outcome = contract.validate_json(raw_response)

        if not outcome.is_valid:
            outcome_record = asdict(outcome)
            failure = {
                "inputId": case["inputId"],
                "issues": outcome_record["issues"],
            }
            failures.append(failure)

    return failures


def validate_gold(project_dir: Path, contract: ExtractionContract, manifest: dict[str, Any]) -> int:
    """Check all approved gold artifacts and print aggregate JSON evidence.

    Returns:
        Success when every case passes, otherwise a validation-failure status.

    Raises:
        ArtifactError: A gold artifact differs from its hash or cannot be read.
    """

    cases = manifest["cases"]
    failures = _gold_failures(project_dir, contract, cases)
    summary = {
        "schema": asdict(contract.identity),
        "gold_count": len(cases),
        "valid_count": len(cases) - len(failures),
        "failures": failures,
    }

    _print_json(summary)

    if failures:
        return EXIT_VALIDATION_FAILURE

    return EXIT_SUCCESS


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(VALIDATE_GOLD_COMMAND, help="Check every approved gold object and its hash")

    preflight_parser = commands.add_parser(PREFLIGHT_COMMAND, help="Verify complete offline setup")
    preflight_parser.add_argument("--config", default=DEFAULT_EXPERIMENT_FILE)

    response_parser = commands.add_parser(
        VALIDATE_RESPONSE_COMMAND,
        help="Validate one raw JSON response file",
    )
    response_parser.add_argument("response_file", type=Path)
    application_cli.add_commands(commands)

    return parser


def _load_contract(project_dir: Path) -> tuple[ExtractionContract, dict[str, Any]]:
    manifest_path = project_dir / "data" / GOLD_MANIFEST_FILENAME
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema_path = project_dir / "schemas" / SCHEMA_FILENAME
    contract = ExtractionContract.load(
        schema_path,
        expected_sha256=manifest["schemaSha256"],
    )

    return contract, manifest


def _validate_response(path: Path, contract: ExtractionContract) -> int:
    raw_response = path.read_text(encoding="utf-8")
    outcome = contract.validate_json(raw_response)
    outcome_record = asdict(outcome)

    _print_json(outcome_record)

    if outcome.is_valid:
        return EXIT_SUCCESS

    return EXIT_VALIDATION_FAILURE


def _dispatch(args: argparse.Namespace) -> int:
    if args.command in application_cli.COMMANDS:
        return application_cli.dispatch(args)

    if args.command == PREFLIGHT_COMMAND:
        report = preflight(args.project_dir, args.config)
        print(report.model_dump_json(indent=JSON_INDENT))

        return EXIT_SUCCESS

    contract, manifest = _load_contract(args.project_dir)

    if args.command == VALIDATE_GOLD_COMMAND:
        return validate_gold(args.project_dir, contract, manifest)

    return _validate_response(args.response_file, contract)


def main(argv: list[str] | None = None) -> int:
    """Parse explicit commands and report checked execution/setup outcomes.

    Args:
        argv: Command arguments, or None to use process arguments.

    Returns:
        Zero for success, one for invalid output, two for setup/application
        errors, three for incomplete work, or 130 for caught interruption.
        Argument parsing uses argparse's standard SystemExit behavior.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return _dispatch(args)
    except KeyboardInterrupt:
        _print_json({"interrupted": True}, indent=None)

        return ExitStatus.INTERRUPTED
    except (OSError, ValueError, KeyError, TypeError) as error:
        # Operational exceptions may contain arbitrary provider or local input.
        message = type(error).__name__ if args.command in application_cli.COMMANDS else str(error)
        error_report = {"setup_error": message}
        _print_json(error_report, indent=None)

        return EXIT_SETUP_FAILURE
    except Exception as error:
        if args.command not in application_cli.COMMANDS:
            raise

        _print_json({"unexpected_error": type(error).__name__}, indent=None)

        return EXIT_SETUP_FAILURE
