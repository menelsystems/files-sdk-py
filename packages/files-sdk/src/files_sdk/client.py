"""Files and AsyncFiles client wrappers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from ._registry import load_adapter_class
from .adapter import Adapter, AsyncAdapter, is_async_adapter
from .errors import FilesError
from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


class Files:
    """Synchronous storage client wrapping a sync :class:`Adapter`."""

    def __init__(self, *, adapter: Adapter) -> None:
        if is_async_adapter(adapter):
            raise FilesError(
                code="invalid_input",
                message="Files() requires a sync Adapter; pass async adapter to AsyncFiles instead",
            )
        self._adapter = adapter

    @classmethod
    def from_name(cls, name: str, **adapter_kwargs: Any) -> Files:
        adapter_cls = load_adapter_class(name)
        return cls(adapter=adapter_cls(**adapter_kwargs))

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return self._adapter.upload(key, body, **opts)

    def download(self, key: str) -> StoredFile:
        return self._adapter.download(key)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        return self._adapter.stream(key, chunk_size=chunk_size)

    def head(self, key: str) -> FileMetadata:
        return self._adapter.head(key)

    def delete(self, key: str) -> None:
        self._adapter.delete(key)

    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        return self._adapter.list(prefix=prefix, cursor=cursor, limit=limit)

    def copy(self, src: str, dst: str) -> FileMetadata:
        return self._adapter.copy(src, dst)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return self._adapter.url(key, expires_in=expires_in, public=public)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return self._adapter.signed_upload_url(key, **opts)

    @property
    def raw(self) -> Any:
        return self._adapter.raw


class AsyncFiles:
    """Asynchronous storage client wrapping an :class:`AsyncAdapter`."""

    def __init__(self, *, adapter: AsyncAdapter) -> None:
        if not is_async_adapter(adapter):
            raise FilesError(
                code="invalid_input",
                message="AsyncFiles() requires an async AsyncAdapter; pass sync adapter to Files instead",
            )
        self._adapter = adapter

    @classmethod
    def from_name(cls, name: str, **adapter_kwargs: Any) -> AsyncFiles:
        adapter_cls = load_adapter_class(name)
        return cls(adapter=adapter_cls(**adapter_kwargs))

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return await self._adapter.upload(key, body, **opts)

    async def download(self, key: str) -> StoredFile:
        return await self._adapter.download(key)

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        return await self._adapter.stream(key, chunk_size=chunk_size)  # type: ignore[no-any-return]

    async def head(self, key: str) -> FileMetadata:
        return await self._adapter.head(key)

    async def delete(self, key: str) -> None:
        await self._adapter.delete(key)

    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        return await self._adapter.list(prefix=prefix, cursor=cursor, limit=limit)

    async def copy(self, src: str, dst: str) -> FileMetadata:
        return await self._adapter.copy(src, dst)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return await self._adapter.url(key, expires_in=expires_in, public=public)

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return await self._adapter.signed_upload_url(key, **opts)

    @property
    def raw(self) -> Any:
        return self._adapter.raw
