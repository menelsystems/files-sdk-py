from unittest.mock import MagicMock, patch

import pytest

from files_sdk._registry import load_adapter_class
from files_sdk.errors import FilesError


def _fake_entry_point(name: str, target: type) -> MagicMock:
    ep = MagicMock()
    ep.name = name
    ep.load.return_value = target
    return ep


def test_load_adapter_class_returns_class():
    class Fake:
        name = "fake"
    fake_ep = _fake_entry_point("fake", Fake)
    with patch("files_sdk._registry.entry_points") as mocked:
        mocked.return_value = [fake_ep]
        cls = load_adapter_class("fake")
    assert cls is Fake


def test_load_adapter_class_unknown_name_raises():
    with patch("files_sdk._registry.entry_points") as mocked:
        mocked.return_value = []
        with pytest.raises(FilesError) as ei:
            load_adapter_class("nope")
    assert ei.value.code == "invalid_input"
    assert "files-sdk-nope" in ei.value.message
