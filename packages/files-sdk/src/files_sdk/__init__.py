"""files-sdk — unified Python SDK for cloud storage."""

from .adapter import Adapter, AsyncAdapter
from .client import AsyncFiles, Files
from .errors import ErrorCode, FilesError
from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

__version__ = "0.1.0"

__all__ = [
    "Adapter",
    "AsyncAdapter",
    "AsyncFiles",
    "ErrorCode",
    "FileMetadata",
    "Files",
    "FilesError",
    "ListPage",
    "SignedUpload",
    "StoredFile",
    "UploadBody",
]
