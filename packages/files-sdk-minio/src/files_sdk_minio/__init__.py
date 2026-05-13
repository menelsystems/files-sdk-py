"""files-sdk-minio — MinIO adapter."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version
from typing import TYPE_CHECKING

from .adapter import MinIOAdapter
from .async_adapter import AsyncMinIOAdapter

try:
    __version__ = _pkg_version("files-sdk-minio")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.0+unknown"

__all__ = ["AsyncMinIOAdapter", "MinIOAdapter"]

if TYPE_CHECKING:
    # See files_sdk_s3.__init__ for the rationale on this tripwire.
    from files_sdk.adapter import Adapter, AsyncAdapter

    _sync_check: type[Adapter] = MinIOAdapter
    _async_check: type[AsyncAdapter] = AsyncMinIOAdapter
