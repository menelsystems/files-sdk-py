"""files-sdk — unified Python SDK for cloud storage."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from .adapter import Adapter, AsyncAdapter
from .client import AsyncFiles, Files
from .errors import ErrorCode, FilesError
from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

try:
    __version__ = _pkg_version("files-sdk")
except PackageNotFoundError:  # pragma: no cover — only triggers in non-installed source trees
    __version__ = "0.0.0+unknown"

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
