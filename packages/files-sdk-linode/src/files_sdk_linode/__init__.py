"""files-sdk-linode — Linode Object Storage adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import LinodeAdapter
from .async_adapter import AsyncLinodeAdapter

try:
    __version__ = _pkg_version("files-sdk-linode")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncLinodeAdapter", "LinodeAdapter"]

if TYPE_CHECKING:
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = LinodeAdapter
    _async_check: type[AsyncAdapter] = AsyncLinodeAdapter
