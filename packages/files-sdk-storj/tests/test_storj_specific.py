import pytest
from files_sdk.errors import FilesError
from files_sdk_storj import AsyncStorjAdapter, StorjAdapter


def test_storj_defaults_to_global_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("STORJ_GATEWAY_REGION", raising=False)
    a = StorjAdapter(bucket="b")
    assert a._endpoint_url == "https://gateway.storjshare.io"
    assert a._gateway_region is None


def test_storj_regional_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    a = StorjAdapter(bucket="b", gateway_region="eu1")
    assert a._endpoint_url == "https://gateway.eu1.storjshare.io"
    assert a._gateway_region == "eu1"


def test_storj_public_url_without_base_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("STORJ_PUBLIC_URL_BASE", raising=False)
    a = StorjAdapter(bucket="b")
    with pytest.raises(FilesError) as ei:
        a.url("k", public=True)
    assert ei.value.code == "invalid_input"


def test_storj_public_url_with_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    a = StorjAdapter(
        bucket="b",
        public_url_base="https://link.storjshare.io/raw/abc",
    )
    assert a.url("hello.txt", public=True) == "https://link.storjshare.io/raw/abc/hello.txt"


def test_async_storj_defaults_to_global_gateway(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("STORJ_GATEWAY_REGION", raising=False)
    a = AsyncStorjAdapter(bucket="b")
    assert a._endpoint_url == "https://gateway.storjshare.io"


async def test_async_storj_public_url_without_base_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("STORJ_PUBLIC_URL_BASE", raising=False)
    a = AsyncStorjAdapter(bucket="b")
    with pytest.raises(FilesError) as ei:
        await a.url("k", public=True)
    assert ei.value.code == "invalid_input"


async def test_async_storj_public_url_with_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "s")
    a = AsyncStorjAdapter(
        bucket="b",
        public_url_base="https://link.storjshare.io/raw/abc",
    )
    assert await a.url("hello.txt", public=True) == "https://link.storjshare.io/raw/abc/hello.txt"


def test_storj_roundtrip_via_moto_endpoint(
    moto_endpoint: str,
    storj_bucket: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("STORJ_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("STORJ_SECRET_ACCESS_KEY", "testing")
    a = StorjAdapter(bucket=storj_bucket, _endpoint_override=moto_endpoint)
    a.upload("hello.txt", b"storj-roundtrip")
    sf = a.download("hello.txt")
    assert sf.data == b"storj-roundtrip"
