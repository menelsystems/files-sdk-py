"""Real Amazon S3 integration — gated on FILES_SDK_AWS_S3_INTEGRATION=1.

Will deposit a small amount of test data in the configured AWS_S3_BUCKET under
prefixes like ``conf/``, ``unicode/``, ``listtest*/``, ``paging/``, ``src/``,
``dst/``, ``a/``. Use a DEDICATED test bucket; no automatic cleanup is
performed.

Run locally (assuming creds in `.secrets` or env):

    FILES_SDK_AWS_S3_INTEGRATION=1 \
    AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... AWS_REGION=... AWS_S3_BUCKET=... \
    uv run pytest tests/integration/test_aws_s3_real.py -v -m aws_s3_integration
"""

from __future__ import annotations

import os

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.aws_s3_integration,
    pytest.mark.skipif(
        os.environ.get("FILES_SDK_AWS_S3_INTEGRATION") != "1",
        reason="set FILES_SDK_AWS_S3_INTEGRATION=1 to run real-AWS-S3 tests",
    ),
]


@pytest.fixture
def adapter():
    """Real AWS S3 adapter — reads AWS_* + AWS_S3_BUCKET from env."""
    from files_sdk_s3 import S3Adapter

    return S3Adapter()


@pytest.fixture
def async_adapter():
    from files_sdk_s3 import AsyncS3Adapter

    return AsyncS3Adapter()


# Wildcard import pulls the entire conformance suite into this module so pytest
# binds the `adapter` / `async_adapter` fixtures defined above. Skip marker on
# pytestmark cascades to every imported test function.
from files_sdk.testing.conformance import *  # noqa: E402,F403


def test_files_from_name_s3_roundtrip() -> None:
    """End-to-end smoke that Files.from_name('s3', ...) works against real AWS S3."""
    from files_sdk import Files

    files = Files.from_name("s3")
    files.upload("aws-roundtrip/from-name.txt", b"hello from s3")
    assert files.download("aws-roundtrip/from-name.txt").data == b"hello from s3"
