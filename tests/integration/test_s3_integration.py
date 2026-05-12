"""Run the shared conformance suite against a real S3-compatible server."""

import pytest

pytestmark = pytest.mark.integration

from files_sdk.testing.conformance import *  # noqa: E402,F401,F403
