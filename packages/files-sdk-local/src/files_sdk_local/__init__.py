"""files-sdk-local — local filesystem adapter."""

from typing import TYPE_CHECKING

from .adapter import LocalAdapter
from .async_adapter import AsyncLocalAdapter

__version__ = "0.1.0"
__all__ = ["AsyncLocalAdapter", "LocalAdapter"]

if TYPE_CHECKING:
    # See files_sdk_s3.__init__ for the rationale on this tripwire.
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = LocalAdapter
    _async_check: type[AsyncAdapter] = AsyncLocalAdapter
