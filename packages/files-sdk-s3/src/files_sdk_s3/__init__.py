"""files-sdk-s3 — Amazon S3 adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import S3Adapter
from .async_adapter import AsyncS3Adapter

try:
    __version__ = _pkg_version("files-sdk-s3")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncS3Adapter", "S3Adapter"]

if TYPE_CHECKING:
    # Tripwire: pyright structurally compares each impl against its Protocol
    # at type-check time. Without this, no callsite in the codebase pins a
    # concrete adapter to its Protocol slot, so signature drift between
    # Protocol and impl slips past the type checker (as the double-await
    # stream() bug did). Zero runtime cost.
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = S3Adapter
    _async_check: type[AsyncAdapter] = AsyncS3Adapter
