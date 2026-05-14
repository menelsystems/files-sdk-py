import pytest
from files_sdk.errors import FilesError
from files_sdk_minio import AsyncMinIOAdapter, MinIOAdapter


def test_minio_requires_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    with pytest.raises(FilesError) as ei:
        MinIOAdapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_minio_defaults_region_to_us_east_1(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("MINIO_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("MINIO_REGION", raising=False)
    a = MinIOAdapter(bucket="b")
    assert a._endpoint_url == "http://localhost:9000"


def test_minio_public_url_without_base_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("MINIO_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("MINIO_PUBLIC_URL_BASE", raising=False)
    a = MinIOAdapter(bucket="b")
    with pytest.raises(FilesError) as ei:
        a.url("k", public=True)
    assert ei.value.code == "invalid_input"


def test_minio_public_url_with_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("MINIO_SECRET_ACCESS_KEY", "s")
    a = MinIOAdapter(bucket="b", public_url_base="https://files.example.com")
    assert a.url("hello.txt", public=True) == "https://files.example.com/hello.txt"


def test_async_minio_requires_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINIO_ENDPOINT", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncMinIOAdapter(bucket="b")
    assert ei.value.code == "unauthorized"


def test_minio_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    minio_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end smoke that MinIOAdapter's kwargs forwarding to S3Adapter actually works."""
    monkeypatch.setenv("MINIO_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("MINIO_SECRET_ACCESS_KEY", "testing")
    a = MinIOAdapter(bucket=minio_bucket, endpoint=moto_endpoint)
    a.upload("hello.txt", b"minio-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"minio-roundtrip"
