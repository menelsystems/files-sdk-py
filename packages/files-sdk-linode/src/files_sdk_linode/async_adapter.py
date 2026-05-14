"""Async Linode Object Storage adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import AsyncS3Adapter


class AsyncLinodeAdapter(AsyncS3Adapter):
    name: ClassVar[str] = "linode-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        cluster: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
        _endpoint_override: str | None = None,
    ) -> None:
        resolved_cluster = cluster or os.environ.get("LINODE_CLUSTER")
        if not resolved_cluster:
            raise FilesError(
                code="unauthorized",
                message="AsyncLinodeAdapter requires cluster= or LINODE_CLUSTER env var",
                provider=self.name,
            )
        self._cluster = resolved_cluster
        self._public_url_base = public_url_base or os.environ.get("LINODE_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=bucket or os.environ.get("LINODE_BUCKET"),
            region=resolved_cluster,
            access_key_id=access_key_id or os.environ.get("LINODE_ACCESS_KEY_ID"),
            secret_access_key=secret_access_key or os.environ.get("LINODE_SECRET_ACCESS_KEY"),
            endpoint_url=_endpoint_override or f"https://{resolved_cluster}.linodeobjects.com",
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = (
                self._public_url_base or f"https://{self.bucket}.{self._cluster}.linodeobjects.com"
            )
            return f"{base.rstrip('/')}/{key}"
        return await super().url(key, expires_in=expires_in, public=False)
