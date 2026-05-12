"""Conformance tests every Adapter implementation should pass.

Adapter packages add a ``conftest.py`` providing an ``adapter`` fixture, then in
``tests/test_conformance.py``::

    from files_sdk.testing.conformance import *  # noqa: F401,F403

pytest discovers each ``test_*`` function and binds the local fixture.
"""

from __future__ import annotations

import io
import uuid

import pytest

from files_sdk.errors import FilesError

__all__ = [
    "test_upload_then_download_bytes",
    "test_upload_then_download_str",
    "test_upload_from_file_like",
    "test_head_returns_metadata",
    "test_delete_is_idempotent",
    "test_download_missing_raises_not_found",
    "test_list_prefix_filters",
    "test_list_pagination_cursor",
    "test_copy_creates_destination",
    "test_url_returns_http_string",
    "test_signed_upload_url_put",
    "test_stream_yields_chunks",
    "test_unicode_key_roundtrip",
    "test_zero_byte_upload",
]


def _k(prefix: str = "conf") -> str:
    return f"{prefix}/{uuid.uuid4().hex}"


def test_upload_then_download_bytes(adapter) -> None:
    k = _k()
    adapter.upload(k, b"hello")
    sf = adapter.download(k)
    assert sf.data == b"hello"
    assert sf.metadata.key == k


def test_upload_then_download_str(adapter) -> None:
    k = _k()
    adapter.upload(k, "héllo")
    sf = adapter.download(k)
    assert sf.text() == "héllo"


def test_upload_from_file_like(adapter) -> None:
    k = _k()
    adapter.upload(k, io.BytesIO(b"file-like"))
    assert adapter.download(k).data == b"file-like"


def test_head_returns_metadata(adapter) -> None:
    k = _k()
    adapter.upload(k, b"abc", content_type="text/plain")
    meta = adapter.head(k)
    assert meta.size == 3
    assert meta.content_type == "text/plain"


def test_delete_is_idempotent(adapter) -> None:
    k = _k()
    adapter.delete(k)  # missing -> no raise
    adapter.upload(k, b"x")
    adapter.delete(k)
    adapter.delete(k)  # already gone -> no raise


def test_download_missing_raises_not_found(adapter) -> None:
    with pytest.raises(FilesError) as ei:
        adapter.download(_k("nope"))
    assert ei.value.code == "not_found"


def test_list_prefix_filters(adapter) -> None:
    p = f"listtest/{uuid.uuid4().hex}"
    for i in range(3):
        adapter.upload(f"{p}/f{i}.txt", b"x")
    adapter.upload(f"{p}-other/f.txt", b"y")
    page = adapter.list(prefix=f"{p}/")
    keys = {item.key for item in page.items}
    assert len(keys) >= 3
    assert all(k.startswith(f"{p}/") for k in keys)


def test_list_pagination_cursor(adapter) -> None:
    p = f"paging/{uuid.uuid4().hex}"
    for i in range(5):
        adapter.upload(f"{p}/{i:02d}.txt", b"x")
    page1 = adapter.list(prefix=f"{p}/", limit=2)
    assert len(page1.items) == 2
    if page1.cursor is not None:
        page2 = adapter.list(prefix=f"{p}/", cursor=page1.cursor, limit=2)
        first_keys = {i.key for i in page1.items}
        second_keys = {i.key for i in page2.items}
        assert first_keys.isdisjoint(second_keys)


def test_copy_creates_destination(adapter) -> None:
    src, dst = _k("src"), _k("dst")
    adapter.upload(src, b"copy-me")
    adapter.copy(src, dst)
    assert adapter.download(dst).data == b"copy-me"


def test_url_returns_http_string(adapter) -> None:
    k = _k()
    adapter.upload(k, b"x")
    url = adapter.url(k, expires_in=60)
    # Most adapters return http(s); LocalAdapter returns file:// — both acceptable.
    assert url.startswith(("http", "file://"))


def test_signed_upload_url_put(adapter) -> None:
    # Adapters can opt out by setting the class attribute supports_signed_upload = False
    # (e.g., LocalAdapter, where there's no signing authority). Default is True.
    if not getattr(adapter, "supports_signed_upload", True):
        pytest.skip("adapter does not support signed_upload_url")
    su = adapter.signed_upload_url(_k(), method="put")
    assert su.method == "PUT"
    assert su.url.startswith("http")


def test_stream_yields_chunks(adapter) -> None:
    k = _k()
    payload = b"abcdefghij" * 1000
    adapter.upload(k, payload)
    got = b"".join(adapter.stream(k, chunk_size=256))
    assert got == payload


def test_unicode_key_roundtrip(adapter) -> None:
    k = f"unicode/{uuid.uuid4().hex}/héllo wörld.txt"
    adapter.upload(k, b"x")
    assert adapter.download(k).data == b"x"


def test_zero_byte_upload(adapter) -> None:
    k = _k()
    adapter.upload(k, b"")
    sf = adapter.download(k)
    assert sf.data == b""
    assert sf.metadata.size == 0
