"""Entry-point based adapter discovery."""

from __future__ import annotations

from importlib.metadata import entry_points

from .adapter import Adapter, AsyncAdapter
from .errors import FilesError

GROUP = "files_sdk.adapters"


def load_adapter_class(name: str) -> type[Adapter] | type[AsyncAdapter]:
    """Return the adapter class registered under ``name``.

    The return type is the union of the two adapter Protocols so that
    callsites surface signature drift between an impl and its Protocol
    at type-check time (sync vs. async is disambiguated at runtime by
    :func:`files_sdk.adapter.is_async_adapter`).

    Raises ``FilesError(code="invalid_input")`` if no entry point matches.
    """
    eps = list(entry_points(group=GROUP))
    for ep in eps:
        if ep.name == name:
            return ep.load()  # type: ignore[no-any-return]
    raise FilesError(
        code="invalid_input",
        message=(
            f"no adapter named {name!r}; install files-sdk-{name} or pass adapter= explicitly"
        ),
    )
