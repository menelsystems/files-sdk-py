"""Stub Vercel adapter — claim this in CLAIM.md and implement."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

_NOT_IMPLEMENTED = "files-sdk-vercel is a stub. See packages/files-sdk-vercel/CLAIM.md to claim it."


class VercelAdapter:
    name: ClassVar[str] = "vercel"

    def __init__(self, **_: Any) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def download(self, key: str) -> StoredFile:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def head(self, key: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def delete(self, key: str) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list(
        self, *, prefix: str | None = None, cursor: str | None = None, limit: int = 1000
    ) -> ListPage:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def copy(self, src: str, dst: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @property
    def raw(self) -> Any:
        raise NotImplementedError(_NOT_IMPLEMENTED)
