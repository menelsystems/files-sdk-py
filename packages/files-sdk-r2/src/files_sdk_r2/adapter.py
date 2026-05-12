"""Cloudflare R2 adapter — S3-compatible with a different endpoint."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


class R2Adapter(S3Adapter):
    """Cloudflare R2 storage adapter (S3-compatible)."""

    name: ClassVar[str] = "r2"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        account_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
    ) -> None:
        resolved_account = account_id or os.environ.get("R2_ACCOUNT_ID")
        if not resolved_account:
            raise FilesError(
                code="unauthorized",
                message="R2Adapter requires account_id= or R2_ACCOUNT_ID env var",
                provider=self.name,
            )
        resolved_bucket = bucket or os.environ.get("R2_BUCKET")
        resolved_key = access_key_id or os.environ.get("R2_ACCESS_KEY_ID")
        resolved_secret = secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY")
        self._account_id = resolved_account
        self._public_url_base = public_url_base or os.environ.get("R2_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=resolved_bucket,
            region="auto",
            access_key_id=resolved_key,
            secret_access_key=resolved_secret,
            endpoint_url=f"https://{resolved_account}.r2.cloudflarestorage.com",
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            if not self._public_url_base:
                raise FilesError(
                    code="invalid_input",
                    message="public=True requires public_url_base= or R2_PUBLIC_URL_BASE",
                    provider=self.name,
                )
            return f"{self._public_url_base.rstrip('/')}/{key}"
        return super().url(key, expires_in=expires_in, public=False)
