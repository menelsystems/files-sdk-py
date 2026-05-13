"""HMAC presign helpers ported from UploadThing's `packages/shared/src/crypto.ts`.

The upstream signing model:

  1. URL is built up with all params (`expires` first, then user data).
  2. HMAC-SHA256(url_string, apiKey) → hex digest, prefixed `hmac-sha256=`.
  3. `signature=...` is appended LAST.

The UploadThing ingest server verifies by parsing the incoming URL, removing
the `signature` param, re-stringifying, and re-running HMAC. The strings must
match byte-for-byte — hence the care below around JS quirks:

  * JS `encodeURIComponent` preserves `!*'()`; Python's default `quote` does
    not. We use a custom safe set to match.
  * Upstream pre-encodes data values with `encodeURIComponent` AND then hands
    them to `URLSearchParams.append`, which encodes again. We replicate the
    double-encoding rather than fix it — both client and server share the same
    code path, so consistency wins over correctness.
  * `Date.now()` is JS milliseconds. The `expires` query param is a ms
    timestamp, NOT seconds.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import urllib.parse
from collections.abc import Mapping
from typing import Any

from sqids import Sqids  # type: ignore[import-untyped]

from ._hash import effect_hash_string, shuffle

_SIGNATURE_PREFIX = "hmac-sha256="

# Chars NOT escaped by JS encodeURIComponent (per MDN):
#   A-Z a-z 0-9 - _ . ! ~ * ' ( )
# Python's quote() doesn't escape A-Z a-z 0-9 by default; we extend `safe`
# to cover the rest. (Underscore and dot are also safe by default but
# repeating them is harmless.)
_JS_ENCODE_URI_COMPONENT_SAFE = "-_.~!*'()"


def js_encode_uri_component(value: str) -> str:
    """Match JavaScript `encodeURIComponent` byte-for-byte."""
    return urllib.parse.quote(value, safe=_JS_ENCODE_URI_COMPONENT_SAFE)


def _js_stringify(value: object) -> str:
    """Match JavaScript's `String(value)` for the value types upstream passes."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _append_param(parts: list[str], key: str, value: str) -> None:
    """Append `key=value` to the query, encoding via JS URLSearchParams rules."""
    parts.append(f"{js_encode_uri_component(key)}={js_encode_uri_component(value)}")


def sign_payload(payload: str, secret: str) -> str:
    """HMAC-SHA256 hex digest of `payload` with `secret`, prefixed `hmac-sha256=`."""
    digest = hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{_SIGNATURE_PREFIX}{digest}"


def generate_signed_url(
    url: str,
    *,
    secret: str,
    ttl_seconds: int = 3600,
    data: Mapping[str, Any] | None = None,
    now_ms: int | None = None,
) -> str:
    """Append `expires`, user `data`, and a trailing `signature` to `url`.

    `now_ms` is the unix-millis epoch; default is `time.time() * 1000`. Pass it
    explicitly in tests for determinism.
    """
    parsed = urllib.parse.urlparse(url)
    existing_query = parsed.query
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    expires_at = now_ms + ttl_seconds * 1000

    parts: list[str] = []
    if existing_query:
        parts.append(existing_query)
    _append_param(parts, "expires", str(expires_at))

    if data:
        for key, value in data.items():
            if value is None:
                continue
            # Upstream calls encodeURIComponent on the value first, then hands
            # the already-encoded string to URLSearchParams.append, which
            # encodes again. We reproduce the double-encoding so the server's
            # HMAC verification matches.
            once_encoded = js_encode_uri_component(_js_stringify(value))
            _append_param(parts, key, once_encoded)

    query = "&".join(parts)
    signed_input = urllib.parse.urlunparse(parsed._replace(query=query))
    signature = sign_payload(signed_input, secret)
    parts.append(f"signature={js_encode_uri_component(signature)}")
    final_query = "&".join(parts)
    return urllib.parse.urlunparse(parsed._replace(query=final_query))


_SQIDS_DEFAULT_ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def generate_file_key(
    app_id: str,
    *,
    file_name: str = "",
    file_size: int = 0,
    file_type: str = "",
    now_ms: int | None = None,
) -> str:
    """Generate a fileKey the UploadThing ingest server will accept.

    The server validates the leading 12 chars as an SQId-encoded hash of the
    appId, decoded with an alphabet that's been deterministically shuffled
    using the same appId as seed. The trailing 36 chars are an SQId-encoded
    hash of file metadata using the same shuffled alphabet — opaque-ish but
    unique per call thanks to `now_ms`.

    Mirrors `generateKey` in upstream `packages/uploadthing/src/sdk/utils.ts`.
    """
    if now_ms is None:
        now_ms = int(time.time() * 1000)
    # JSON.stringify with no spaces, matching JS default. `lastModified` is
    # 0 for synthetic uploads (we don't have a File handle); `Date.now()`
    # provides the per-call entropy.
    hash_parts = json.dumps(
        [file_name, file_size, file_type, 0, now_ms],
        separators=(",", ":"),
    )
    file_seed_hash = abs(effect_hash_string(hash_parts))
    app_id_hash = abs(effect_hash_string(app_id))

    alphabet = shuffle(_SQIDS_DEFAULT_ALPHABET, app_id)
    encoded_app_id = Sqids(alphabet=alphabet, min_length=12).encode([app_id_hash])
    encoded_file_seed = Sqids(alphabet=alphabet, min_length=36).encode([file_seed_hash])
    return encoded_app_id + encoded_file_seed


__all__ = [
    "generate_file_key",
    "generate_signed_url",
    "js_encode_uri_component",
    "sign_payload",
]
