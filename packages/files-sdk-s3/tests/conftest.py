"""Fixtures for files-sdk-s3 tests.

Uses moto (https://github.com/getmoto/moto) to mock S3 in-process.
"""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def s3_bucket(aws_credentials: None):
    with mock_aws():
        bucket = "conformance-bucket"
        boto3.client("s3").create_bucket(Bucket=bucket)
        yield bucket


@pytest.fixture
def adapter(s3_bucket: str):
    from files_sdk_s3 import S3Adapter
    return S3Adapter(bucket=s3_bucket)
