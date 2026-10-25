"""S3 contracts include conflict detection, download validation and redacted failures."""

import io
import json
from pathlib import Path

import pytest
from botocore.exceptions import ClientError
from botocore.response import StreamingBody
from botocore.stub import ANY, Stubber
from pydantic import SecretStr, ValidationError

from extraction_service.archiving.archive import archive_path
from extraction_service.archiving.storage import (
    StorageSettings,
    download_archive,
    storage_client,
    upload_archive,
)

from .test_archiving import _create
from .test_archiving import archive_project as archive_project


def _settings() -> StorageSettings:
    return StorageSettings(
        endpoint_url="http://localhost:1",
        bucket="hw01-test",
        access_key=SecretStr("test-access-key"),
        secret_key=SecretStr("test-secret-key"),
    )


def _body(content: bytes) -> StreamingBody:
    return StreamingBody(io.BytesIO(content), len(content))


@pytest.mark.parametrize("existing", [False, True])
def test_upload_verifies_get_and_reuses_identical_remote_evidence(
    archive_project: Path,
    existing: bool,
) -> None:
    index = _create(archive_project)
    content = archive_path(archive_project, index).read_bytes()
    settings = _settings()
    params = {"Bucket": settings.bucket, "Key": index.object_key}

    with storage_client(settings) as client, Stubber(client) as stub:
        if existing:
            stub.add_response("head_object", {"ContentLength": len(content)}, params)
        else:
            stub.add_client_error(
                "head_object",
                service_error_code="404",
                http_status_code=404,
                expected_params=params,
            )
            stub.add_response(
                "put_object",
                {},
                {
                    **params,
                    "Body": ANY,
                    "ContentLength": len(content),
                    "ContentType": "application/gzip",
                    "Metadata": {"sha256": index.archive_sha256},
                },
            )
        stub.add_response(
            "get_object", {"Body": _body(content), "ContentLength": len(content)}, params
        )

        report = upload_archive(archive_project, index, client, settings.bucket)

        assert report["download_verified"] is True and report["uploaded"] is not existing
        stub.assert_no_pending_responses()

    receipt = archive_project / f"archive-index/{index.archive_sha256}.remote.json"
    assert json.loads(receipt.read_bytes())["archive_sha256"] == index.archive_sha256
    assert "test-secret-key" not in receipt.read_text()


def test_existing_conflicting_object_is_never_uploaded_over(archive_project: Path) -> None:
    index = _create(archive_project)
    wrong = b"x" * index.archive_size
    settings = _settings()
    params = {"Bucket": settings.bucket, "Key": index.object_key}

    with storage_client(settings) as client, Stubber(client) as stub:
        stub.add_response("head_object", {"ContentLength": len(wrong)}, params)
        stub.add_response("get_object", {"Body": _body(wrong), "ContentLength": len(wrong)}, params)

        with pytest.raises(ValueError, match="checksum"):
            upload_archive(archive_project, index, client, settings.bucket)
        stub.assert_no_pending_responses()

    assert not (archive_project / f"archive-index/{index.archive_sha256}.remote.json").exists()


@pytest.mark.parametrize("defect", ["checksum", "size", "short-body"])
def test_bad_download_does_not_publish_or_replace_local_evidence(
    archive_project: Path,
    defect: str,
) -> None:
    index = _create(archive_project)
    path = archive_path(archive_project, index)
    original = path.read_bytes()
    content = (b"x" * len(original)) if defect == "checksum" else original[:-1]
    size = len(content) if defect == "size" else len(original)
    settings = _settings()

    with storage_client(settings) as client, Stubber(client) as stub:
        stub.add_response(
            "get_object",
            {"Body": _body(content), "ContentLength": size},
            {"Bucket": settings.bucket, "Key": index.object_key},
        )
        with pytest.raises((ValueError, OSError)):
            download_archive(archive_project, index, client, settings.bucket)

    assert path.read_bytes() == original
    assert not list(path.parent.glob(".download-*"))


def test_download_validates_full_bundle_after_original_cache_is_absent(
    archive_project: Path,
) -> None:
    index = _create(archive_project)
    path = archive_path(archive_project, index)
    content = path.read_bytes()
    path.unlink()
    settings = _settings()

    with storage_client(settings) as client, Stubber(client) as stub:
        stub.add_response(
            "get_object",
            {"Body": _body(content), "ContentLength": len(content)},
            {"Bucket": settings.bucket, "Key": index.object_key},
        )
        downloaded = download_archive(archive_project, index, client, settings.bucket)

    assert downloaded.read_bytes() == content


def test_credentials_in_endpoint_are_rejected_without_displaying_values() -> None:
    with pytest.raises(ValidationError) as raised:
        StorageSettings(
            endpoint_url="http://person:test-secret@localhost:3900",
            bucket="hw01-test",
            access_key=SecretStr("test-access"),
            secret_key=SecretStr("test-secret"),
        )

    assert "test-secret" not in str(raised.value)


def test_failed_upload_does_not_publish_a_verification_receipt(archive_project: Path) -> None:
    index = _create(archive_project)
    settings = _settings()

    with storage_client(settings) as client, Stubber(client) as stub:
        stub.add_client_error("head_object", service_error_code="404", http_status_code=404)
        stub.add_client_error("put_object", service_error_code="AccessDenied", http_status_code=403)

        with pytest.raises(ClientError):
            upload_archive(archive_project, index, client, settings.bucket)
        stub.assert_no_pending_responses()

    assert not (archive_project / f"archive-index/{index.archive_sha256}.remote.json").exists()
