"""Smoke test confirming the stub raises NotImplementedError."""

import pytest

from files_sdk_digitalocean import DigitalOceanAdapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        DigitalOceanAdapter()
