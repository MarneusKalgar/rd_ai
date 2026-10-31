"""Explicit setup entrypoint; there is deliberately no inference command here."""

import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from extraction_service.configuration.settings import ApplicationSettings, OllamaMode
from extraction_service.inference.errors import ModelTransportError
from extraction_service.inference.transport.client_setup import ollama_client
from extraction_service.runtime.configuration import CapacityScope, SetupSettings
from extraction_service.runtime.errors import SetupError
from extraction_service.runtime.native import initialize_native
from extraction_service.runtime.storage import verify_storage
from extraction_service.runtime.workflows import ReadinessStatus, local_setup, provider_setup


def main(arguments: list[str] | None = None) -> int:
    """Report safe setup failures with exit 2, or a recorded readiness blocker with 3."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--model-id")
    parser.add_argument(
        "--exhaustive", action="store_true", help="Check all prepared requests (readiness only)"
    )
    parser.add_argument(
        "command", choices=["provider", "initialize", "initialize-native", "readiness", "storage"]
    )
    args = parser.parse_args(arguments)

    if args.exhaustive and args.command != "readiness":
        parser.error("--exhaustive is only supported with readiness")

    try:
        if args.command == "provider":
            report = provider_setup(args.project_dir, args.model_id or "provider")
        elif args.command == "storage":
            report = verify_storage(args.project_dir / "results")
        elif args.command == "initialize-native":
            application_settings = ApplicationSettings.load(args.project_dir)

            if application_settings.ollama_mode != OllamaMode.NATIVE:
                raise SetupError("Native initialization requires explicit native mode")

            with ollama_client(application_settings) as client:
                report = initialize_native(args.project_dir, args.model_id or "local", client)
        else:
            settings = SetupSettings()
            application_settings = ApplicationSettings.load(args.project_dir)

            if application_settings.ollama_mode != OllamaMode.DOCKER:
                raise SetupError("Docker diagnostics require explicit Docker mode")

            with ollama_client(application_settings) as client:
                report = local_setup(
                    args.project_dir,
                    args.model_id or "local",
                    settings,
                    client,
                    initialize=args.command == "initialize",
                    capacity_scope=(
                        CapacityScope.EXHAUSTIVE
                        if args.exhaustive
                        else CapacityScope.REPRESENTATIVE
                    ),
                )
    except ModelTransportError as error:
        print(
            json.dumps(
                {
                    "setup_error": error.evidence.kind.value,
                    "action": "Check Ollama connectivity/download and retry explicit setup",
                }
            )
        )
        return 2
    except (ValueError, OSError) as error:
        # Pydantic errors hide input values; filesystem/other errors may contain
        # private paths. Print their type only, never dotenv values or HTTP headers.
        message = (
            str(error) if isinstance(error, (SetupError, ValidationError)) else type(error).__name__
        )
        print(
            json.dumps({"setup_error": message, "action": "Check setup configuration and storage"})
        )
        return 2

    print(json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2))

    return 3 if report.get("status") == ReadinessStatus.BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
