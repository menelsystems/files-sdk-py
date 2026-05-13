import pytest
from files_sdk.errors import FilesError
from files_sdk_akamai import AkamaiAdapter, AsyncAkamaiAdapter


def test_akamai_requires_cluster(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AKAMAI_CLUSTER", raising=False)
    with pytest.raises(FilesError) as ei:
        AkamaiAdapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_akamai_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKAMAI_CLUSTER", "us-east-1")
    monkeypatch.setenv("AKAMAI_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("AKAMAI_SECRET_ACCESS_KEY", "s")
    a = AkamaiAdapter(bucket="b")
    assert a._endpoint_url == "https://us-east-1.linodeobjects.com"
    assert a._cluster == "us-east-1"


def test_akamai_default_public_url_uses_virtual_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKAMAI_CLUSTER", "eu-central-1")
    monkeypatch.setenv("AKAMAI_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("AKAMAI_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("AKAMAI_PUBLIC_URL_BASE", raising=False)
    a = AkamaiAdapter(bucket="my-bucket")
    assert (
        a.url("hello.txt", public=True)
        == "https://my-bucket.eu-central-1.linodeobjects.com/hello.txt"
    )


def test_akamai_public_url_with_base_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AKAMAI_CLUSTER", "ap-south-1")
    monkeypatch.setenv("AKAMAI_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("AKAMAI_SECRET_ACCESS_KEY", "s")
    a = AkamaiAdapter(bucket="b", public_url_base="https://cdn.example.com")
    assert a.url("hello.txt", public=True) == "https://cdn.example.com/hello.txt"


def test_async_akamai_requires_cluster(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AKAMAI_CLUSTER", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncAkamaiAdapter(bucket="b")
    assert ei.value.code == "unauthorized"


def test_akamai_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    akamai_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AKAMAI_CLUSTER", "us-east-1")
    monkeypatch.setenv("AKAMAI_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AKAMAI_SECRET_ACCESS_KEY", "testing")
    a = AkamaiAdapter(bucket=akamai_bucket, _endpoint_override=moto_endpoint)
    a.upload("hello.txt", b"akamai-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"akamai-roundtrip"
