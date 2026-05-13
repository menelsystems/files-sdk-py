"""Fixtures for files-sdk-uploadthing conformance tests.

Live tests require `UPLOADTHING_TOKEN` in the environment. If absent the
conformance suite is skipped so unit tests (`test_token`, `test_signing`)
still run in environments without a UT account.
"""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
import pytest_asyncio


def _skip_if_no_token() -> None:
    if not os.environ.get("UPLOADTHING_TOKEN"):
        pytest.skip("UPLOADTHING_TOKEN not set — skipping live conformance")


def _cleanup_keys(adapter, keys: list[str]) -> None:
    """Best-effort delete of every key uploaded during a test."""
    for k in keys:
        try:
            adapter.delete(k)
        except Exception:
            pass


@pytest.fixture
def adapter() -> Iterator:
    _skip_if_no_token()
    from files_sdk_uploadthing import UploadThingAdapter

    a = UploadThingAdapter()

    # Patch upload/copy to capture keys for teardown, so live tests don't
    # leave litter in the UT account.
    uploaded: list[str] = []
    real_upload = a.upload
    real_copy = a.copy

    def upload(key, body, **opts):
        uploaded.append(key)
        return real_upload(key, body, **opts)

    def copy(src, dst):
        uploaded.append(dst)
        return real_copy(src, dst)

    a.upload = upload  # type: ignore[method-assign]
    a.copy = copy  # type: ignore[method-assign]
    try:
        yield a
    finally:
        _cleanup_keys(a, uploaded)


@pytest_asyncio.fixture
async def async_adapter() -> AsyncIterator:
    _skip_if_no_token()
    from files_sdk_uploadthing import AsyncUploadThingAdapter

    a = AsyncUploadThingAdapter()
    uploaded: list[str] = []
    real_upload = a.upload
    real_copy = a.copy

    async def upload(key, body, **opts):
        uploaded.append(key)
        return await real_upload(key, body, **opts)

    async def copy(src, dst):
        uploaded.append(dst)
        return await real_copy(src, dst)

    a.upload = upload  # type: ignore[method-assign]
    a.copy = copy  # type: ignore[method-assign]
    try:
        yield a
    finally:
        for k in uploaded:
            try:
                await a.delete(k)
            except Exception:
                pass
        await a.aclose()


@pytest.fixture
def test_run_id() -> str:
    """Unique prefix per test run for namespacing keys."""
    return f"conf-{uuid.uuid4().hex[:8]}"
