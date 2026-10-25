"""Explicit S3 transfers; verify downloaded bytes instead of trusting ETags."""

import tempfile
from collections.abc import Generator
from contextlib import closing, contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from pydantic import AnyHttpUrl, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from extraction_service.archiving.archive import archive_path, verify_archive, verify_archive_file
from extraction_service.archiving.files import canonical, confined, digest, publish
from extraction_service.archiving.models import ArchiveIndex

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HW01_ARCHIVE_", hide_input_in_errors=True)

    endpoint_url: AnyHttpUrl
    region: str = "garage"
    bucket: str = Field(pattern=r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
    access_key: SecretStr
    secret_key: SecretStr

    @field_validator("endpoint_url")
    @classmethod
    def plain_endpoint(cls, value: AnyHttpUrl) -> AnyHttpUrl:
        if value.username or value.password or value.query or value.fragment:
            raise ValueError("Endpoint must not contain credentials, query or fragment")

        return value


@contextmanager
def storage_client(settings: StorageSettings) -> Generator[S3Client]:
    """Use explicit credentials only; never fall back to an AWS credential chain."""

    client = boto3.client(
        "s3",
        endpoint_url=str(settings.endpoint_url),
        region_name=settings.region,
        aws_access_key_id=settings.access_key.get_secret_value(),
        aws_secret_access_key=settings.secret_key.get_secret_value(),
        config=Config(
            signature_version="s3v4",
            connect_timeout=10,
            read_timeout=60,
            retries={"max_attempts": 0},
            s3={"addressing_style": "path", "payload_signing_enabled": True},
            request_checksum_calculation="when_required",
            response_checksum_validation="when_required",
        ),
    )

    try:
        yield client
    finally:
        client.close()


def _receive(client: S3Client, bucket: str, index: ArchiveIndex, destination: Path) -> None:
    response = client.get_object(Bucket=bucket, Key=index.object_key)

    with closing(response["Body"]) as body:
        if response.get("ContentLength") != index.archive_size:
            raise ValueError("Remote archive size differs")

        received = 0

        with destination.open("xb") as output:
            for chunk in body.iter_chunks(chunk_size=1024 * 1024):
                received += len(chunk)

                if received > index.archive_size:
                    raise ValueError("Remote body exceeds indexed size")

                output.write(chunk)

    if received != index.archive_size or digest(destination) != index.archive_sha256:
        raise ValueError("Downloaded archive checksum differs")


def upload_archive(
    project: Path, index: ArchiveIndex, client: S3Client, bucket: str
) -> dict[str, object]:
    """Refuse an existing conflicting object; mark success only after a full GET check.

    Hash keys make cooperating uploads idempotent. This is not server-side
    immutability: Garage has no Object Lock, and another client can change data.
    """

    verify_archive(project, index)
    exists = True

    try:
        client.head_object(Bucket=bucket, Key=index.object_key)
    except ClientError as error:
        if error.response["Error"]["Code"] not in ("404", "NoSuchKey", "NotFound"):
            raise

        exists = False

    with tempfile.TemporaryDirectory(prefix="hw01-upload-") as temporary:
        path = Path(temporary) / "download.tar.gz"

        if not exists:
            with archive_path(project, index).open("rb") as source:
                client.put_object(
                    Bucket=bucket,
                    Key=index.object_key,
                    Body=source,
                    ContentLength=index.archive_size,
                    ContentType="application/gzip",
                    Metadata={"sha256": index.archive_sha256},
                )

        _receive(client, bucket, index, path)
        receipt: dict[str, object] = {
            "archive_sha256": index.archive_sha256,
            "bucket": bucket,
            "object_key": index.object_key,
            "download_verified": True,
        }
        receipt_path = Path(temporary) / "receipt.json"
        receipt_path.write_bytes(canonical(receipt))
        destination = confined(project, f"archive-index/{index.archive_sha256}.remote.json")
        publish(receipt_path, destination)

    return {**receipt, "uploaded": not exists}


def download_archive(project: Path, index: ArchiveIndex, client: S3Client, bucket: str) -> Path:
    cache = confined(project, "results/archives")
    cache.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(dir=cache, prefix=".download-") as temporary:
        path = Path(temporary) / "archive.tar.gz"
        _receive(client, bucket, index, path)
        verify_archive_file(path, index)
        publish(path, archive_path(project, index))

    verify_archive(project, index)

    return archive_path(project, index)
