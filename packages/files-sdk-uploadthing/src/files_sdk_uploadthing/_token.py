"""Decode an `UPLOADTHING_TOKEN` (base64 JSON) into its parts.

The v7 token format is base64-encoded JSON of shape::

    {"apiKey": "sk_live_...", "appId": "abc123", "regions": ["sea1"]}

The decoded `apiKey` is sent as the `x-uploadthing-api-key` header on every
call to `api.uploadthing.com`; `appId` is used in the CDN host and as a salt
for client-side key generation; `primary_region` selects the ingest host.
"""

from __future__ import annotations

import base64
import binascii
import json
from dataclasses import dataclass

from files_sdk.errors import FilesError


@dataclass(frozen=True, slots=True)
class UploadThingToken:
    api_key: str
    app_id: str
    regions: tuple[str, ...]

    @property
    def primary_region(self) -> str:
        return self.regions[0]


def decode_token(raw: str) -> UploadThingToken:
    """Decode an UPLOADTHING_TOKEN. Raise FilesError('unauthorized') on malformed input."""
    cleaned = raw.strip()
    try:
        payload = base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError) as e:
        raise FilesError(
            code="unauthorized",
            message=f"UPLOADTHING_TOKEN is not valid base64: {e}",
            provider="uploadthing",
        ) from e
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as e:
        raise FilesError(
            code="unauthorized",
            message=f"UPLOADTHING_TOKEN payload is not JSON: {e}",
            provider="uploadthing",
        ) from e
    if not isinstance(data, dict):
        raise FilesError(
            code="unauthorized",
            message="UPLOADTHING_TOKEN payload is not a JSON object",
            provider="uploadthing",
        )
    api_key = data.get("apiKey")
    app_id = data.get("appId")
    regions = data.get("regions")
    if not isinstance(api_key, str) or not api_key:
        raise FilesError(
            code="unauthorized",
            message="UPLOADTHING_TOKEN is missing apiKey",
            provider="uploadthing",
        )
    if not isinstance(app_id, str) or not app_id:
        raise FilesError(
            code="unauthorized",
            message="UPLOADTHING_TOKEN is missing appId",
            provider="uploadthing",
        )
    if not isinstance(regions, list) or not regions or not all(isinstance(r, str) for r in regions):
        raise FilesError(
            code="unauthorized",
            message="UPLOADTHING_TOKEN is missing regions",
            provider="uploadthing",
        )
    return UploadThingToken(api_key=api_key, app_id=app_id, regions=tuple(regions))


__all__ = ["UploadThingToken", "decode_token"]
