import os

import pytest
from moto import mock_aws

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


def test_s3_adapter_raises_unauthorized_without_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    with pytest.raises(FilesError) as ei:
        S3Adapter()
    assert ei.value.code == "unauthorized"


def test_s3_adapter_reads_bucket_from_env(aws_credentials: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    with mock_aws():
        import boto3
        boto3.client("s3").create_bucket(Bucket="env-bucket")
        a = S3Adapter()
    assert a.bucket == "env-bucket"
