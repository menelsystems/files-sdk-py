"""DigitalOcean Spaces conformance fixtures.

Spaces inherits S3-compatible behavior. Conformance runs S3Adapter against
moto; DO-specific endpoint construction and public-URL logic are tested in
test_digitalocean_specific.py.
"""

from __future__ import annotations

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
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def do_bucket(moto_endpoint: str, aws_credentials: None) -> str:
    import uuid

    bucket = f"do-{uuid.uuid4().hex[:12]}"
    boto3.client("s3", endpoint_url=moto_endpoint, region_name="us-east-1").create_bucket(
        Bucket=bucket
    )
    return bucket


@pytest.fixture
def adapter(moto_endpoint: str, do_bucket: str):
    from files_sdk_s3 import S3Adapter

    return S3Adapter(bucket=do_bucket, endpoint_url=moto_endpoint, region="us-east-1")


@pytest.fixture
def async_adapter(moto_endpoint: str, do_bucket: str):
    from files_sdk_s3 import AsyncS3Adapter

    return AsyncS3Adapter(bucket=do_bucket, endpoint_url=moto_endpoint, region="us-east-1")
