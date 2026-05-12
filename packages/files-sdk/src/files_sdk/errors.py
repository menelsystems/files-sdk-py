"""Unified error type for files-sdk."""

from __future__ import annotations

from typing import Literal

ErrorCode = Literal[
    "not_found",
    "unauthorized",
    "conflict",
    "provider",
    "invalid_input",
]

VALID_CODES: frozenset[str] = frozenset(
    {"not_found", "unauthorized", "conflict", "provider", "invalid_input"}
)


class FilesError(Exception):
    """Single exception type raised by files-sdk and its adapters."""

    code: ErrorCode
    message: str
    provider: str | None

    def __init__(
        self,
        *,
        code: ErrorCode,
        message: str,
        provider: str | None = None,
    ) -> None:
        if code not in VALID_CODES:
            raise ValueError(f"invalid error code: {code!r}")
        super().__init__(message)
        self.code = code
        self.message = message
        self.provider = provider
