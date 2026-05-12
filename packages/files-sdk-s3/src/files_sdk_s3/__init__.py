"""files-sdk-s3 — Amazon S3 adapter."""

from .adapter import S3Adapter
from .async_adapter import AsyncS3Adapter

__version__ = "0.1.0"
__all__ = ["AsyncS3Adapter", "S3Adapter"]
