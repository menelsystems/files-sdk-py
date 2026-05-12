"""Real multipart upload — verifies TransferConfig threshold wiring against a live server."""

from __future__ import annotations

import io
import uuid

import pytest

pytestmark = pytest.mark.integration


def test_multipart_upload_above_threshold(
    integration_endpoint: str,
    integration_bucket: str,
    integration_credentials: dict[str, str],
) -> None:
    """Upload 12 MiB with a 5 MiB multipart threshold — forces multipart path."""
    from files_sdk_s3 import S3Adapter

    a = S3Adapter(
        bucket=integration_bucket,
        endpoint_url=integration_endpoint,
        access_key_id=integration_credentials["access_key_id"],
        secret_access_key=integration_credentials["secret_access_key"],
        region=integration_credentials["region"],
        multipart_threshold=5 * 1024 * 1024,
    )
    payload = (b"abcdefgh" * 1024) * 1536  # 12 MiB
    assert len(payload) == 12 * 1024 * 1024
    key = f"multipart/{uuid.uuid4().hex}.bin"
    a.upload(key, io.BytesIO(payload))  # file-like triggers upload_fileobj + TransferConfig
    sf = a.download(key)
    assert sf.data == payload
    assert sf.metadata.size == len(payload)


def test_small_upload_below_threshold_uses_put(
    integration_endpoint: str,
    integration_bucket: str,
    integration_credentials: dict[str, str],
) -> None:
    """Below threshold uploads go through put_object — sanity check that the bytes path also works."""
    from files_sdk_s3 import S3Adapter

    a = S3Adapter(
        bucket=integration_bucket,
        endpoint_url=integration_endpoint,
        access_key_id=integration_credentials["access_key_id"],
        secret_access_key=integration_credentials["secret_access_key"],
        region=integration_credentials["region"],
        multipart_threshold=5 * 1024 * 1024,
    )
    key = f"small/{uuid.uuid4().hex}.bin"
    a.upload(key, b"small payload")
    assert a.download(key).data == b"small payload"
