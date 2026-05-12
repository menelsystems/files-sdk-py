"""files-sdk-r2 — Cloudflare R2 adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import R2Adapter
from .async_adapter import AsyncR2Adapter

try:
    __version__ = _pkg_version("files-sdk-r2")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncR2Adapter", "R2Adapter"]

if TYPE_CHECKING:
    # See files_sdk_s3.__init__ for the rationale on this tripwire.
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = R2Adapter
    _async_check: type[AsyncAdapter] = AsyncR2Adapter
