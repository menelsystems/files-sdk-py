"""Smoke test confirming the stub raises NotImplementedError."""

import pytest
from files_sdk_akamai import AkamaiAdapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        AkamaiAdapter()
