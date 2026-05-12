"""Smoke test confirming the stub raises NotImplementedError."""

import pytest

from files_sdk_gdrive import GDriveAdapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        GDriveAdapter()
