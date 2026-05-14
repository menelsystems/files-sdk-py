"""Tests for HMAC presign helpers.

The upstream TypeScript SDK
(`packages/shared/src/crypto.ts:signPayload` and `generateSignedURL`) is the
canonical implementation; this module must produce byte-identical query
strings so the UploadThing ingest server's HMAC verification passes.

Specifically tested:
  - HMAC-SHA256 hex digest with `hmac-sha256=` prefix (matches `signaturePrefix`)
  - `expires` is milliseconds (JS `Date.now() + ttl*1000`), not seconds
  - data values are URI-encoded with the JS `encodeURIComponent` charset
    (preserving `!*'()` unlike RFC 3986), then encoded again by the
    URLSearchParams-style serializer — matching upstream's double-encoding
  - `None` values in data are dropped, not serialized as "None"
  - param order: existing query, then expires, then data, then signature LAST
"""

from __future__ import annotations

import hashlib
import hmac
import urllib.parse

import pytest
from files_sdk_uploadthing._signing import (
    generate_file_key,
    generate_signed_url,
    js_encode_uri_component,
    sign_payload,
)

# ---- sign_payload --------------------------------------------------------


def test_sign_payload_returns_prefixed_hex() -> None:
    sig = sign_payload("hello", "secret")
    assert sig.startswith("hmac-sha256=")
    digest = sig.removeprefix("hmac-sha256=")
    expected = hmac.new(b"secret", b"hello", hashlib.sha256).hexdigest()
    assert digest == expected


def test_sign_payload_unicode_payload() -> None:
    sig = sign_payload("héllo wörld", "k")
    expected = hmac.new(b"k", "héllo wörld".encode(), hashlib.sha256).hexdigest()
    assert sig == f"hmac-sha256={expected}"


def test_sign_payload_unicode_secret() -> None:
    sig = sign_payload("x", "sêcret")
    expected = hmac.new("sêcret".encode(), b"x", hashlib.sha256).hexdigest()
    assert sig == f"hmac-sha256={expected}"


# ---- js_encode_uri_component --------------------------------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("hello world", "hello%20world"),
        ("a!b*c'd(e)f", "a!b*c'd(e)f"),  # JS-safe chars stay raw
        ("a/b", "a%2Fb"),  # slash IS encoded by encodeURIComponent
        ("a&b=c", "a%26b%3Dc"),
        ("héllo", "h%C3%A9llo"),
        ("", ""),
    ],
)
def test_js_encode_uri_component_matches_js(raw: str, expected: str) -> None:
    assert js_encode_uri_component(raw) == expected


# ---- generate_signed_url ------------------------------------------------


def test_generate_signed_url_appends_expires_and_signature() -> None:
    url = generate_signed_url(
        "https://example.com/x",
        secret="k",
        ttl_seconds=60,
        data={},
        now_ms=1_000_000,
    )
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    assert params["expires"] == [str(1_000_000 + 60_000)]
    assert "signature" in params
    assert params["signature"][0].startswith("hmac-sha256=")


def test_generate_signed_url_signature_covers_url_without_itself() -> None:
    url = generate_signed_url(
        "https://example.com/x",
        secret="k",
        ttl_seconds=60,
        data={"foo": "bar"},
        now_ms=0,
    )
    # Strip the &signature=... from the end; the remainder is what was signed.
    sig_idx = url.rfind("&signature=")
    assert sig_idx > 0
    signed_input = url[:sig_idx]
    sig_value = url[sig_idx + len("&signature=") :]
    # The signature was URL-encoded once when appended; decode.
    sig_decoded = urllib.parse.unquote(sig_value)
    expected = hmac.new(b"k", signed_input.encode("utf-8"), hashlib.sha256).hexdigest()
    assert sig_decoded == f"hmac-sha256={expected}"


def test_generate_signed_url_skips_none_values() -> None:
    url = generate_signed_url(
        "https://example.com/x",
        secret="k",
        ttl_seconds=60,
        data={"keep": "yes", "drop": None},
        now_ms=0,
    )
    assert "keep=" in url
    assert "drop=" not in url


def test_generate_signed_url_double_encodes_data_values() -> None:
    # Upstream calls encodeURIComponent then appends to URLSearchParams,
    # which encodes again. A space becomes %2520 (not %20).
    url = generate_signed_url(
        "https://example.com/x",
        secret="k",
        ttl_seconds=60,
        data={"name": "hello world"},
        now_ms=0,
    )
    assert "name=hello%2520world" in url


def test_generate_signed_url_serializes_numbers_and_bools() -> None:
    url = generate_signed_url(
        "https://example.com/x",
        secret="k",
        ttl_seconds=60,
        data={"size": 42, "public": True},
        now_ms=0,
    )
    assert "size=42" in url
    # JS String(true) → "true"
    assert "public=true" in url


def test_generate_signed_url_preserves_existing_query() -> None:
    url = generate_signed_url(
        "https://example.com/x?a=1",
        secret="k",
        ttl_seconds=60,
        data={"b": "2"},
        now_ms=0,
    )
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    assert params["a"] == ["1"]
    assert params["b"] == ["2"]


# ---- generate_file_key --------------------------------------------------


def test_generate_file_key_has_expected_shape() -> None:
    # 12-char encoded appId prefix + 36-char encoded file seed = 48 chars min.
    k = generate_file_key("myapp", file_name="avatar.png", file_size=10, file_type="image/png")
    assert len(k) >= 48
    assert all(c.isalnum() for c in k)


def test_generate_file_key_deterministic_app_id_prefix() -> None:
    # The first 12 chars (encoded appId) must be stable for a given appId so
    # the ingest server's appId validation can succeed across uploads.
    a = generate_file_key("myapp", file_name="a", file_size=1, file_type="x", now_ms=1)
    b = generate_file_key("myapp", file_name="b", file_size=2, file_type="y", now_ms=2)
    assert a[:12] == b[:12]


def test_generate_file_key_varies_per_call() -> None:
    keys = {
        generate_file_key("a", file_name=f"f{i}.txt", file_size=i, file_type="text/plain")
        for i in range(50)
    }
    assert len(keys) == 50


def test_generate_file_key_url_safe() -> None:
    # Only chars from the shuffled SQIds alphabet (alphanumeric).
    k = generate_file_key("a", file_name="f", file_size=1, file_type="t")
    assert all(c.isalnum() for c in k)
