"""files-sdk-uploadthing — adapter for UploadThing."""

from .adapter import UploadThingAdapter
from .async_adapter import AsyncUploadThingAdapter

__version__ = "0.0.0"
__all__ = ["AsyncUploadThingAdapter", "UploadThingAdapter"]
