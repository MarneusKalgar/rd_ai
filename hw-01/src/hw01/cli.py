"""Offline contract checks; this command does not run models or spend API credits."""

import argparse
import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Final

from hw01.extraction import ContractLoadError, ExtractionContract
from hw01.extraction.constants import SCHEMA_FILENAME

GOLD_MANIFEST_FILENAME: Final[str] = "manifest.json"
EXIT_SUCCESS: Final[int] = 0
EXIT_VALIDATION_FAILURE: Final[int] = 1
EXIT_SETUP_FAILURE: Final[int] = 2


def read_checked(path: Path, expected_sha256: str) -> str:
    """Read an approved UTF-8 artifact only if its bytes match the expected hash.

    Raises:
        ContractLoadError: Artifact bytes differ from the approved hash.
        OSError: The file cannot be read.
        UnicodeError: The verified bytes are not UTF-8 text.
    """

    data = path.read_bytes()
    actual_sha256 = hashlib.sha256(data).hexdigest()

    if actual_sha256 != expected_sha256:
        raise ContractLoadError(f"Approved artifact hash mismatch: {path}")

    return data.decode("utf-8")


def validate_gold(project_dir: Path, contract: ExtractionContract, manifest: dict[str, Any]) -> int:
    """Verify and validate each gold artifact, then print aggregate JSON evidence.

    Returns:
        Success when every case passes, otherwise a validation-failure status.

    Raises:
        ContractLoadError: A gold artifact differs from its manifest hash.
        OSError: A gold artifact cannot be read.
        UnicodeError: An artifact is not UTF-8 text.
    """

    failures: list[dict[str, Any]] = []

    for case in manifest["cases"]:
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

    summary = {
        "schema": asdict(contract.identity),
        "gold_count": len(manifest["cases"]),
        "valid_count": len(manifest["cases"]) - len(failures),
        "failures": failures,
    }

    formatted_summary = json.dumps(
        summary,
        ensure_ascii=False,
        indent=2,
    )

    print(formatted_summary)

    if failures:
        return EXIT_VALIDATION_FAILURE

    return EXIT_SUCCESS


def main(argv: list[str] | None = None) -> int:
    """Run offline validation and print a JSON outcome or setup error.

    Args:
        argv: Command arguments, or None to use the process arguments.

    Returns:
        Zero for success, one for invalid output, or two for setup/file errors.
        Argument parsing uses argparse's standard SystemExit behavior.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())

    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-gold", help="Check every approved gold object and its hash")

    response_parser = commands.add_parser(
        "validate-response",
        help="Validate one raw JSON response file",
    )
    response_parser.add_argument("response_file", type=Path)

    args = parser.parse_args(argv)

    try:
        manifest_path = args.project_dir / "data" / GOLD_MANIFEST_FILENAME
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        schema_path = args.project_dir / "schemas" / SCHEMA_FILENAME
        contract = ExtractionContract.load(
            schema_path,
            expected_sha256=manifest["schemaSha256"],
        )

        if args.command == "validate-gold":
            return validate_gold(args.project_dir, contract, manifest)

        raw_response = args.response_file.read_text(encoding="utf-8")
        outcome = contract.validate_json(raw_response)

        outcome_record = asdict(outcome)
        formatted_outcome = json.dumps(
            outcome_record,
            ensure_ascii=False,
            indent=2,
        )

        print(formatted_outcome)

        if outcome.is_valid:
            return EXIT_SUCCESS

        return EXIT_VALIDATION_FAILURE
    except (OSError, ValueError, KeyError, TypeError) as error:
        error_report = {"setup_error": str(error)}
        formatted_error = json.dumps(error_report, ensure_ascii=False)

        print(formatted_error)

        return EXIT_SETUP_FAILURE
