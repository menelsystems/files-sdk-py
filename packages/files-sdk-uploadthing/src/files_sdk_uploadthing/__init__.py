"""files-sdk-uploadthing — adapter for UploadThing."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import UploadThingAdapter
from .async_adapter import AsyncUploadThingAdapter

try:
    __version__ = _pkg_version("files-sdk-uploadthing")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncUploadThingAdapter", "UploadThingAdapter"]

if TYPE_CHECKING:
    # See files_sdk_s3.__init__ for the rationale on this tripwire.
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = UploadThingAdapter
    _async_check: type[AsyncAdapter] = AsyncUploadThingAdapter
