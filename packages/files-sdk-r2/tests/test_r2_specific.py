import pytest
from files_sdk.errors import FilesError
from files_sdk_r2 import AsyncR2Adapter, R2Adapter


def test_r2_requires_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    with pytest.raises(FilesError) as ei:
        R2Adapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_r2_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    a = R2Adapter(bucket="b")
    assert a._endpoint_url == "https://abc123.r2.cloudflarestorage.com"
    assert a._account_id == "abc123"


def test_r2_public_url_without_base_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("R2_PUBLIC_URL_BASE", raising=False)
    a = R2Adapter(bucket="b")
    with pytest.raises(FilesError) as ei:
        a.url("k", public=True)
    assert ei.value.code == "invalid_input"


def test_r2_public_url_with_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    a = R2Adapter(bucket="b", public_url_base="https://files.example.com")
    assert a.url("hello.txt", public=True) == "https://files.example.com/hello.txt"


def test_async_r2_requires_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncR2Adapter(bucket="b")
    assert ei.value.code == "unauthorized"
