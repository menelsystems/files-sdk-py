"""Real Cloudflare R2 integration — gated on FILES_SDK_R2_INTEGRATION=1.

Will deposit a small amount of test data in the configured R2_BUCKET under
prefixes like ``conf/``, ``unicode/``, ``listtest*/``, ``paging/``, ``src/``,
``dst/``, ``a/``, ``r2-roundtrip/``. Use a DEDICATED test bucket; no automatic
cleanup is performed (R2 free tier is generous, but the data accumulates).

Run locally (assuming creds in `.secrets` or env):

    FILES_SDK_R2_INTEGRATION=1 \
    R2_ACCOUNT_ID=... R2_ACCESS_KEY_ID=... R2_SECRET_ACCESS_KEY=... R2_BUCKET=... \
    uv run pytest tests/integration/test_r2_real.py -v -m r2_integration
"""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.r2_integration,
    pytest.mark.skipif(
        os.environ.get("FILES_SDK_R2_INTEGRATION") != "1",
        reason="set FILES_SDK_R2_INTEGRATION=1 to run real-R2 tests",
    ),
]


@pytest.fixture
def adapter():
    """Real R2 adapter — reads R2_* from env."""
    from files_sdk_r2 import R2Adapter

    return R2Adapter()


@pytest.fixture
def async_adapter():
    from files_sdk_r2 import AsyncR2Adapter

    return AsyncR2Adapter()


# Wildcard import pulls the entire conformance suite into this module so pytest
# binds the `adapter` / `async_adapter` fixtures defined above. Skip marker on
# pytestmark cascades to every imported test function.
from files_sdk.testing.conformance import *  # noqa: E402,F401,F403


def test_files_from_name_r2_roundtrip() -> None:
    """End-to-end smoke that Files.from_name('r2', ...) works against real R2."""
    from files_sdk import Files

    files = Files.from_name("r2")
    files.upload("r2-roundtrip/from-name.txt", b"hello from r2")
    assert files.download("r2-roundtrip/from-name.txt").data == b"hello from r2"
