"""Shared helpers used by both the sync and async adapters.

Kept in a separate `_helpers` module (rather than as private members of
`adapter.py`) so the async adapter can import them without tripping pyright's
`reportPrivateUsage` on cross-module underscore-prefixed names.
"""

from __future__ import annotations

import mimetypes
import os
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, cast

from files_sdk.errors import FilesError
from files_sdk.types import UploadBody

from ._token import UploadThingToken, decode_token

API_BASE = "https://api.uploadthing.com"
DEFAULT_TTL = 3600


def resolve_token(token: str | None, *, adapter_name: str) -> UploadThingToken:
    raw = token or os.environ.get("UPLOADTHING_TOKEN")
    if not raw:
        raise FilesError(
            code="unauthorized",
            message=f"{adapter_name} requires token= or UPLOADTHING_TOKEN env var",
            provider="uploadthing",
        )
    return decode_token(raw)


def normalize_http_error(op: str, status: int, body: bytes) -> FilesError:
    text = body.decode("utf-8", errors="replace")[:500]
    if status == 404:
        return FilesError(code="not_found", message=f"{op}: {text}", provider="uploadthing")
    if status in (401, 403):
        return FilesError(code="unauthorized", message=f"{op}: {text}", provider="uploadthing")
    if status in (409, 412):
        return FilesError(code="conflict", message=f"{op}: {text}", provider="uploadthing")
    if status == 400:
        return FilesError(code="invalid_input", message=f"{op}: {text}", provider="uploadthing")
    return FilesError(
        code="provider",
        message=f"{op}: HTTP {status} {text}",
        provider="uploadthing",
    )


def body_to_bytes(body: UploadBody) -> bytes:
    if isinstance(body, (bytes, bytearray)):
        return bytes(body)
    if isinstance(body, str):
        return body.encode("utf-8")
    if isinstance(body, Path):
        return body.read_bytes()
    return body.read()  # file-like


def guess_content_type(key: str, override: str | None) -> str:
    if override:
        return override
    guessed, _ = mimetypes.guess_type(key)
    return guessed or "application/octet-stream"


def parse_last_modified(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    try:
        return parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return datetime.now(UTC)


def clean_etag(value: str | None) -> str | None:
    """Normalize CDN etags: strip `W/` weak-validator prefix and surrounding quotes."""
    if not value:
        return None
    v = value
    if v.startswith("W/"):
        v = v[2:]
    return v.strip('"') or None


def size_from_range_headers(headers: Any) -> int:
    """Cloudflare HEAD returns ``content-length: 0`` on cold cache for some
    paths; a ranged GET returns ``Content-Range: bytes 0-0/N`` which is
    reliable. Fall back to content-length if the server ignored Range."""
    cr = headers.get("content-range")
    if cr:
        try:
            return int(cr.rsplit("/", 1)[-1])
        except ValueError:
            pass
    cl = headers.get("content-length")
    if cl:
        try:
            return int(cl)
        except ValueError:
            pass
    return 0


def extract_url_from_get_file_url_response(resp: dict[str, Any]) -> str | None:
    """Pull the first `url` string out of a `/v6/getFileUrl` response."""
    data = resp.get("data")
    if not isinstance(data, list):
        return None
    for item in cast("list[Any]", data):
        if isinstance(item, dict):
            url = cast("dict[str, Any]", item).get("url")
            if isinstance(url, str):
                return url
    return None


__all__ = [
    "API_BASE",
    "DEFAULT_TTL",
    "body_to_bytes",
    "clean_etag",
    "extract_url_from_get_file_url_response",
    "guess_content_type",
    "normalize_http_error",
    "parse_last_modified",
    "resolve_token",
    "size_from_range_headers",
]
