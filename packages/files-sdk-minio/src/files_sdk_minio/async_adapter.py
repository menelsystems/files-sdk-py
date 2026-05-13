"""Async MinIO adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import AsyncS3Adapter


class AsyncMinIOAdapter(AsyncS3Adapter):
    name: ClassVar[str] = "minio-async"

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        bucket: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        region: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
    ) -> None:
        resolved_endpoint = endpoint or os.environ.get("MINIO_ENDPOINT")
        if not resolved_endpoint:
            raise FilesError(
                code="unauthorized",
                message="AsyncMinIOAdapter requires endpoint= or MINIO_ENDPOINT env var",
                provider=self.name,
            )
        self._public_url_base = public_url_base or os.environ.get("MINIO_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=bucket or os.environ.get("MINIO_BUCKET"),
            region=region or os.environ.get("MINIO_REGION") or "us-east-1",
            access_key_id=access_key_id or os.environ.get("MINIO_ACCESS_KEY_ID"),
            secret_access_key=secret_access_key or os.environ.get("MINIO_SECRET_ACCESS_KEY"),
            endpoint_url=resolved_endpoint,
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            if not self._public_url_base:
                raise FilesError(
                    code="invalid_input",
                    message="public=True requires public_url_base= or MINIO_PUBLIC_URL_BASE",
                    provider=self.name,
                )
            return f"{self._public_url_base.rstrip('/')}/{key}"
        return await super().url(key, expires_in=expires_in, public=False)
