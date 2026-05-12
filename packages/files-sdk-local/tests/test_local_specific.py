"""LocalAdapter-specific behavior: path safety, file:// urls, signed-upload opt-out."""

from __future__ import annotations

from pathlib import Path

import pytest
from files_sdk.errors import FilesError
from files_sdk_local import AsyncLocalAdapter, LocalAdapter


def test_creates_root_if_missing(tmp_path: Path) -> None:
    root = tmp_path / "nested" / "store"
    assert not root.exists()
    LocalAdapter(root=root)
    assert root.is_dir()


def test_rejects_absolute_key(tmp_path: Path) -> None:
    a = LocalAdapter(root=tmp_path)
    with pytest.raises(FilesError) as ei:
        a.upload("/etc/passwd", b"x")
    assert ei.value.code == "invalid_input"


def test_rejects_escaping_key(tmp_path: Path) -> None:
    a = LocalAdapter(root=tmp_path / "store")
    with pytest.raises(FilesError) as ei:
        a.upload("../escape.txt", b"x")
    assert ei.value.code == "invalid_input"


def test_url_returns_file_uri_when_not_public(tmp_path: Path) -> None:
    a = LocalAdapter(root=tmp_path)
    a.upload("k.txt", b"x")
    url = a.url("k.txt")
    assert url.startswith("file://")
    assert "k.txt" in url


def test_url_public_requires_base(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("FILES_SDK_LOCAL_PUBLIC_URL_BASE", raising=False)
    a = LocalAdapter(root=tmp_path)
    a.upload("k.txt", b"x")
    with pytest.raises(FilesError) as ei:
        a.url("k.txt", public=True)
    assert ei.value.code == "invalid_input"


def test_url_public_with_base(tmp_path: Path) -> None:
    a = LocalAdapter(root=tmp_path, public_url_base="https://files.example.com")
    a.upload("k.txt", b"x")
    assert a.url("k.txt", public=True) == "https://files.example.com/k.txt"


def test_signed_upload_opted_out(tmp_path: Path) -> None:
    a = LocalAdapter(root=tmp_path)
    assert a.supports_signed_upload is False
    with pytest.raises(FilesError) as ei:
        a.signed_upload_url("k.txt", method="put")
    assert ei.value.code == "invalid_input"


def test_async_supports_signed_upload_is_false(tmp_path: Path) -> None:
    a = AsyncLocalAdapter(root=tmp_path)
    assert a.supports_signed_upload is False
