"""Local adapter conformance fixtures — use tmp_path for isolation."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def adapter(tmp_path: Path):
    from files_sdk_local import LocalAdapter

    return LocalAdapter(root=tmp_path / "store")


@pytest.fixture
def async_adapter(tmp_path: Path):
    from files_sdk_local import AsyncLocalAdapter

    return AsyncLocalAdapter(root=tmp_path / "store-async")
