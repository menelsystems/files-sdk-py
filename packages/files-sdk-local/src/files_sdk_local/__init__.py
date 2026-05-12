"""files-sdk-local — local filesystem adapter."""

from .adapter import LocalAdapter
from .async_adapter import AsyncLocalAdapter

__version__ = "0.1.0"
__all__ = ["AsyncLocalAdapter", "LocalAdapter"]
