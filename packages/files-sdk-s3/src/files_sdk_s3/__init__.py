"""files-sdk-s3 — Amazon S3 adapter."""

from typing import TYPE_CHECKING

from .adapter import S3Adapter
from .async_adapter import AsyncS3Adapter

__version__ = "0.1.0"
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
