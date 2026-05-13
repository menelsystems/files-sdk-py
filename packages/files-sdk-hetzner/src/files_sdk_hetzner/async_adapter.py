"""Async Hetzner Object Storage adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import AsyncS3Adapter


class AsyncHetznerAdapter(AsyncS3Adapter):
    name: ClassVar[str] = "hetzner-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
        _endpoint_override: str | None = None,
    ) -> None:
        resolved_region = region or os.environ.get("HETZNER_REGION")
        if not resolved_region:
            raise FilesError(
                code="unauthorized",
                message="AsyncHetznerAdapter requires region= or HETZNER_REGION env var",
                provider=self.name,
            )
        self._region = resolved_region
        self._public_url_base = public_url_base or os.environ.get("HETZNER_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=bucket or os.environ.get("HETZNER_BUCKET"),
            region=resolved_region,
            access_key_id=access_key_id or os.environ.get("HETZNER_ACCESS_KEY_ID"),
            secret_access_key=secret_access_key or os.environ.get("HETZNER_SECRET_ACCESS_KEY"),
            endpoint_url=_endpoint_override or f"https://{resolved_region}.your-objectstorage.com",
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = (
                self._public_url_base
                or f"https://{self.bucket}.{self._region}.your-objectstorage.com"
            )
            return f"{base.rstrip('/')}/{key}"
        return await super().url(key, expires_in=expires_in, public=False)
