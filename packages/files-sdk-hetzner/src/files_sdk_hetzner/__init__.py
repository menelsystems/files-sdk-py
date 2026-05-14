"""files-sdk-hetzner — Hetzner Object Storage adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import HetznerAdapter
from .async_adapter import AsyncHetznerAdapter

try:
    __version__ = _pkg_version("files-sdk-hetzner")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncHetznerAdapter", "HetznerAdapter"]

if TYPE_CHECKING:
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = HetznerAdapter
    _async_check: type[AsyncAdapter] = AsyncHetznerAdapter
