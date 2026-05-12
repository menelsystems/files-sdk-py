"""Synchronous local filesystem adapter."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

from ._storage import _LocalStorage


class LocalAdapter:
    """Filesystem-backed storage adapter.

    Stores objects under ``root/<key>`` with sidecar JSON metadata under
    ``root/.files-sdk-meta/<key>.json``.
    """

    name: ClassVar[str] = "local"
    supports_signed_upload: ClassVar[bool] = False

    def __init__(self, root: str | Path, *, public_url_base: str | None = None) -> None:
        self._storage = _LocalStorage(root, public_url_base=public_url_base)

    @property
    def root(self) -> Path:
        return self._storage.root

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return self._storage.upload(key, body, **opts)

    def download(self, key: str) -> StoredFile:
        return self._storage.download(key)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        return self._storage.stream(key, chunk_size=chunk_size)

    def head(self, key: str) -> FileMetadata:
        return self._storage.head(key)

    def delete(self, key: str) -> None:
        self._storage.delete(key)

    def list(self, *, prefix: str | None = None, cursor: str | None = None,
             limit: int = 1000) -> ListPage:
        return self._storage.list(prefix=prefix, cursor=cursor, limit=limit)

    def copy(self, src: str, dst: str) -> FileMetadata:
        return self._storage.copy(src, dst)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return self._storage.url(key, expires_in=expires_in, public=public)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return self._storage.signed_upload_url(key, **opts)

    @property
    def raw(self) -> Any:
        return self._storage
