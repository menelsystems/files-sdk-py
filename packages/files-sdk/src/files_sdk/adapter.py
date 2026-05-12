"""Protocol interfaces every adapter must implement."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Iterator
from typing import Any, ClassVar, Protocol, runtime_checkable

from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


@runtime_checkable
class Adapter(Protocol):
    """Synchronous storage adapter."""

    name: ClassVar[str]

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata: ...
    def download(self, key: str) -> StoredFile: ...
    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]: ...
    def head(self, key: str) -> FileMetadata: ...
    def delete(self, key: str) -> None: ...
    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage: ...
    def copy(self, src: str, dst: str) -> FileMetadata: ...
    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str: ...
    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload: ...

    @property
    def raw(self) -> Any: ...


@runtime_checkable
class AsyncAdapter(Protocol):
    """Asynchronous storage adapter.

    Methods mirror :class:`Adapter` but are coroutines. ``stream`` returns an
    async iterator.
    """

    name: ClassVar[str]

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata: ...
    async def download(self, key: str) -> StoredFile: ...
    def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]: ...
    async def head(self, key: str) -> FileMetadata: ...
    async def delete(self, key: str) -> None: ...
    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage: ...
    async def copy(self, src: str, dst: str) -> FileMetadata: ...
    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str: ...
    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload: ...

    @property
    def raw(self) -> Any: ...


def is_async_adapter(candidate: object) -> bool:
    """Return True iff candidate looks like an AsyncAdapter (upload is a coroutine)."""
    fn = getattr(candidate, "upload", None)
    return inspect.iscoroutinefunction(fn)
