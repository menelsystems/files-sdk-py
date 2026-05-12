"""Fixtures for files-sdk-s3 tests.

Uses `moto.server.ThreadedMotoServer` — moto ships a real HTTP server precisely
because the `mock_aws()` botocore stubber path does not work with aiobotocore 2.x.
Both sync (boto3) and async (aioboto3) clients connect via `endpoint_url`, so the
same backing server services both transports with zero monkey-patching.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterator

import boto3
import pytest
from moto.server import ThreadedMotoServer


@pytest.fixture(scope="session")
def moto_endpoint() -> Iterator[str]:
    server = ThreadedMotoServer(port=0)
    server.start()
    host, port = server.get_host_and_port()
    try:
        yield f"http://{host}:{port}"
    finally:
        server.stop()


@pytest.fixture
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def s3_bucket(moto_endpoint: str, aws_credentials: None) -> str:
    """Create a fresh bucket per test against the shared moto server."""
    bucket = f"conf-{uuid.uuid4().hex[:12]}"
    client = boto3.client("s3", endpoint_url=moto_endpoint, region_name="us-east-1")
    client.create_bucket(Bucket=bucket)
    return bucket


@pytest.fixture
def adapter(moto_endpoint: str, s3_bucket: str):
    from files_sdk_s3 import S3Adapter
    return S3Adapter(bucket=s3_bucket, endpoint_url=moto_endpoint, region="us-east-1")


@pytest.fixture
def async_adapter(moto_endpoint: str, s3_bucket: str):
    from files_sdk_s3 import AsyncS3Adapter
    return AsyncS3Adapter(bucket=s3_bucket, endpoint_url=moto_endpoint, region="us-east-1")
