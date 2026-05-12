"""Entry-point based adapter discovery."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any

from .errors import FilesError

GROUP = "files_sdk.adapters"


def load_adapter_class(name: str) -> type[Any]:
    """Return the adapter class registered under ``name``.

    Raises ``FilesError(code="invalid_input")`` if no entry point matches.
    """
    eps = list(entry_points(group=GROUP))
    for ep in eps:
        if ep.name == name:
            return ep.load()
    raise FilesError(
        code="invalid_input",
        message=(
            f"no adapter named {name!r}; install files-sdk-{name} or pass adapter= explicitly"
        ),
    )
