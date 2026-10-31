"""Explicit archive commands; never run models, modify Git or remove source evidence."""

import argparse
import json
from pathlib import Path

from extraction_service.archiving.archive import (
    create_archive,
    load_index,
    restore_archive,
    verify_archive,
)
from extraction_service.archiving.files import confined


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("--config", default="config/archives.yaml")
    create.add_argument("--selection", required=True)
    commands.add_parser("init-store")

    for command in ("verify", "restore", "upload", "download"):
        subparser = commands.add_parser(command)
        subparser.add_argument(
            "--index", required=True, help="Project-relative compact archive index"
        )

    args = parser.parse_args(arguments)

    try:
        if args.command == "init-store":
            from extraction_service.archiving.store_setup import initialize_store

            report: object = initialize_store(args.project_dir)
        elif args.command == "create":
            index = create_archive(args.project_dir, args.config, args.selection)
            report = index.model_dump(mode="json")
        else:
            index = load_index(confined(args.project_dir, args.index))

            if args.command == "verify":
                manifest = verify_archive(args.project_dir, index)
                report = {"verified": True, "bundles": len(manifest.bundles)}
            elif args.command == "restore":
                restored = restore_archive(args.project_dir, index)
                report = {"restored": restored.relative_to(args.project_dir).as_posix()}
            else:
                # Offline operations neither import the SDK nor load storage credentials.
                from extraction_service.archiving.storage import (
                    StorageSettings,
                    download_archive,
                    storage_client,
                    upload_archive,
                )

                settings = StorageSettings()

                with storage_client(settings) as client:
                    if args.command == "upload":
                        report = upload_archive(args.project_dir, index, client, settings.bucket)
                    else:
                        downloaded = download_archive(
                            args.project_dir, index, client, settings.bucket
                        )
                        report = {"downloaded": downloaded.relative_to(args.project_dir).as_posix()}

        print(json.dumps(report, indent=2))
        return 0
    except Exception as error:
        # SDK errors and invalid settings can contain URLs/credentials or untrusted data.
        print(json.dumps({"archive_error": type(error).__name__, "command": args.command}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
