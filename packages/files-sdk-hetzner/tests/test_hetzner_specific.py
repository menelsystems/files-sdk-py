import pytest
from files_sdk.errors import FilesError
from files_sdk_hetzner import AsyncHetznerAdapter, HetznerAdapter


def test_hetzner_requires_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HETZNER_REGION", raising=False)
    with pytest.raises(FilesError) as ei:
        HetznerAdapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_hetzner_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HETZNER_REGION", "fsn1")
    monkeypatch.setenv("HETZNER_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("HETZNER_SECRET_ACCESS_KEY", "s")
    a = HetznerAdapter(bucket="b")
    assert a._endpoint_url == "https://fsn1.your-objectstorage.com"
    assert a._region == "fsn1"


def test_hetzner_default_public_url_uses_virtual_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HETZNER_REGION", "nbg1")
    monkeypatch.setenv("HETZNER_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("HETZNER_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("HETZNER_PUBLIC_URL_BASE", raising=False)
    a = HetznerAdapter(bucket="my-bucket")
    assert (
        a.url("hello.txt", public=True) == "https://my-bucket.nbg1.your-objectstorage.com/hello.txt"
    )


def test_hetzner_public_url_with_base_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HETZNER_REGION", "hel1")
    monkeypatch.setenv("HETZNER_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("HETZNER_SECRET_ACCESS_KEY", "s")
    a = HetznerAdapter(bucket="b", public_url_base="https://files.example.com")
    assert a.url("hello.txt", public=True) == "https://files.example.com/hello.txt"


def test_async_hetzner_requires_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HETZNER_REGION", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncHetznerAdapter(bucket="b")
    assert ei.value.code == "unauthorized"


def test_hetzner_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    hetzner_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HETZNER_REGION", "fsn1")
    monkeypatch.setenv("HETZNER_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("HETZNER_SECRET_ACCESS_KEY", "testing")
    a = HetznerAdapter(bucket=hetzner_bucket, _endpoint_override=moto_endpoint)
    a.upload("hello.txt", b"hetzner-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"hetzner-roundtrip"
