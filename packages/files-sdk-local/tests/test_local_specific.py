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


async def test_async_stream_is_chunked_not_buffered(tmp_path: Path) -> None:
    """An 8 MB file must not be buffered whole before yielding chunks.

    Regression test for the v0 impl which did
    `list(self._storage.stream(...))` in a worker thread — that materialised
    the entire file in memory before the first chunk reached the consumer.
    The current impl pumps one chunk per `asyncio.to_thread(next, ...)`, so
    peak Python heap stays at roughly one chunk regardless of file size.
    """
    import tracemalloc

    a = AsyncLocalAdapter(root=tmp_path / "store")
    payload_size = 8 * 1024 * 1024
    chunk_size = 64 * 1024
    key = "big.bin"

    # Write the file directly through the filesystem to avoid measuring
    # the upload path's memory profile in the same tracemalloc window.
    target = a.root / key
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"\0" * payload_size)

    tracemalloc.start()
    chunks_seen = 0
    async for chunk in a.stream(key, chunk_size=chunk_size):
        chunks_seen += 1
        del chunk  # drop reference so it can be reclaimed before the next iter
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    assert chunks_seen == payload_size // chunk_size, (
        f"expected {payload_size // chunk_size} chunks, got {chunks_seen}"
    )
    # A buffered impl would peak around 8 MB. Chunked impl should peak in the
    # tens-to-low-hundreds of KB. 8x chunk_size (= 512 KB) is a generous ceiling
    # that still catches the regression by a factor of 16.
    max_acceptable = 8 * chunk_size
    assert peak < max_acceptable, (
        f"peak memory {peak:,} exceeds {max_acceptable:,} for {payload_size:,}-byte file — likely buffering"
    )
