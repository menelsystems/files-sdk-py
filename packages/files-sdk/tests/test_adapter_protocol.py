from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

from files_sdk.adapter import Adapter, AsyncAdapter
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile


class _DummySync:
    name = "dummy"

    def upload(self, key: str, body: Any, **opts: Any) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=0,
            etag=None,
            content_type=None,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
            metadata={},
        )

    def download(self, key: str) -> StoredFile:  # pragma: no cover
        raise NotImplementedError

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:  # pragma: no cover
        raise NotImplementedError

    def head(self, key: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def list(
        self, *, prefix: str | None = None, cursor: str | None = None, limit: int = 1000
    ) -> ListPage:  # pragma: no cover
        raise NotImplementedError

    def copy(self, src: str, dst: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    def url(
        self, key: str, *, expires_in: int = 3600, public: bool = False
    ) -> str:  # pragma: no cover
        raise NotImplementedError

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:  # pragma: no cover
        raise NotImplementedError

    @property
    def raw(self) -> Any:  # pragma: no cover
        return None


def test_sync_adapter_protocol_recognizes_compliant_class():
    assert isinstance(_DummySync(), Adapter)


class _DummyAsync:
    name = "dummy-async"

    async def upload(self, key: str, body: Any, **opts: Any) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=0,
            etag=None,
            content_type=None,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
            metadata={},
        )

    async def download(self, key: str) -> StoredFile:  # pragma: no cover
        raise NotImplementedError

    async def stream(
        self, key: str, *, chunk_size: int = 65536
    ) -> AsyncIterator[bytes]:  # pragma: no cover
        if False:
            yield b""
        raise NotImplementedError

    async def head(self, key: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    async def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    async def list(
        self, *, prefix: str | None = None, cursor: str | None = None, limit: int = 1000
    ) -> ListPage:  # pragma: no cover
        raise NotImplementedError

    async def copy(self, src: str, dst: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    async def url(
        self, key: str, *, expires_in: int = 3600, public: bool = False
    ) -> str:  # pragma: no cover
        raise NotImplementedError

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:  # pragma: no cover
        raise NotImplementedError

    @property
    def raw(self) -> Any:  # pragma: no cover
        return None


def test_async_adapter_protocol_recognizes_async_class():
    assert isinstance(_DummyAsync(), AsyncAdapter)


def test_is_async_adapter_helper_distinguishes():
    from files_sdk.adapter import is_async_adapter

    assert not is_async_adapter(_DummySync())
    assert is_async_adapter(_DummyAsync())
