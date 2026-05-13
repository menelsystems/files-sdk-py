import pytest
from files_sdk.errors import FilesError
from files_sdk_digitalocean import AsyncDigitalOceanAdapter, DigitalOceanAdapter


def test_do_requires_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DO_SPACES_REGION", raising=False)
    with pytest.raises(FilesError) as ei:
        DigitalOceanAdapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_do_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DO_SPACES_REGION", "nyc3")
    monkeypatch.setenv("DO_SPACES_KEY", "k")
    monkeypatch.setenv("DO_SPACES_SECRET", "s")
    a = DigitalOceanAdapter(bucket="b")
    assert a._endpoint_url == "https://nyc3.digitaloceanspaces.com"
    assert a._region == "nyc3"


def test_do_default_public_url_uses_virtual_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DO_SPACES_REGION", "sfo3")
    monkeypatch.setenv("DO_SPACES_KEY", "k")
    monkeypatch.setenv("DO_SPACES_SECRET", "s")
    monkeypatch.delenv("DO_SPACES_PUBLIC_URL_BASE", raising=False)
    a = DigitalOceanAdapter(bucket="my-space")
    assert (
        a.url("hello.txt", public=True) == "https://my-space.sfo3.digitaloceanspaces.com/hello.txt"
    )


def test_do_public_url_with_base_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DO_SPACES_REGION", "fra1")
    monkeypatch.setenv("DO_SPACES_KEY", "k")
    monkeypatch.setenv("DO_SPACES_SECRET", "s")
    a = DigitalOceanAdapter(bucket="b", public_url_base="https://cdn.example.com")
    assert a.url("hello.txt", public=True) == "https://cdn.example.com/hello.txt"


def test_async_do_requires_region(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DO_SPACES_REGION", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncDigitalOceanAdapter(bucket="b")
    assert ei.value.code == "unauthorized"


def test_do_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    do_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DO_SPACES_REGION", "nyc3")
    monkeypatch.setenv("DO_SPACES_KEY", "testing")
    monkeypatch.setenv("DO_SPACES_SECRET", "testing")
    a = DigitalOceanAdapter(bucket=do_bucket, _endpoint_override=moto_endpoint)
    a.upload("hello.txt", b"do-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"do-roundtrip"
