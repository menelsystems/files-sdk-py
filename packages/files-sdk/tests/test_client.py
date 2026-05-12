from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from files_sdk import AsyncFiles, Files
from files_sdk.errors import FilesError
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile


def _meta(key: str = "k") -> FileMetadata:
    return FileMetadata(
        key=key,
        size=0,
        etag=None,
        content_type=None,
        last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        metadata={},
    )


class FakeSyncAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []
        self._raw = object()

    def _record(self, op: str, *args: Any, **kw: Any) -> None:
        self.calls.append((op, args, kw))

    def upload(self, key, body, **opts):
        self._record("upload", key, body, **opts)
        return _meta(key)

    def download(self, key):
        self._record("download", key)
        return StoredFile(metadata=_meta(key), data=b"x")

    def stream(self, key, *, chunk_size=65536):
        self._record("stream", key, chunk_size=chunk_size)
        return iter([b"x"])

    def head(self, key):
        self._record("head", key)
        return _meta(key)

    def delete(self, key):
        self._record("delete", key)

    def list(self, *, prefix=None, cursor=None, limit=1000):
        self._record("list", prefix=prefix, cursor=cursor, limit=limit)
        return ListPage(items=[], cursor=None)

    def copy(self, src, dst):
        self._record("copy", src, dst)
        return _meta(dst)

    def url(self, key, *, expires_in=3600, public=False):
        self._record("url", key, expires_in=expires_in, public=public)
        return f"https://example/{key}"

    def signed_upload_url(self, key, **opts):
        self._record("signed_upload_url", key, **opts)
        return SignedUpload(
            url="https://x",
            method="PUT",
            headers={},
            fields=None,
            expires_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    @property
    def raw(self):
        return self._raw


class FakeAsyncAdapter:
    name = "fake-async"

    async def upload(self, key, body, **opts):
        return _meta(key)

    async def download(self, key):
        return StoredFile(metadata=_meta(key), data=b"x")

    def stream(self, key, *, chunk_size=65536) -> AsyncIterator[bytes]:
        async def gen() -> AsyncIterator[bytes]:
            yield b"x"

        return gen()

    async def head(self, key):
        return _meta(key)

    async def delete(self, key):
        return None

    async def list(self, *, prefix=None, cursor=None, limit=1000):
        return ListPage(items=[], cursor=None)

    async def copy(self, src, dst):
        return _meta(dst)

    async def url(self, key, *, expires_in=3600, public=False):
        return f"https://example/{key}"

    async def signed_upload_url(self, key, **opts):
        return SignedUpload(
            url="https://x",
            method="PUT",
            headers={},
            fields=None,
            expires_at=datetime(2026, 1, 1, tzinfo=UTC),
        )

    @property
    def raw(self):
        return object()


def test_files_delegates_all_methods():
    adapter = FakeSyncAdapter()
    files = Files(adapter=adapter)
    files.upload("k", b"hi", content_type="text/plain")
    files.download("k")
    list(files.stream("k", chunk_size=1024))
    files.head("k")
    files.delete("k")
    files.list(prefix="p/")
    files.copy("a", "b")
    files.url("k", expires_in=60, public=True)
    files.signed_upload_url("k", method="put")
    assert {c[0] for c in adapter.calls} == {
        "upload",
        "download",
        "stream",
        "head",
        "delete",
        "list",
        "copy",
        "url",
        "signed_upload_url",
    }


def test_files_rejects_async_adapter():
    with pytest.raises(FilesError) as ei:
        Files(adapter=FakeAsyncAdapter())
    assert ei.value.code == "invalid_input"
    assert "async" in ei.value.message.lower()


def test_files_raw_property():
    adapter = FakeSyncAdapter()
    files = Files(adapter=adapter)
    assert files.raw is adapter.raw


@pytest.mark.asyncio
async def test_async_files_delegates():
    files = AsyncFiles(adapter=FakeAsyncAdapter())
    meta = await files.upload("k", b"hi")
    assert meta.key == "k"
    sf = await files.download("k")
    assert sf.data == b"x"
    async for chunk in files.stream("k"):
        assert chunk == b"x"


def test_async_files_rejects_sync_adapter():
    with pytest.raises(FilesError) as ei:
        AsyncFiles(adapter=FakeSyncAdapter())
    assert ei.value.code == "invalid_input"


def test_files_from_name_loads_via_registry():
    class FakeAdapter(FakeSyncAdapter):
        def __init__(self, *, bucket: str) -> None:
            super().__init__()
            self.bucket = bucket

    with patch("files_sdk.client.load_adapter_class") as mocked:
        mocked.return_value = FakeAdapter
        files = Files.from_name("fake", bucket="my-bucket")
    assert isinstance(files._adapter, FakeAdapter)
    assert files._adapter.bucket == "my-bucket"


def test_files_from_name_rejects_async_adapter():
    with patch("files_sdk.client.load_adapter_class") as mocked:
        mocked.return_value = FakeAsyncAdapter
        with pytest.raises(FilesError) as ei:
            Files.from_name("fake-async")
    assert ei.value.code == "invalid_input"
    assert "async" in ei.value.message.lower()


def test_async_files_from_name_loads_via_registry():
    with patch("files_sdk.client.load_adapter_class") as mocked:
        mocked.return_value = FakeAsyncAdapter
        files = AsyncFiles.from_name("fake-async")
    assert isinstance(files._adapter, FakeAsyncAdapter)


def test_async_files_from_name_rejects_sync_adapter():
    with patch("files_sdk.client.load_adapter_class") as mocked:
        mocked.return_value = FakeSyncAdapter
        with pytest.raises(FilesError) as ei:
            AsyncFiles.from_name("fake")
    assert ei.value.code == "invalid_input"
    assert "sync" in ei.value.message.lower()
