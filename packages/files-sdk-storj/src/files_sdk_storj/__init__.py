"""files-sdk-storj — Storj DCS adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import StorjAdapter
from .async_adapter import AsyncStorjAdapter

try:
    __version__ = _pkg_version("files-sdk-storj")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncStorjAdapter", "StorjAdapter"]

if TYPE_CHECKING:
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = StorjAdapter
    _async_check: type[AsyncAdapter] = AsyncStorjAdapter
