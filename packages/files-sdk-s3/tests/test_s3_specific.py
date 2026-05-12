import boto3
import pytest

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


def test_s3_adapter_raises_unauthorized_without_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    with pytest.raises(FilesError) as ei:
        S3Adapter()
    assert ei.value.code == "unauthorized"


def test_s3_adapter_reads_bucket_from_env(
    aws_credentials: None,
    moto_endpoint: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    boto3.client("s3", endpoint_url=moto_endpoint).create_bucket(Bucket="env-bucket")
    a = S3Adapter(endpoint_url=moto_endpoint, region="us-east-1")
    assert a.bucket == "env-bucket"
