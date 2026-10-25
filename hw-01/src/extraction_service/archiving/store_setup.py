"""Explicit single-node Garage configuration with generated local credentials."""

import os
import secrets
import tempfile
from pathlib import Path

from extraction_service.archiving.files import confined, publish


def initialize_store(project: Path) -> dict[str, str]:
    """Create first-use configuration only; never replace existing credentials or data."""

    environment = project / ".env.archive"
    directory = confined(project, "results/garage-config")
    configuration = directory / "garage.toml"

    if (
        environment.exists()
        or environment.is_symlink()
        or configuration.exists()
        or configuration.is_symlink()
    ):
        raise FileExistsError("Archive store settings already exist")

    directory.mkdir(parents=True, exist_ok=True)
    access_key = "GK" + secrets.token_hex(12)
    secret_key = secrets.token_hex(32)
    values = (
        "HW01_ARCHIVE_ENDPOINT_URL=http://garage:3900\n"
        "HW01_ARCHIVE_REGION=garage\nHW01_ARCHIVE_BUCKET=hw01-evidence\n"
        f"HW01_ARCHIVE_ACCESS_KEY={access_key}\nHW01_ARCHIVE_SECRET_KEY={secret_key}\n"
        f"GARAGE_DEFAULT_ACCESS_KEY={access_key}\nGARAGE_DEFAULT_SECRET_KEY={secret_key}\n"
        "GARAGE_DEFAULT_BUCKET=hw01-evidence\n"
    )
    config = (
        'metadata_dir = "/var/lib/garage/meta"\ndata_dir = "/var/lib/garage/data"\n'
        'db_engine = "sqlite"\nreplication_factor = 1\n'
        'rpc_bind_addr = "0.0.0.0:3901"\nrpc_public_addr = "127.0.0.1:3901"\n'
        f'rpc_secret = "{secrets.token_hex(32)}"\n'
        '[s3_api]\ns3_region = "garage"\napi_bind_addr = "0.0.0.0:3900"\n'
    )

    with tempfile.TemporaryDirectory(prefix="hw01-store-") as temporary:
        for name, destination, content in (
            ("environment", environment, values),
            ("configuration", configuration, config),
        ):
            source = Path(temporary) / name
            source.write_text(content)
            os.chmod(source, 0o600)
            publish(source, destination)
            os.chmod(destination, 0o600)

    return {"configured": "single-node Garage", "credentials": ".env.archive"}
