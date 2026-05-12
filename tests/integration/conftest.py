"""Integration conftest — uses FILES_SDK_INTEGRATION_ENDPOINT to point at a live server."""

from __future__ import annotations

import os
import uuid
from collections.abc import Iterator

import boto3
import pytest


@pytest.fixture(scope="session")
def integration_endpoint() -> str:
    ep = os.environ.get("FILES_SDK_INTEGRATION_ENDPOINT")
    if not ep:
        pytest.skip("FILES_SDK_INTEGRATION_ENDPOINT not set")
    return ep


@pytest.fixture(scope="session")
def integration_credentials() -> dict[str, str]:
    return {
        "access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "test"),
        "secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "test"),
        "region": os.environ.get("AWS_REGION", "us-east-1"),
    }


@pytest.fixture
def integration_bucket(
    integration_endpoint: str, integration_credentials: dict[str, str]
) -> Iterator[str]:
    bucket = f"fsdk-{uuid.uuid4().hex[:12]}"
    boto3.client(
        "s3",
        endpoint_url=integration_endpoint,
        aws_access_key_id=integration_credentials["access_key_id"],
        aws_secret_access_key=integration_credentials["secret_access_key"],
        region_name=integration_credentials["region"],
    ).create_bucket(Bucket=bucket)
    yield bucket
    # No teardown — ephemeral server, vanishes with the CI job.


@pytest.fixture
def adapter(
    integration_endpoint: str,
    integration_bucket: str,
    integration_credentials: dict[str, str],
):
    from files_sdk_s3 import S3Adapter
    return S3Adapter(
        bucket=integration_bucket,
        endpoint_url=integration_endpoint,
        access_key_id=integration_credentials["access_key_id"],
        secret_access_key=integration_credentials["secret_access_key"],
        region=integration_credentials["region"],
    )


@pytest.fixture
def async_adapter(
    integration_endpoint: str,
    integration_bucket: str,
    integration_credentials: dict[str, str],
):
    from files_sdk_s3 import AsyncS3Adapter
    return AsyncS3Adapter(
        bucket=integration_bucket,
        endpoint_url=integration_endpoint,
        access_key_id=integration_credentials["access_key_id"],
        secret_access_key=integration_credentials["secret_access_key"],
        region=integration_credentials["region"],
    )
