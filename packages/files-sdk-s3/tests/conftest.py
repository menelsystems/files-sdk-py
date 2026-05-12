"""Fixtures for files-sdk-s3 tests.

Uses moto (https://github.com/getmoto/moto) to mock S3 in-process.

Compatibility note: moto v5 does not natively support aiobotocore 2.x.
The ``_patch_moto_for_aiobotocore`` function below applies two monkey-patches
that allow the in-process moto stubber to work with aioboto3/aiobotocore 2.x:

1. ``BotocoreStubber.__call__`` — returns an ``AWSResponse`` whose ``.content``
   property returns an awaitable (``AwaitableBytes``) rather than plain bytes,
   satisfying ``await http_response.content`` inside aiobotocore.  The raw
   attribute is also replaced with a ``MockRawResponseWithContent`` that exposes
   a ``StreamReader``-compatible async ``.content`` attribute so that
   ``StreamingBody.__wrapped__.content.read()`` works for GET responses.

2. ``BaseResponse.setup_class`` — aiobotocore wraps the request body in an
   ``AioAwsChunkedWrapper`` whose ``.read()`` is a coroutine.  moto's sync
   response handler calls ``.readline()`` on that object and explodes.  The
   patch runs the coroutine in a fresh thread-local event loop before moto
   ever sees the body.
"""

from __future__ import annotations

import asyncio
import os
import threading
from io import BytesIO

import boto3
import pytest
from botocore.awsrequest import AWSResponse
from moto import mock_aws


# ---------------------------------------------------------------------------
# moto + aiobotocore v2 compatibility shims
# ---------------------------------------------------------------------------

class _MockStreamReader:
    """Async reader shim that wraps bytes — satisfies ``aiohttp.StreamReader`` protocol."""

    def __init__(self, data: bytes) -> None:
        self._data = data
        self._pos = 0

    async def read(self, n: int = -1) -> bytes:
        if n == -1:
            chunk = self._data[self._pos:]
            self._pos = len(self._data)
        else:
            chunk = self._data[self._pos : self._pos + n]
            self._pos += len(chunk)
        return chunk

    def at_eof(self) -> bool:
        return self._pos >= len(self._data)


class _MockRawResponseWithContent(BytesIO):
    """BytesIO subclass with a ``.content`` async reader, as aiobotocore expects."""

    def __init__(self, data: bytes | str) -> None:
        if isinstance(data, str):
            data = data.encode("utf-8")
        super().__init__(data)
        self.content = _MockStreamReader(data)

    def stream(self, **kwargs: object) -> object:  # type: ignore[override]
        data = self.getvalue()
        if data:
            yield data


class _AwaitableBytes(bytes):
    """bytes subclass that can be ``await``-ed, returning itself."""

    def __await__(self):  # type: ignore[override]
        yield
        return self


class _PatchedAWSResponse(AWSResponse):
    """AWSResponse whose ``.content`` property returns an awaitable."""

    @property  # type: ignore[override]
    def content(self) -> "_AwaitableBytes":  # type: ignore[override]
        if self._content is None:  # type: ignore[has-type]
            self._content = b"".join(self.raw.stream()) or b""  # type: ignore[attr-defined]
        return _AwaitableBytes(self._content)  # type: ignore[arg-type]


def _patch_moto_for_aiobotocore() -> None:
    """Apply the two monkey-patches exactly once."""
    import moto.core.botocore_stubber as _stubber
    import moto.core.responses as _core_resp

    # ---- Patch 1: BotocoreStubber.__call__ ----------------------------------
    _orig_call = _stubber.BotocoreStubber.__call__

    def _patched_call(self, event_name, request, **kwargs):  # type: ignore[no-untyped-def]
        if not self.enabled:
            return None
        response = self.process_request(request)
        if response is not None:
            status, headers, body = response
            return _PatchedAWSResponse(
                request.url, status, headers,
                _MockRawResponseWithContent(body),
            )
        return response

    _stubber.BotocoreStubber.__call__ = _patched_call  # type: ignore[method-assign]

    # ---- Patch 2: BaseResponse.setup_class — materialise async body ---------
    _orig_setup = _core_resp.BaseResponse.setup_class

    def _patched_setup(self, request, full_url, headers, use_raw_body=False):  # type: ignore[no-untyped-def]
        if hasattr(request, "body") and hasattr(request.body, "read"):
            if asyncio.iscoroutinefunction(request.body.read):
                result: list[bytes | None] = [None]

                def _run() -> None:
                    loop = asyncio.new_event_loop()
                    try:
                        result[0] = loop.run_until_complete(request.body.read())
                    finally:
                        loop.close()

                t = threading.Thread(target=_run)
                t.start()
                t.join()
                request.body = result[0] if result[0] is not None else b""
        return _orig_setup(self, request, full_url, headers, use_raw_body=use_raw_body)

    _core_resp.BaseResponse.setup_class = _patched_setup  # type: ignore[method-assign]


_patch_moto_for_aiobotocore()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def s3_bucket(aws_credentials: None):
    with mock_aws():
        bucket = "conformance-bucket"
        boto3.client("s3").create_bucket(Bucket=bucket)
        yield bucket


@pytest.fixture
def adapter(s3_bucket: str):
    from files_sdk_s3 import S3Adapter
    return S3Adapter(bucket=s3_bucket)


@pytest.fixture
def async_adapter(s3_bucket: str):
    from files_sdk_s3 import AsyncS3Adapter
    return AsyncS3Adapter(bucket=s3_bucket)
