"""files-sdk-akamai — Akamai (Linode) Object Storage adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import AkamaiAdapter
from .async_adapter import AsyncAkamaiAdapter

try:
    __version__ = _pkg_version("files-sdk-akamai")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AkamaiAdapter", "AsyncAkamaiAdapter"]

if TYPE_CHECKING:
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = AkamaiAdapter
    _async_check: type[AsyncAdapter] = AsyncAkamaiAdapter
