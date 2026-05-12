"""files-sdk-r2 — Cloudflare R2 adapter."""

from .adapter import R2Adapter
from .async_adapter import AsyncR2Adapter

__version__ = "0.1.0"
__all__ = ["AsyncR2Adapter", "R2Adapter"]
