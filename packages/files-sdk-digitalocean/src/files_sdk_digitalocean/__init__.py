"""files-sdk-digitalocean — DigitalOcean Spaces adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import DigitalOceanAdapter
from .async_adapter import AsyncDigitalOceanAdapter

try:
    __version__ = _pkg_version("files-sdk-digitalocean")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncDigitalOceanAdapter", "DigitalOceanAdapter"]

if TYPE_CHECKING:
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = DigitalOceanAdapter
    _async_check: type[AsyncAdapter] = AsyncDigitalOceanAdapter
