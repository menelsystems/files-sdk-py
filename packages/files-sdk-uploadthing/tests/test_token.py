"""Tests for the UPLOADTHING_TOKEN decoder."""

from __future__ import annotations

import base64
import json

import pytest
from files_sdk.errors import FilesError
from files_sdk_uploadthing._token import UploadThingToken, decode_token


def _encode(payload: dict[str, object]) -> str:
    return base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")


def test_decode_token_extracts_fields() -> None:
    raw = _encode(
        {"apiKey": "sk_live_abc", "appId": "myapp", "regions": ["sea1", "fra1"]}
    )
    tok = decode_token(raw)
    assert isinstance(tok, UploadThingToken)
    assert tok.api_key == "sk_live_abc"
    assert tok.app_id == "myapp"
    assert tok.regions == ("sea1", "fra1")
    assert tok.primary_region == "sea1"


def test_decode_token_accepts_padded_base64() -> None:
    raw = _encode({"apiKey": "k", "appId": "a", "regions": ["x"]})
    # Add explicit padding (b64encode already does, but verify tolerant)
    assert decode_token(raw).api_key == "k"


def test_decode_token_strips_trailing_whitespace() -> None:
    raw = _encode({"apiKey": "k", "appId": "a", "regions": ["x"]}) + "\n"
    assert decode_token(raw).api_key == "k"


def test_decode_token_rejects_non_base64() -> None:
    with pytest.raises(FilesError) as ei:
        decode_token("not-base64-!!!")
    assert ei.value.code == "unauthorized"
    assert ei.value.provider == "uploadthing"


def test_decode_token_rejects_non_json_payload() -> None:
    raw = base64.b64encode(b"hello world").decode("ascii")
    with pytest.raises(FilesError) as ei:
        decode_token(raw)
    assert ei.value.code == "unauthorized"


def test_decode_token_rejects_missing_apiKey() -> None:
    raw = _encode({"appId": "a", "regions": ["x"]})
    with pytest.raises(FilesError) as ei:
        decode_token(raw)
    assert ei.value.code == "unauthorized"


def test_decode_token_rejects_missing_appId() -> None:
    raw = _encode({"apiKey": "k", "regions": ["x"]})
    with pytest.raises(FilesError) as ei:
        decode_token(raw)
    assert ei.value.code == "unauthorized"


def test_decode_token_rejects_empty_regions() -> None:
    raw = _encode({"apiKey": "k", "appId": "a", "regions": []})
    with pytest.raises(FilesError) as ei:
        decode_token(raw)
    assert ei.value.code == "unauthorized"
