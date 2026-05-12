"""Smoke test confirming the stub raises NotImplementedError."""

import pytest

from files_sdk_minio import MinIOAdapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        MinIOAdapter()
