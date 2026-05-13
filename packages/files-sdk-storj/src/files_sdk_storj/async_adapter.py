"""Async Storj DCS adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import AsyncS3Adapter


class AsyncStorjAdapter(AsyncS3Adapter):
    name: ClassVar[str] = "storj-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        gateway_region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
        _endpoint_override: str | None = None,
    ) -> None:
        resolved_region = gateway_region or os.environ.get("STORJ_GATEWAY_REGION")
        self._gateway_region = resolved_region
        self._public_url_base = public_url_base or os.environ.get("STORJ_PUBLIC_URL_BASE")
        if resolved_region:
            default_endpoint = f"https://gateway.{resolved_region}.storjshare.io"
        else:
            default_endpoint = "https://gateway.storjshare.io"
        kwargs: dict[str, Any] = dict(
            bucket=bucket or os.environ.get("STORJ_BUCKET"),
            region="global",
            access_key_id=access_key_id or os.environ.get("STORJ_ACCESS_KEY_ID"),
            secret_access_key=secret_access_key or os.environ.get("STORJ_SECRET_ACCESS_KEY"),
            endpoint_url=_endpoint_override or default_endpoint,
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            if not self._public_url_base:
                raise FilesError(
                    code="invalid_input",
                    message=(
                        "public=True requires public_url_base= or STORJ_PUBLIC_URL_BASE "
                        "(typically a Storj Linksharing service root URL)"
                    ),
                    provider=self.name,
                )
            return f"{self._public_url_base.rstrip('/')}/{key}"
        return await super().url(key, expires_in=expires_in, public=False)
