"""Async local adapter — wraps sync I/O in asyncio.to_thread."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

from ._storage import _LocalStorage


class AsyncLocalAdapter:
    """Async local filesystem adapter."""

    name: ClassVar[str] = "local-async"
    supports_signed_upload: ClassVar[bool] = False

    def __init__(self, root: str | Path, *, public_url_base: str | None = None) -> None:
        self._storage = _LocalStorage(root, public_url_base=public_url_base)

    @property
    def root(self) -> Path:
        return self._storage.root

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return await asyncio.to_thread(self._storage.upload, key, body, **opts)

    async def download(self, key: str) -> StoredFile:
        return await asyncio.to_thread(self._storage.download, key)

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        # Eagerly read into memory in a worker thread, then yield from memory.
        # For very large files, a chunked thread-based generator would be better;
        # acceptable tradeoff for v0.
        async def gen() -> AsyncIterator[bytes]:
            chunks = await asyncio.to_thread(
                lambda: list(self._storage.stream(key, chunk_size=chunk_size))
            )
            for c in chunks:
                yield c

        return gen()

    async def head(self, key: str) -> FileMetadata:
        return await asyncio.to_thread(self._storage.head, key)

    async def delete(self, key: str) -> None:
        await asyncio.to_thread(self._storage.delete, key)

    async def list(
        self, *, prefix: str | None = None, cursor: str | None = None, limit: int = 1000
    ) -> ListPage:
        return await asyncio.to_thread(
            self._storage.list,
            prefix=prefix,
            cursor=cursor,
            limit=limit,
        )

    async def copy(self, src: str, dst: str) -> FileMetadata:
        return await asyncio.to_thread(self._storage.copy, src, dst)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return await asyncio.to_thread(
            self._storage.url,
            key,
            expires_in=expires_in,
            public=public,
        )

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return await asyncio.to_thread(self._storage.signed_upload_url, key, **opts)

    @property
    def raw(self) -> Any:
        return self._storage
