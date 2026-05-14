import pytest
from files_sdk.errors import FilesError
from files_sdk_linode import AsyncLinodeAdapter, LinodeAdapter


def test_linode_requires_cluster(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINODE_CLUSTER", raising=False)
    with pytest.raises(FilesError) as ei:
        LinodeAdapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_linode_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINODE_CLUSTER", "us-east-1")
    monkeypatch.setenv("LINODE_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("LINODE_SECRET_ACCESS_KEY", "s")
    a = LinodeAdapter(bucket="b")
    assert a._endpoint_url == "https://us-east-1.linodeobjects.com"
    assert a._cluster == "us-east-1"


def test_linode_default_public_url_uses_virtual_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINODE_CLUSTER", "eu-central-1")
    monkeypatch.setenv("LINODE_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("LINODE_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("LINODE_PUBLIC_URL_BASE", raising=False)
    a = LinodeAdapter(bucket="my-bucket")
    assert (
        a.url("hello.txt", public=True)
        == "https://my-bucket.eu-central-1.linodeobjects.com/hello.txt"
    )


def test_linode_public_url_with_base_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LINODE_CLUSTER", "ap-south-1")
    monkeypatch.setenv("LINODE_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("LINODE_SECRET_ACCESS_KEY", "s")
    a = LinodeAdapter(bucket="b", public_url_base="https://cdn.example.com")
    assert a.url("hello.txt", public=True) == "https://cdn.example.com/hello.txt"


def test_async_linode_requires_cluster(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LINODE_CLUSTER", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncLinodeAdapter(bucket="b")
    assert ei.value.code == "unauthorized"


def test_linode_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    linode_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LINODE_CLUSTER", "us-east-1")
    monkeypatch.setenv("LINODE_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("LINODE_SECRET_ACCESS_KEY", "testing")
    a = LinodeAdapter(bucket=linode_bucket, _endpoint_override=moto_endpoint)
    a.upload("hello.txt", b"linode-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"linode-roundtrip"
