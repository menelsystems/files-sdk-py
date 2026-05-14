"""Synchronous DigitalOcean Spaces adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


class DigitalOceanAdapter(S3Adapter):
    """DigitalOcean Spaces storage adapter (S3-compatible).

    Endpoint is constructed from ``region`` as
    ``https://<region>.digitaloceanspaces.com``. Default public URLs use the
    bucket-virtual-host form ``https://<bucket>.<region>.digitaloceanspaces.com/<key>``;
    pass ``public_url_base`` (e.g. a CDN endpoint or custom domain) to override.
    """

    name: ClassVar[str] = "digitalocean"

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
        resolved_region = region or os.environ.get("DO_SPACES_REGION")
        if not resolved_region:
            raise FilesError(
                code="unauthorized",
                message="DigitalOceanAdapter requires region= or DO_SPACES_REGION env var",
                provider=self.name,
            )
        resolved_bucket = bucket or os.environ.get("DO_SPACES_BUCKET")
        self._region = resolved_region
        self._public_url_base = public_url_base or os.environ.get("DO_SPACES_PUBLIC_URL_BASE")
        default_endpoint = f"https://{resolved_region}.digitaloceanspaces.com"
        kwargs: dict[str, Any] = dict(
            bucket=resolved_bucket,
            region=resolved_region,
            access_key_id=access_key_id or os.environ.get("DO_SPACES_KEY"),
            secret_access_key=secret_access_key or os.environ.get("DO_SPACES_SECRET"),
            endpoint_url=_endpoint_override or default_endpoint,
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = (
                self._public_url_base
                or f"https://{self.bucket}.{self._region}.digitaloceanspaces.com"
            )
            return f"{base.rstrip('/')}/{key}"
        return super().url(key, expires_in=expires_in, public=False)
