"""Public pydantic models returned by adapters."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

UploadBody = Union[bytes, str, BinaryIO, Path]


class FileMetadata(BaseModel):
    """Metadata for a stored object."""

    model_config = ConfigDict(frozen=True)

    key: str
    size: int = Field(ge=0)
    etag: str | None
    content_type: str | None
    last_modified: datetime
    metadata: dict[str, str]


class StoredFile(BaseModel):
    """A fully-buffered downloaded file."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    metadata: FileMetadata
    data: bytes

    def as_bytes(self) -> bytes:
        return self.data

    def text(self, *, encoding: str = "utf-8", errors: str = "strict") -> str:
        return self.data.decode(encoding, errors=errors)


class ListPage(BaseModel):
    """One page of a list operation."""

    items: list[FileMetadata]
    cursor: str | None


class SignedUpload(BaseModel):
    """A signed-URL contract for a browser-direct upload."""

    url: str
    method: Literal["PUT", "POST"]
    headers: dict[str, str]
    fields: dict[str, str] | None
    expires_at: datetime
