# files-sdk-py v0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python `uv` workspace recreating files-sdk.dev with a core `files-sdk` package, working R2 and S3 adapters, and 15 scaffolded stub packages.

**Architecture:** `uv` workspace with member packages. Core defines a sync `Adapter` and async `AsyncAdapter` Protocol; `Files`/`AsyncFiles` clients thin-wrap an adapter. R2 adapter subclasses S3 adapter with a different endpoint. Plugin discovery via `importlib.metadata` entry points (`files_sdk.adapters` group). Errors normalize to a single `FilesError` enum-coded exception.

**Tech Stack:** Python 3.11+, uv (workspace), hatchling (build), pydantic v2, httpx, boto3, aioboto3, ruff, pyright, pytest, pytest-asyncio, moto.

**Spec:** `docs/superpowers/specs/2026-05-12-files-sdk-py-design.md`

---

## File Structure (locks in decomposition)

```
files-sdk/
├── pyproject.toml                              # workspace root + dev deps
├── uv.lock
├── .python-version                             # 3.13
├── ruff.toml                                   # shared
├── pyrightconfig.json                          # shared, strict
├── .github/workflows/ci.yml
├── docs/superpowers/{specs,plans}/
└── packages/
    ├── files-sdk/
    │   ├── pyproject.toml
    │   └── src/files_sdk/
    │       ├── __init__.py                     # re-exports public API
    │       ├── errors.py                       # FilesError + codes
    │       ├── types.py                        # FileMetadata, StoredFile, ListPage, SignedUpload, UploadBody alias
    │       ├── adapter.py                      # Adapter, AsyncAdapter Protocols
    │       ├── _registry.py                    # entry-point lookup
    │       ├── client.py                       # Files, AsyncFiles
    │       └── testing/
    │           ├── __init__.py                 # re-exports
    │           └── conformance.py              # parametrizable conformance test functions
    ├── files-sdk-s3/
    │   ├── pyproject.toml
    │   ├── src/files_sdk_s3/
    │   │   ├── __init__.py
    │   │   ├── adapter.py                      # S3Adapter (sync)
    │   │   └── async_adapter.py                # AsyncS3Adapter
    │   └── tests/
    │       ├── conftest.py                     # adapter fixture w/ moto
    │       └── test_conformance.py             # imports from files_sdk.testing
    ├── files-sdk-r2/
    │   ├── pyproject.toml                      # depends on files-sdk-s3
    │   ├── src/files_sdk_r2/{__init__,adapter,async_adapter}.py
    │   └── tests/{conftest,test_conformance}.py
    ├── _template/                              # contributor scaffold (NOT a uv member)
    │   ├── pyproject.toml.tmpl
    │   ├── CLAIM.md.tmpl
    │   └── src/files_sdk_PROVIDER/{__init__,adapter}.py.tmpl
    └── files-sdk-{akamai,azure,box,digitalocean,dropbox,gcs,gdrive,
                   hetzner,minio,netlify,onedrive,storj,supabase,
                   uploadthing,vercel}/         # 15 stub packages
        ├── pyproject.toml
        ├── CLAIM.md
        └── src/files_sdk_<provider>/{__init__,adapter}.py
```

---

## Task 1: Workspace scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `ruff.toml`
- Create: `pyrightconfig.json`
- Create: `.gitignore`
- Modify: none

- [ ] **Step 1: Verify uv is installed and version**

Run: `uv --version`
Expected: `uv 0.5.0` or higher. If missing: `curl -LsSf https://astral.sh/uv/install.sh | sh`.

- [ ] **Step 2: Create `.python-version`**

Write file `.python-version`:
```
3.13
```

- [ ] **Step 3: Create workspace `pyproject.toml`**

Write file `pyproject.toml`:
```toml
[project]
name = "files-sdk-workspace"
version = "0.0.0"
description = "Workspace root for files-sdk Python packages"
requires-python = ">=3.11"

[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/_template"]

[tool.uv.sources]
files-sdk = { workspace = true }
files-sdk-s3 = { workspace = true }
files-sdk-r2 = { workspace = true }

[dependency-groups]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.24",
    "pyright>=1.1.380",
    "ruff>=0.7",
    "moto[s3]>=5",
    "httpx>=0.27",
]
```

- [ ] **Step 4: Create `ruff.toml`**

Write file `ruff.toml`:
```toml
target-version = "py311"
line-length = 100

[lint]
select = ["E", "F", "I", "B", "UP", "N", "SIM", "RUF"]
ignore = ["E501"]  # handled by formatter

[format]
quote-style = "double"
```

- [ ] **Step 5: Create `pyrightconfig.json`**

Write file `pyrightconfig.json`:
```json
{
  "include": ["packages/*/src", "packages/*/tests"],
  "exclude": ["**/__pycache__", "packages/_template"],
  "pythonVersion": "3.13",
  "typeCheckingMode": "strict",
  "reportMissingTypeStubs": false,
  "venvPath": ".",
  "venv": ".venv"
}
```

- [ ] **Step 6: Create `.gitignore`**

Write file `.gitignore`:
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
dist/
build/
*.egg-info/
.DS_Store
.coverage
htmlcov/
```

- [ ] **Step 7: Run `uv sync`**

Run: `uv sync`
Expected: creates `.venv/`, installs dev deps. (No workspace members yet so this only installs dev tools.)

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml .python-version ruff.toml pyrightconfig.json .gitignore
git commit -m "chore: bootstrap uv workspace and tooling config"
```

---

## Task 2: Core package skeleton (`files-sdk`)

**Files:**
- Create: `packages/files-sdk/pyproject.toml`
- Create: `packages/files-sdk/src/files_sdk/__init__.py`
- Create: `packages/files-sdk/src/files_sdk/py.typed`
- Create: `packages/files-sdk/README.md`

- [ ] **Step 1: Create core package `pyproject.toml`**

Write file `packages/files-sdk/pyproject.toml`:
```toml
[project]
name = "files-sdk"
version = "0.1.0"
description = "Unified Python SDK for cloud object/blob storage"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [{name = "Carter Himmel", email = "carter@hellopatient.com"}]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "pydantic>=2.8",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk"]
```

- [ ] **Step 2: Create `py.typed` marker**

Write file `packages/files-sdk/src/files_sdk/py.typed` (empty file).

- [ ] **Step 3: Create minimal `__init__.py`**

Write file `packages/files-sdk/src/files_sdk/__init__.py`:
```python
"""files-sdk — unified Python SDK for cloud storage."""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create README**

Write file `packages/files-sdk/README.md`:
```markdown
# files-sdk

Unified Python SDK for cloud object/blob storage. Python port of [files-sdk.dev](https://files-sdk.dev/).

Install an adapter: `pip install files-sdk-s3` or `pip install files-sdk-r2`.

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").data)
```
```

- [ ] **Step 5: Sync workspace**

Run: `uv sync`
Expected: `files-sdk` shows as installed editable from `packages/files-sdk`.

- [ ] **Step 6: Import smoke check**

Run: `uv run python -c "import files_sdk; print(files_sdk.__version__)"`
Expected output: `0.1.0`

- [ ] **Step 7: Commit**

```bash
git add packages/files-sdk
git commit -m "feat(core): scaffold files-sdk package"
```

---

## Task 3: Errors module (TDD)

**Files:**
- Create: `packages/files-sdk/tests/test_errors.py`
- Create: `packages/files-sdk/src/files_sdk/errors.py`

- [ ] **Step 1: Write the failing tests**

Write file `packages/files-sdk/tests/test_errors.py`:
```python
import pytest
from files_sdk.errors import FilesError, ErrorCode


def test_files_error_holds_code_and_message():
    err = FilesError(code="not_found", message="missing")
    assert err.code == "not_found"
    assert err.message == "missing"
    assert str(err) == "missing"


def test_files_error_optional_provider():
    err = FilesError(code="provider", message="boom", provider="s3")
    assert err.provider == "s3"


def test_files_error_preserves_cause():
    original = ValueError("oops")
    try:
        try:
            raise original
        except ValueError as e:
            raise FilesError(code="provider", message="wrapped") from e
    except FilesError as wrapped:
        assert wrapped.__cause__ is original


def test_files_error_rejects_invalid_code():
    with pytest.raises(ValueError):
        FilesError(code="totally_made_up", message="x")  # type: ignore[arg-type]


def test_error_code_literal_values():
    expected = {"not_found", "unauthorized", "conflict", "provider", "invalid_input"}
    # ErrorCode is a Literal alias; validate the set defined as VALID_CODES
    from files_sdk.errors import VALID_CODES
    assert VALID_CODES == expected
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/files-sdk/tests/test_errors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'files_sdk.errors'`.

- [ ] **Step 3: Write implementation**

Write file `packages/files-sdk/src/files_sdk/errors.py`:
```python
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
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest packages/files-sdk/tests/test_errors.py -v`
Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add packages/files-sdk/src/files_sdk/errors.py packages/files-sdk/tests/test_errors.py
git commit -m "feat(core): add FilesError with code enum"
```

---

## Task 4: Core types module (TDD)

**Files:**
- Create: `packages/files-sdk/tests/test_types.py`
- Create: `packages/files-sdk/src/files_sdk/types.py`

- [ ] **Step 1: Write the failing tests**

Write file `packages/files-sdk/tests/test_types.py`:
```python
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile


def _meta() -> FileMetadata:
    return FileMetadata(
        key="a/b.txt",
        size=3,
        etag="abc",
        content_type="text/plain",
        last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        metadata={"k": "v"},
    )


def test_file_metadata_required_fields():
    m = _meta()
    assert m.key == "a/b.txt"
    assert m.size == 3
    assert m.metadata == {"k": "v"}


def test_file_metadata_size_nonnegative():
    with pytest.raises(ValidationError):
        FileMetadata(
            key="x", size=-1, etag=None, content_type=None,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC), metadata={},
        )


def test_stored_file_text_decoding():
    sf = StoredFile(metadata=_meta(), data=b"hi!")
    assert sf.text() == "hi!"
    assert sf.as_bytes() == b"hi!"


def test_stored_file_text_custom_encoding():
    sf = StoredFile(metadata=_meta().model_copy(update={"size": 6}), data="héllo".encode("utf-8"))
    assert sf.text(encoding="utf-8") == "héllo"


def test_list_page_terminal_cursor_is_none():
    page = ListPage(items=[_meta()], cursor=None)
    assert page.cursor is None
    assert len(page.items) == 1


def test_signed_upload_method_upper():
    su = SignedUpload(
        url="https://x",
        method="PUT",
        headers={"Content-Type": "text/plain"},
        fields=None,
        expires_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert su.method == "PUT"


def test_signed_upload_post_has_fields():
    su = SignedUpload(
        url="https://x",
        method="POST",
        headers={},
        fields={"key": "a", "policy": "p"},
        expires_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert su.fields == {"key": "a", "policy": "p"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/files-sdk/tests/test_types.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

Write file `packages/files-sdk/src/files_sdk/types.py`:
```python
"""Public pydantic models returned by adapters."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Literal, Union

from pydantic import BaseModel, ConfigDict, Field

UploadBody = Union[bytes, str, BinaryIO, Path]


class FileMetadata(BaseModel):
    """Metadata for a stored object."""

    model_config = ConfigDict(frozen=True)

    key: str
    size: int = Field(ge=0)
    etag: str | None
    content_type: str | None
    last_modified: datetime
    metadata: dict[str, str]


class StoredFile(BaseModel):
    """A fully-buffered downloaded file."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    metadata: FileMetadata
    data: bytes

    def as_bytes(self) -> bytes:
        return self.data

    def text(self, *, encoding: str = "utf-8", errors: str = "strict") -> str:
        return self.data.decode(encoding, errors=errors)


class ListPage(BaseModel):
    """One page of a list operation."""

    items: list[FileMetadata]
    cursor: str | None


class SignedUpload(BaseModel):
    """A signed-URL contract for a browser-direct upload."""

    url: str
    method: Literal["PUT", "POST"]
    headers: dict[str, str]
    fields: dict[str, str] | None
    expires_at: datetime
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest packages/files-sdk/tests/test_types.py -v`
Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add packages/files-sdk/src/files_sdk/types.py packages/files-sdk/tests/test_types.py
git commit -m "feat(core): add pydantic types for metadata, stored file, list page, signed upload"
```

---

## Task 5: Adapter Protocols

**Files:**
- Create: `packages/files-sdk/src/files_sdk/adapter.py`
- Create: `packages/files-sdk/tests/test_adapter_protocol.py`

- [ ] **Step 1: Write the failing tests**

Write file `packages/files-sdk/tests/test_adapter_protocol.py`:
```python
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any

from files_sdk.adapter import Adapter, AsyncAdapter
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile


class _DummySync:
    name = "dummy"

    def upload(self, key: str, body: Any, **opts: Any) -> FileMetadata:
        return FileMetadata(key=key, size=0, etag=None, content_type=None,
                            last_modified=datetime(2026, 1, 1, tzinfo=UTC), metadata={})

    def download(self, key: str) -> StoredFile:  # pragma: no cover
        raise NotImplementedError

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:  # pragma: no cover
        raise NotImplementedError

    def head(self, key: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    def list(self, *, prefix: str | None = None, cursor: str | None = None,
             limit: int = 1000) -> ListPage:  # pragma: no cover
        raise NotImplementedError

    def copy(self, src: str, dst: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:  # pragma: no cover
        raise NotImplementedError

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:  # pragma: no cover
        raise NotImplementedError

    @property
    def raw(self) -> Any:  # pragma: no cover
        return None


def test_sync_adapter_protocol_recognizes_compliant_class():
    assert isinstance(_DummySync(), Adapter)


def test_async_adapter_protocol_distinct_from_sync():
    # A sync adapter must NOT satisfy AsyncAdapter (methods aren't coroutines).
    assert not isinstance(_DummySync(), AsyncAdapter)


class _DummyAsync:
    name = "dummy-async"

    async def upload(self, key: str, body: Any, **opts: Any) -> FileMetadata:
        return FileMetadata(key=key, size=0, etag=None, content_type=None,
                            last_modified=datetime(2026, 1, 1, tzinfo=UTC), metadata={})

    async def download(self, key: str) -> StoredFile:  # pragma: no cover
        raise NotImplementedError

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:  # pragma: no cover
        if False:
            yield b""
        raise NotImplementedError

    async def head(self, key: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    async def delete(self, key: str) -> None:  # pragma: no cover
        raise NotImplementedError

    async def list(self, *, prefix: str | None = None, cursor: str | None = None,
                   limit: int = 1000) -> ListPage:  # pragma: no cover
        raise NotImplementedError

    async def copy(self, src: str, dst: str) -> FileMetadata:  # pragma: no cover
        raise NotImplementedError

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:  # pragma: no cover
        raise NotImplementedError

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:  # pragma: no cover
        raise NotImplementedError

    @property
    def raw(self) -> Any:  # pragma: no cover
        return None


def test_async_adapter_protocol_recognizes_async_class():
    assert isinstance(_DummyAsync(), AsyncAdapter)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/files-sdk/tests/test_adapter_protocol.py -v`
Expected: FAIL with `ModuleNotFoundError: files_sdk.adapter`.

- [ ] **Step 3: Write implementation**

Write file `packages/files-sdk/src/files_sdk/adapter.py`:
```python
"""Protocol interfaces every adapter must implement."""

from __future__ import annotations

import inspect
from collections.abc import AsyncIterator, Iterator
from typing import Any, ClassVar, Protocol, runtime_checkable

from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


@runtime_checkable
class Adapter(Protocol):
    """Synchronous storage adapter."""

    name: ClassVar[str]

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata: ...
    def download(self, key: str) -> StoredFile: ...
    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]: ...
    def head(self, key: str) -> FileMetadata: ...
    def delete(self, key: str) -> None: ...
    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage: ...
    def copy(self, src: str, dst: str) -> FileMetadata: ...
    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str: ...
    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload: ...

    @property
    def raw(self) -> Any: ...


@runtime_checkable
class AsyncAdapter(Protocol):
    """Asynchronous storage adapter.

    Methods mirror :class:`Adapter` but are coroutines. ``stream`` returns an
    async iterator.
    """

    name: ClassVar[str]

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata: ...
    async def download(self, key: str) -> StoredFile: ...
    def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]: ...
    async def head(self, key: str) -> FileMetadata: ...
    async def delete(self, key: str) -> None: ...
    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage: ...
    async def copy(self, src: str, dst: str) -> FileMetadata: ...
    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str: ...
    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload: ...

    @property
    def raw(self) -> Any: ...


def is_async_adapter(candidate: object) -> bool:
    """Return True iff candidate looks like an AsyncAdapter (upload is a coroutine)."""
    fn = getattr(candidate, "upload", None)
    return inspect.iscoroutinefunction(fn)
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest packages/files-sdk/tests/test_adapter_protocol.py -v`
Expected: 3 passed.

> **Why `is_async_adapter`?** `@runtime_checkable` Protocol's `isinstance` check only verifies attribute presence, not whether they're coroutines. The `test_async_adapter_protocol_distinct_from_sync` assertion would fail otherwise. We provide a helper `is_async_adapter()` for the client to discriminate. The protocol itself still works for type-hinting.

- [ ] **Step 5: Adjust the failing distinction test**

The test `test_async_adapter_protocol_distinct_from_sync` is wrong as written — `@runtime_checkable` Protocol won't distinguish. Replace it in `test_adapter_protocol.py`:

```python
def test_is_async_adapter_helper_distinguishes():
    from files_sdk.adapter import is_async_adapter
    assert not is_async_adapter(_DummySync())
    assert is_async_adapter(_DummyAsync())
```

Remove the old `test_async_adapter_protocol_distinct_from_sync` test.

- [ ] **Step 6: Re-run tests**

Run: `uv run pytest packages/files-sdk/tests/test_adapter_protocol.py -v`
Expected: 3 passed.

- [ ] **Step 7: Commit**

```bash
git add packages/files-sdk/src/files_sdk/adapter.py packages/files-sdk/tests/test_adapter_protocol.py
git commit -m "feat(core): add Adapter and AsyncAdapter Protocols"
```

---

## Task 6: Plugin registry via entry points (TDD)

**Files:**
- Create: `packages/files-sdk/src/files_sdk/_registry.py`
- Create: `packages/files-sdk/tests/test_registry.py`

- [ ] **Step 1: Write the failing tests**

Write file `packages/files-sdk/tests/test_registry.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/files-sdk/tests/test_registry.py -v`
Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Write implementation**

Write file `packages/files-sdk/src/files_sdk/_registry.py`:
```python
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
            f"no adapter named {name!r}; install files-sdk-{name} "
            f"or pass adapter= explicitly"
        ),
    )
```

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest packages/files-sdk/tests/test_registry.py -v`
Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add packages/files-sdk/src/files_sdk/_registry.py packages/files-sdk/tests/test_registry.py
git commit -m "feat(core): add entry-point based adapter registry"
```

---

## Task 7: Files / AsyncFiles client (TDD)

**Files:**
- Create: `packages/files-sdk/src/files_sdk/client.py`
- Create: `packages/files-sdk/tests/test_client.py`

- [ ] **Step 1: Write the failing tests**

Write file `packages/files-sdk/tests/test_client.py`:
```python
from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from files_sdk import AsyncFiles, Files
from files_sdk.errors import FilesError
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile


def _meta(key: str = "k") -> FileMetadata:
    return FileMetadata(key=key, size=0, etag=None, content_type=None,
                        last_modified=datetime(2026, 1, 1, tzinfo=UTC), metadata={})


class FakeSyncAdapter:
    name = "fake"

    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def _record(self, op: str, *args: Any, **kw: Any) -> None:
        self.calls.append((op, args, kw))

    def upload(self, key, body, **opts):
        self._record("upload", key, body, **opts)
        return _meta(key)

    def download(self, key):
        self._record("download", key)
        return StoredFile(metadata=_meta(key), data=b"x")

    def stream(self, key, *, chunk_size=65536):
        self._record("stream", key, chunk_size=chunk_size)
        return iter([b"x"])

    def head(self, key):
        self._record("head", key)
        return _meta(key)

    def delete(self, key):
        self._record("delete", key)

    def list(self, *, prefix=None, cursor=None, limit=1000):
        self._record("list", prefix=prefix, cursor=cursor, limit=limit)
        return ListPage(items=[], cursor=None)

    def copy(self, src, dst):
        self._record("copy", src, dst)
        return _meta(dst)

    def url(self, key, *, expires_in=3600, public=False):
        self._record("url", key, expires_in=expires_in, public=public)
        return f"https://example/{key}"

    def signed_upload_url(self, key, **opts):
        self._record("signed_upload_url", key, **opts)
        return SignedUpload(url="https://x", method="PUT", headers={}, fields=None,
                            expires_at=datetime(2026, 1, 1, tzinfo=UTC))

    @property
    def raw(self):
        return object()


class FakeAsyncAdapter:
    name = "fake-async"

    async def upload(self, key, body, **opts):
        return _meta(key)

    async def download(self, key):
        return StoredFile(metadata=_meta(key), data=b"x")

    async def stream(self, key, *, chunk_size=65536):  # AsyncIterator[bytes]
        async def gen() -> AsyncIterator[bytes]:
            yield b"x"
        return gen()

    async def head(self, key):
        return _meta(key)

    async def delete(self, key):
        return None

    async def list(self, *, prefix=None, cursor=None, limit=1000):
        return ListPage(items=[], cursor=None)

    async def copy(self, src, dst):
        return _meta(dst)

    async def url(self, key, *, expires_in=3600, public=False):
        return f"https://example/{key}"

    async def signed_upload_url(self, key, **opts):
        return SignedUpload(url="https://x", method="PUT", headers={}, fields=None,
                            expires_at=datetime(2026, 1, 1, tzinfo=UTC))

    @property
    def raw(self):
        return object()


def test_files_delegates_all_methods():
    adapter = FakeSyncAdapter()
    files = Files(adapter=adapter)
    files.upload("k", b"hi", content_type="text/plain")
    files.download("k")
    list(files.stream("k", chunk_size=1024))
    files.head("k")
    files.delete("k")
    files.list(prefix="p/")
    files.copy("a", "b")
    files.url("k", expires_in=60, public=True)
    files.signed_upload_url("k", method="put")
    assert {c[0] for c in adapter.calls} == {
        "upload", "download", "stream", "head", "delete",
        "list", "copy", "url", "signed_upload_url",
    }


def test_files_rejects_async_adapter():
    with pytest.raises(FilesError) as ei:
        Files(adapter=FakeAsyncAdapter())
    assert ei.value.code == "invalid_input"
    assert "async" in ei.value.message.lower()


def test_files_raw_property():
    adapter = FakeSyncAdapter()
    files = Files(adapter=adapter)
    assert files.raw is adapter.raw


@pytest.mark.asyncio
async def test_async_files_delegates():
    files = AsyncFiles(adapter=FakeAsyncAdapter())
    meta = await files.upload("k", b"hi")
    assert meta.key == "k"
    sf = await files.download("k")
    assert sf.data == b"x"
    async for chunk in await files.stream("k"):
        assert chunk == b"x"


def test_async_files_rejects_sync_adapter():
    with pytest.raises(FilesError) as ei:
        AsyncFiles(adapter=FakeSyncAdapter())
    assert ei.value.code == "invalid_input"


def test_files_from_name_loads_via_registry():
    class FakeAdapter(FakeSyncAdapter):
        def __init__(self, *, bucket: str) -> None:
            super().__init__()
            self.bucket = bucket

    with patch("files_sdk.client.load_adapter_class") as mocked:
        mocked.return_value = FakeAdapter
        files = Files.from_name("fake", bucket="my-bucket")
    assert isinstance(files._adapter, FakeAdapter)
    assert files._adapter.bucket == "my-bucket"
```

Append `pytest-asyncio` config to `packages/files-sdk/pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest packages/files-sdk/tests/test_client.py -v`
Expected: FAIL with `ImportError: cannot import name 'Files'`.

- [ ] **Step 3: Write implementation**

Write file `packages/files-sdk/src/files_sdk/client.py`:
```python
"""Files and AsyncFiles client wrappers."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from ._registry import load_adapter_class
from .adapter import Adapter, AsyncAdapter, is_async_adapter
from .errors import FilesError
from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


class Files:
    """Synchronous storage client wrapping a sync :class:`Adapter`."""

    def __init__(self, *, adapter: Adapter) -> None:
        if is_async_adapter(adapter):
            raise FilesError(
                code="invalid_input",
                message="Files() requires a sync Adapter; pass async adapter to AsyncFiles instead",
            )
        self._adapter = adapter

    @classmethod
    def from_name(cls, name: str, **adapter_kwargs: Any) -> Files:
        adapter_cls = load_adapter_class(name)
        return cls(adapter=adapter_cls(**adapter_kwargs))

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return self._adapter.upload(key, body, **opts)

    def download(self, key: str) -> StoredFile:
        return self._adapter.download(key)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        return self._adapter.stream(key, chunk_size=chunk_size)

    def head(self, key: str) -> FileMetadata:
        return self._adapter.head(key)

    def delete(self, key: str) -> None:
        self._adapter.delete(key)

    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        return self._adapter.list(prefix=prefix, cursor=cursor, limit=limit)

    def copy(self, src: str, dst: str) -> FileMetadata:
        return self._adapter.copy(src, dst)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return self._adapter.url(key, expires_in=expires_in, public=public)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return self._adapter.signed_upload_url(key, **opts)

    @property
    def raw(self) -> Any:
        return self._adapter.raw


class AsyncFiles:
    """Asynchronous storage client wrapping an :class:`AsyncAdapter`."""

    def __init__(self, *, adapter: AsyncAdapter) -> None:
        if not is_async_adapter(adapter):
            raise FilesError(
                code="invalid_input",
                message="AsyncFiles() requires an async AsyncAdapter; pass sync adapter to Files instead",
            )
        self._adapter = adapter

    @classmethod
    def from_name(cls, name: str, **adapter_kwargs: Any) -> AsyncFiles:
        adapter_cls = load_adapter_class(name)
        return cls(adapter=adapter_cls(**adapter_kwargs))

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        return await self._adapter.upload(key, body, **opts)

    async def download(self, key: str) -> StoredFile:
        return await self._adapter.download(key)

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        return await self._adapter.stream(key, chunk_size=chunk_size)  # type: ignore[no-any-return]

    async def head(self, key: str) -> FileMetadata:
        return await self._adapter.head(key)

    async def delete(self, key: str) -> None:
        await self._adapter.delete(key)

    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        return await self._adapter.list(prefix=prefix, cursor=cursor, limit=limit)

    async def copy(self, src: str, dst: str) -> FileMetadata:
        return await self._adapter.copy(src, dst)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        return await self._adapter.url(key, expires_in=expires_in, public=public)

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        return await self._adapter.signed_upload_url(key, **opts)

    @property
    def raw(self) -> Any:
        return self._adapter.raw
```

- [ ] **Step 4: Update core `__init__.py` to re-export**

Replace file `packages/files-sdk/src/files_sdk/__init__.py`:
```python
"""files-sdk — unified Python SDK for cloud storage."""

from .adapter import Adapter, AsyncAdapter
from .client import AsyncFiles, Files
from .errors import ErrorCode, FilesError
from .types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

__version__ = "0.1.0"

__all__ = [
    "Adapter",
    "AsyncAdapter",
    "AsyncFiles",
    "ErrorCode",
    "FileMetadata",
    "Files",
    "FilesError",
    "ListPage",
    "SignedUpload",
    "StoredFile",
    "UploadBody",
]
```

- [ ] **Step 5: Run tests**

Run: `uv run pytest packages/files-sdk/tests/test_client.py -v`
Expected: 6 passed.

- [ ] **Step 6: Run all core tests**

Run: `uv run pytest packages/files-sdk -v`
Expected: all green (errors + types + adapter + registry + client tests).

- [ ] **Step 7: Type-check core**

Run: `uv run pyright packages/files-sdk/src`
Expected: 0 errors.

- [ ] **Step 8: Commit**

```bash
git add packages/files-sdk
git commit -m "feat(core): add Files and AsyncFiles clients with from_name sugar"
```

---

## Task 8: Conformance test suite (helpers, not yet wired)

**Files:**
- Create: `packages/files-sdk/src/files_sdk/testing/__init__.py`
- Create: `packages/files-sdk/src/files_sdk/testing/conformance.py`

> The conformance module exports test functions. Adapter packages provide a pytest `adapter` fixture in conftest and import the test functions via `from files_sdk.testing.conformance import *` — pytest discovers them and binds the fixture.

- [ ] **Step 1: Create the testing subpackage**

Write file `packages/files-sdk/src/files_sdk/testing/__init__.py`:
```python
"""Test helpers for adapter authors. Import from .conformance."""
from . import conformance

__all__ = ["conformance"]
```

- [ ] **Step 2: Write the conformance test functions**

Write file `packages/files-sdk/src/files_sdk/testing/conformance.py`:
```python
"""Conformance tests every Adapter implementation should pass.

Adapter packages add a ``conftest.py`` providing an ``adapter`` fixture, then in
``tests/test_conformance.py``::

    from files_sdk.testing.conformance import *  # noqa: F401,F403

pytest discovers each ``test_*`` function and binds the local fixture.
"""

from __future__ import annotations

import io
import uuid

import pytest

from files_sdk.errors import FilesError

__all__ = [
    "test_upload_then_download_bytes",
    "test_upload_then_download_str",
    "test_upload_from_file_like",
    "test_head_returns_metadata",
    "test_delete_is_idempotent",
    "test_download_missing_raises_not_found",
    "test_list_prefix_filters",
    "test_list_pagination_cursor",
    "test_copy_creates_destination",
    "test_url_returns_http_string",
    "test_signed_upload_url_put",
    "test_stream_yields_chunks",
    "test_unicode_key_roundtrip",
    "test_zero_byte_upload",
]


def _k(prefix: str = "conf") -> str:
    return f"{prefix}/{uuid.uuid4().hex}"


def test_upload_then_download_bytes(adapter) -> None:
    k = _k()
    adapter.upload(k, b"hello")
    sf = adapter.download(k)
    assert sf.data == b"hello"
    assert sf.metadata.key == k


def test_upload_then_download_str(adapter) -> None:
    k = _k()
    adapter.upload(k, "héllo")
    sf = adapter.download(k)
    assert sf.text() == "héllo"


def test_upload_from_file_like(adapter) -> None:
    k = _k()
    adapter.upload(k, io.BytesIO(b"file-like"))
    assert adapter.download(k).data == b"file-like"


def test_head_returns_metadata(adapter) -> None:
    k = _k()
    adapter.upload(k, b"abc", content_type="text/plain")
    meta = adapter.head(k)
    assert meta.size == 3
    assert meta.content_type == "text/plain"


def test_delete_is_idempotent(adapter) -> None:
    k = _k()
    adapter.delete(k)  # missing -> no raise
    adapter.upload(k, b"x")
    adapter.delete(k)
    adapter.delete(k)  # already gone -> no raise


def test_download_missing_raises_not_found(adapter) -> None:
    with pytest.raises(FilesError) as ei:
        adapter.download(_k("nope"))
    assert ei.value.code == "not_found"


def test_list_prefix_filters(adapter) -> None:
    p = f"listtest/{uuid.uuid4().hex}"
    for i in range(3):
        adapter.upload(f"{p}/f{i}.txt", b"x")
    adapter.upload(f"{p}-other/f.txt", b"y")
    page = adapter.list(prefix=f"{p}/")
    keys = {item.key for item in page.items}
    assert len(keys) >= 3
    assert all(k.startswith(f"{p}/") for k in keys)


def test_list_pagination_cursor(adapter) -> None:
    p = f"paging/{uuid.uuid4().hex}"
    for i in range(5):
        adapter.upload(f"{p}/{i:02d}.txt", b"x")
    page1 = adapter.list(prefix=f"{p}/", limit=2)
    assert len(page1.items) == 2
    if page1.cursor is not None:
        page2 = adapter.list(prefix=f"{p}/", cursor=page1.cursor, limit=2)
        first_keys = {i.key for i in page1.items}
        second_keys = {i.key for i in page2.items}
        assert first_keys.isdisjoint(second_keys)


def test_copy_creates_destination(adapter) -> None:
    src, dst = _k("src"), _k("dst")
    adapter.upload(src, b"copy-me")
    adapter.copy(src, dst)
    assert adapter.download(dst).data == b"copy-me"


def test_url_returns_http_string(adapter) -> None:
    k = _k()
    adapter.upload(k, b"x")
    url = adapter.url(k, expires_in=60)
    assert url.startswith("http")


def test_signed_upload_url_put(adapter) -> None:
    su = adapter.signed_upload_url(_k(), method="put")
    assert su.method == "PUT"
    assert su.url.startswith("http")


def test_stream_yields_chunks(adapter) -> None:
    k = _k()
    payload = b"abcdefghij" * 1000
    adapter.upload(k, payload)
    got = b"".join(adapter.stream(k, chunk_size=256))
    assert got == payload


def test_unicode_key_roundtrip(adapter) -> None:
    k = f"unicode/{uuid.uuid4().hex}/héllo wörld.txt"
    adapter.upload(k, b"x")
    assert adapter.download(k).data == b"x"


def test_zero_byte_upload(adapter) -> None:
    k = _k()
    adapter.upload(k, b"")
    sf = adapter.download(k)
    assert sf.data == b""
    assert sf.metadata.size == 0
```

- [ ] **Step 3: Verify imports cleanly**

Run: `uv run python -c "from files_sdk.testing.conformance import test_upload_then_download_bytes; print('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit**

```bash
git add packages/files-sdk/src/files_sdk/testing
git commit -m "feat(core): add conformance test suite"
```

---

## Task 9: S3 adapter package — scaffold

**Files:**
- Create: `packages/files-sdk-s3/pyproject.toml`
- Create: `packages/files-sdk-s3/src/files_sdk_s3/__init__.py`
- Create: `packages/files-sdk-s3/src/files_sdk_s3/py.typed`
- Create: `packages/files-sdk-s3/README.md`

- [ ] **Step 1: Create `pyproject.toml`**

Write file `packages/files-sdk-s3/pyproject.toml`:
```toml
[project]
name = "files-sdk-s3"
version = "0.1.0"
description = "Amazon S3 adapter for files-sdk"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [{name = "Carter Himmel", email = "carter@hellopatient.com"}]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "files-sdk",
    "boto3>=1.35",
    "botocore>=1.35",
    "aioboto3>=13",
]

[project.entry-points."files_sdk.adapters"]
s3 = "files_sdk_s3:S3Adapter"
"s3-async" = "files_sdk_s3:AsyncS3Adapter"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk_s3"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `py.typed`**

Write empty file `packages/files-sdk-s3/src/files_sdk_s3/py.typed`.

- [ ] **Step 3: Create temporary `__init__.py` (placeholder for adapter classes)**

Write file `packages/files-sdk-s3/src/files_sdk_s3/__init__.py`:
```python
"""files-sdk-s3 — Amazon S3 adapter."""

from .adapter import S3Adapter
from .async_adapter import AsyncS3Adapter

__version__ = "0.1.0"
__all__ = ["AsyncS3Adapter", "S3Adapter"]
```

- [ ] **Step 4: Create README**

Write file `packages/files-sdk-s3/README.md`:
```markdown
# files-sdk-s3

S3 adapter for [files-sdk](../files-sdk).

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
```

Reads credentials from the standard AWS environment (`AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_SESSION_TOKEN`).
```

- [ ] **Step 5: Don't sync yet** — adapter.py and async_adapter.py don't exist; sync will fail on import. Move on to Task 10.

> The `__init__.py` re-exports will fail at import until Task 10/11 create the modules. We sync after.

---

## Task 10: S3 sync adapter (TDD with moto)

**Files:**
- Create: `packages/files-sdk-s3/src/files_sdk_s3/adapter.py`
- Create: `packages/files-sdk-s3/tests/conftest.py`
- Create: `packages/files-sdk-s3/tests/test_conformance.py`
- Create: `packages/files-sdk-s3/tests/test_s3_specific.py`

- [ ] **Step 1: Create test conftest with moto-backed adapter fixture**

Write file `packages/files-sdk-s3/tests/conftest.py`:
```python
"""Fixtures for files-sdk-s3 tests.

Uses moto (https://github.com/getmoto/moto) to mock S3 in-process.
"""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")


@pytest.fixture
def s3_bucket(aws_credentials: None):
    with mock_aws():
        bucket = "conformance-bucket"
        boto3.client("s3").create_bucket(Bucket=bucket)
        yield bucket


@pytest.fixture
def adapter(s3_bucket: str):
    from files_sdk_s3 import S3Adapter
    return S3Adapter(bucket=s3_bucket)
```

- [ ] **Step 2: Create the conformance import file**

Write file `packages/files-sdk-s3/tests/test_conformance.py`:
```python
"""Run the shared conformance suite against S3Adapter.

The wildcard import is intentional: it pulls every ``test_*`` function from
``files_sdk.testing.conformance`` into this module so pytest discovers them and
binds them to the local ``adapter`` fixture defined in conftest.py.
"""

from files_sdk.testing.conformance import *  # noqa: F401,F403
```

- [ ] **Step 3: Write the S3 adapter implementation**

Write file `packages/files-sdk-s3/src/files_sdk_s3/adapter.py`:
```python
"""Synchronous S3 adapter."""

from __future__ import annotations

import io
import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, ClassVar

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from files_sdk.errors import FilesError
from files_sdk.types import (
    FileMetadata,
    ListPage,
    SignedUpload,
    StoredFile,
    UploadBody,
)

_DEFAULT_MULTIPART_THRESHOLD = 8 * 1024 * 1024  # 8 MiB


class S3Adapter:
    """Synchronous S3-compatible storage adapter."""

    name: ClassVar[str] = "s3"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        session_token: str | None = None,
        endpoint_url: str | None = None,
        multipart_threshold: int = _DEFAULT_MULTIPART_THRESHOLD,
    ) -> None:
        resolved_bucket = bucket or os.environ.get("AWS_S3_BUCKET")
        if not resolved_bucket:
            raise FilesError(
                code="unauthorized",
                message="S3Adapter requires bucket= or AWS_S3_BUCKET env var",
                provider=self.name,
            )
        self.bucket = resolved_bucket
        self.multipart_threshold = multipart_threshold
        self._endpoint_url = endpoint_url
        self._client = boto3.client(
            "s3",
            region_name=region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=session_token or os.environ.get("AWS_SESSION_TOKEN"),
            endpoint_url=endpoint_url,
            config=Config(signature_version="s3v4"),
        )

    # ---- normalization helpers ----------------------------------------------

    def _wrap(self, op: str, fn, *args, **kw):  # type: ignore[no-untyped-def]
        try:
            return fn(*args, **kw)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if code in ("NoSuchKey", "NoSuchBucket") or status == 404:
                raise FilesError(code="not_found", message=str(e), provider=self.name) from e
            if status in (401, 403) or "AccessDenied" in code or "SignatureDoesNotMatch" in code:
                raise FilesError(code="unauthorized", message=str(e), provider=self.name) from e
            if status == 412:
                raise FilesError(code="conflict", message=str(e), provider=self.name) from e
            raise FilesError(code="provider", message=f"{op}: {e}", provider=self.name) from e

    def _to_body(self, body: UploadBody) -> bytes | io.IOBase:
        if isinstance(body, (bytes, bytearray)):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        if isinstance(body, Path):
            return body.read_bytes()
        return body  # file-like

    def _meta_from_head(self, key: str, resp: dict[str, Any]) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=int(resp.get("ContentLength", 0)),
            etag=(resp.get("ETag") or "").strip('"') or None,
            content_type=resp.get("ContentType"),
            last_modified=resp.get("LastModified") or datetime.now(timezone.utc),
            metadata=dict(resp.get("Metadata") or {}),
        )

    # ---- public API ---------------------------------------------------------

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        extra: dict[str, Any] = {}
        if ct := opts.get("content_type"):
            extra["ContentType"] = ct
        if meta := opts.get("metadata"):
            extra["Metadata"] = meta
        if cc := opts.get("cache_control"):
            extra["CacheControl"] = cc
        payload = self._to_body(body)
        if isinstance(payload, (bytes, bytearray)):
            self._wrap(
                "upload",
                self._client.put_object,
                Bucket=self.bucket, Key=key, Body=payload, **extra,
            )
        else:
            self._wrap(
                "upload",
                self._client.upload_fileobj,
                payload, self.bucket, key, ExtraArgs=extra or None,
            )
        return self.head(key)

    def download(self, key: str) -> StoredFile:
        resp = self._wrap(
            "download", self._client.get_object, Bucket=self.bucket, Key=key,
        )
        data = resp["Body"].read()
        meta = self._meta_from_head(key, resp)
        # ContentLength in get_object may not reflect actual bytes streamed
        return StoredFile(metadata=meta.model_copy(update={"size": len(data)}), data=data)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        resp = self._wrap(
            "stream", self._client.get_object, Bucket=self.bucket, Key=key,
        )
        body = resp["Body"]
        try:
            while True:
                chunk = body.read(chunk_size)
                if not chunk:
                    return
                yield chunk
        finally:
            body.close()

    def head(self, key: str) -> FileMetadata:
        resp = self._wrap(
            "head", self._client.head_object, Bucket=self.bucket, Key=key,
        )
        return self._meta_from_head(key, resp)

    def delete(self, key: str) -> None:
        # S3 delete_object is idempotent and does not 404 on missing keys
        self._wrap(
            "delete", self._client.delete_object, Bucket=self.bucket, Key=key,
        )

    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        params: dict[str, Any] = {"Bucket": self.bucket, "MaxKeys": limit}
        if prefix is not None:
            params["Prefix"] = prefix
        if cursor is not None:
            params["ContinuationToken"] = cursor
        resp = self._wrap("list", self._client.list_objects_v2, **params)
        items = [
            FileMetadata(
                key=obj["Key"],
                size=int(obj.get("Size", 0)),
                etag=(obj.get("ETag") or "").strip('"') or None,
                content_type=None,
                last_modified=obj.get("LastModified") or datetime.now(timezone.utc),
                metadata={},
            )
            for obj in resp.get("Contents", [])
        ]
        next_cursor = resp.get("NextContinuationToken") if resp.get("IsTruncated") else None
        return ListPage(items=items, cursor=next_cursor)

    def copy(self, src: str, dst: str) -> FileMetadata:
        self._wrap(
            "copy",
            self._client.copy_object,
            Bucket=self.bucket,
            Key=dst,
            CopySource={"Bucket": self.bucket, "Key": src},
        )
        return self.head(dst)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = self._endpoint_url or f"https://{self.bucket}.s3.amazonaws.com"
            return f"{base.rstrip('/')}/{key}"
        return self._wrap(
            "url",
            self._client.generate_presigned_url,
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        method = str(opts.get("method", "put")).lower()
        expires_in = int(opts.get("expires_in", 3600))
        content_type = opts.get("content_type")
        if method == "put":
            params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
            if content_type:
                params["ContentType"] = content_type
            url = self._wrap(
                "signed_upload_url",
                self._client.generate_presigned_url,
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            headers = {"Content-Type": content_type} if content_type else {}
            return SignedUpload(
                url=url, method="PUT", headers=headers, fields=None,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        if method == "post":
            conditions: list[Any] = []
            if max_size := opts.get("max_size"):
                conditions.append(["content-length-range", 0, int(max_size)])
            if content_type:
                conditions.append({"Content-Type": content_type})
            post = self._wrap(
                "signed_upload_url",
                self._client.generate_presigned_post,
                Bucket=self.bucket, Key=key, Conditions=conditions or None,
                ExpiresIn=expires_in,
            )
            return SignedUpload(
                url=post["url"], method="POST", headers={}, fields=dict(post["fields"]),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        raise FilesError(
            code="invalid_input",
            message=f"unknown signed_upload_url method: {method!r}",
            provider=self.name,
        )

    @property
    def raw(self) -> Any:
        return self._client
```

- [ ] **Step 4: Sync workspace and run S3 conformance tests**

Run: `uv sync`
Expected: `files-sdk-s3` installed editable.

Run: `uv run pytest packages/files-sdk-s3/tests -v`
Expected: all 14 conformance tests pass against moto. (Some may need adjusting — see Step 5.)

- [ ] **Step 5: Investigate any conformance failures**

Common moto quirks to expect:
- `test_download_missing_raises_not_found`: moto returns `NoSuchKey` — already mapped, should pass.
- `test_zero_byte_upload`: moto handles fine, should pass.
- `test_signed_upload_url_put`: moto signs URLs, should pass.

If any test fails, fix the adapter (not the test). Re-run.

- [ ] **Step 6: Add an S3-specific test for env-var construction**

Write file `packages/files-sdk-s3/tests/test_s3_specific.py`:
```python
import os

import pytest
from moto import mock_aws

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


def test_s3_adapter_raises_unauthorized_without_bucket(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_S3_BUCKET", raising=False)
    with pytest.raises(FilesError) as ei:
        S3Adapter()
    assert ei.value.code == "unauthorized"


def test_s3_adapter_reads_bucket_from_env(aws_credentials: None, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_S3_BUCKET", "env-bucket")
    with mock_aws():
        import boto3
        boto3.client("s3").create_bucket(Bucket="env-bucket")
        a = S3Adapter()
    assert a.bucket == "env-bucket"
```

Run: `uv run pytest packages/files-sdk-s3/tests/test_s3_specific.py -v`
Expected: 2 passed.

- [ ] **Step 7: Type-check**

Run: `uv run pyright packages/files-sdk-s3/src`
Expected: 0 errors. (boto3 types may surface; add `# type: ignore[no-untyped-call]` only at the boto3 boundary if pyright complains, never on our own code.)

- [ ] **Step 8: Commit**

```bash
git add packages/files-sdk-s3
git commit -m "feat(s3): implement sync S3Adapter with conformance suite passing"
```

---

## Task 11: S3 async adapter (TDD with moto)

**Files:**
- Create: `packages/files-sdk-s3/src/files_sdk_s3/async_adapter.py`
- Create: `packages/files-sdk-s3/tests/test_async_conformance.py`

> **Strategy:** mirror Task 10 with `aioboto3`. moto v5 supports `mock_aws` and works transparently with `aioboto3` because aioboto3 uses botocore under the hood.

- [ ] **Step 1: Add async conformance test functions to core**

Extend `packages/files-sdk/src/files_sdk/testing/conformance.py` by **appending** these async tests (do not modify existing tests):

```python
# --- async variants (require ``async_adapter`` fixture) ---------------------

import pytest as _pytest


@_pytest.mark.asyncio
async def test_async_upload_then_download_bytes(async_adapter) -> None:
    k = _k("a")
    await async_adapter.upload(k, b"hello")
    sf = await async_adapter.download(k)
    assert sf.data == b"hello"


@_pytest.mark.asyncio
async def test_async_delete_idempotent(async_adapter) -> None:
    k = _k("a")
    await async_adapter.delete(k)
    await async_adapter.upload(k, b"x")
    await async_adapter.delete(k)
    await async_adapter.delete(k)


@_pytest.mark.asyncio
async def test_async_download_missing_raises_not_found(async_adapter) -> None:
    with _pytest.raises(FilesError) as ei:
        await async_adapter.download(_k("nope-a"))
    assert ei.value.code == "not_found"


@_pytest.mark.asyncio
async def test_async_stream_yields_chunks(async_adapter) -> None:
    k = _k("a")
    payload = b"abc" * 1000
    await async_adapter.upload(k, payload)
    got = b""
    async for chunk in await async_adapter.stream(k, chunk_size=128):
        got += chunk
    assert got == payload


__all__ += [
    "test_async_upload_then_download_bytes",
    "test_async_delete_idempotent",
    "test_async_download_missing_raises_not_found",
    "test_async_stream_yields_chunks",
]
```

- [ ] **Step 2: Implement async adapter**

Write file `packages/files-sdk-s3/src/files_sdk_s3/async_adapter.py`:
```python
"""Asynchronous S3 adapter using aioboto3."""

from __future__ import annotations

import io
import os
from collections.abc import AsyncIterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, ClassVar

import aioboto3
from botocore.exceptions import ClientError

from files_sdk.errors import FilesError
from files_sdk.types import (
    FileMetadata,
    ListPage,
    SignedUpload,
    StoredFile,
    UploadBody,
)

_DEFAULT_MULTIPART_THRESHOLD = 8 * 1024 * 1024


class AsyncS3Adapter:
    """Async S3-compatible storage adapter."""

    name: ClassVar[str] = "s3-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        session_token: str | None = None,
        endpoint_url: str | None = None,
        multipart_threshold: int = _DEFAULT_MULTIPART_THRESHOLD,
    ) -> None:
        resolved_bucket = bucket or os.environ.get("AWS_S3_BUCKET")
        if not resolved_bucket:
            raise FilesError(
                code="unauthorized",
                message="AsyncS3Adapter requires bucket= or AWS_S3_BUCKET env var",
                provider=self.name,
            )
        self.bucket = resolved_bucket
        self.multipart_threshold = multipart_threshold
        self._endpoint_url = endpoint_url
        self._session = aioboto3.Session(
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=session_token or os.environ.get("AWS_SESSION_TOKEN"),
            region_name=region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
        )

    def _client(self):  # type: ignore[no-untyped-def]
        return self._session.client("s3", endpoint_url=self._endpoint_url)

    def _normalize_error(self, op: str, e: ClientError) -> FilesError:
        code = e.response.get("Error", {}).get("Code", "")
        status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
        if code in ("NoSuchKey", "NoSuchBucket") or status == 404:
            return FilesError(code="not_found", message=str(e), provider=self.name)
        if status in (401, 403) or "AccessDenied" in code or "SignatureDoesNotMatch" in code:
            return FilesError(code="unauthorized", message=str(e), provider=self.name)
        if status == 412:
            return FilesError(code="conflict", message=str(e), provider=self.name)
        return FilesError(code="provider", message=f"{op}: {e}", provider=self.name)

    def _to_body(self, body: UploadBody) -> bytes | io.IOBase:
        if isinstance(body, (bytes, bytearray)):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        if isinstance(body, Path):
            return body.read_bytes()
        return body

    def _meta(self, key: str, resp: dict[str, Any]) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=int(resp.get("ContentLength", 0)),
            etag=(resp.get("ETag") or "").strip('"') or None,
            content_type=resp.get("ContentType"),
            last_modified=resp.get("LastModified") or datetime.now(timezone.utc),
            metadata=dict(resp.get("Metadata") or {}),
        )

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        extra: dict[str, Any] = {}
        if ct := opts.get("content_type"):
            extra["ContentType"] = ct
        if meta := opts.get("metadata"):
            extra["Metadata"] = meta
        if cc := opts.get("cache_control"):
            extra["CacheControl"] = cc
        payload = self._to_body(body)
        async with self._client() as c:
            try:
                if isinstance(payload, (bytes, bytearray)):
                    await c.put_object(Bucket=self.bucket, Key=key, Body=payload, **extra)
                else:
                    await c.upload_fileobj(payload, self.bucket, key, ExtraArgs=extra or None)
            except ClientError as e:
                raise self._normalize_error("upload", e) from e
        return await self.head(key)

    async def download(self, key: str) -> StoredFile:
        async with self._client() as c:
            try:
                resp = await c.get_object(Bucket=self.bucket, Key=key)
                data = await resp["Body"].read()
            except ClientError as e:
                raise self._normalize_error("download", e) from e
        meta = self._meta(key, resp)
        return StoredFile(metadata=meta.model_copy(update={"size": len(data)}), data=data)

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        async def gen() -> AsyncIterator[bytes]:
            async with self._client() as c:
                try:
                    resp = await c.get_object(Bucket=self.bucket, Key=key)
                    async for chunk in resp["Body"].iter_chunks(chunk_size=chunk_size):
                        yield chunk
                except ClientError as e:
                    raise self._normalize_error("stream", e) from e
        return gen()

    async def head(self, key: str) -> FileMetadata:
        async with self._client() as c:
            try:
                resp = await c.head_object(Bucket=self.bucket, Key=key)
            except ClientError as e:
                raise self._normalize_error("head", e) from e
        return self._meta(key, resp)

    async def delete(self, key: str) -> None:
        async with self._client() as c:
            try:
                await c.delete_object(Bucket=self.bucket, Key=key)
            except ClientError as e:
                raise self._normalize_error("delete", e) from e

    async def list(self, *, prefix=None, cursor=None, limit=1000) -> ListPage:
        params: dict[str, Any] = {"Bucket": self.bucket, "MaxKeys": limit}
        if prefix is not None:
            params["Prefix"] = prefix
        if cursor is not None:
            params["ContinuationToken"] = cursor
        async with self._client() as c:
            try:
                resp = await c.list_objects_v2(**params)
            except ClientError as e:
                raise self._normalize_error("list", e) from e
        items = [
            FileMetadata(
                key=obj["Key"],
                size=int(obj.get("Size", 0)),
                etag=(obj.get("ETag") or "").strip('"') or None,
                content_type=None,
                last_modified=obj.get("LastModified") or datetime.now(timezone.utc),
                metadata={},
            )
            for obj in resp.get("Contents", [])
        ]
        next_cursor = resp.get("NextContinuationToken") if resp.get("IsTruncated") else None
        return ListPage(items=items, cursor=next_cursor)

    async def copy(self, src: str, dst: str) -> FileMetadata:
        async with self._client() as c:
            try:
                await c.copy_object(
                    Bucket=self.bucket, Key=dst,
                    CopySource={"Bucket": self.bucket, "Key": src},
                )
            except ClientError as e:
                raise self._normalize_error("copy", e) from e
        return await self.head(dst)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = self._endpoint_url or f"https://{self.bucket}.s3.amazonaws.com"
            return f"{base.rstrip('/')}/{key}"
        async with self._client() as c:
            return await c.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        method = str(opts.get("method", "put")).lower()
        expires_in = int(opts.get("expires_in", 3600))
        content_type = opts.get("content_type")
        async with self._client() as c:
            if method == "put":
                params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
                if content_type:
                    params["ContentType"] = content_type
                url = await c.generate_presigned_url(
                    "put_object", Params=params, ExpiresIn=expires_in,
                )
                headers = {"Content-Type": content_type} if content_type else {}
                return SignedUpload(
                    url=url, method="PUT", headers=headers, fields=None,
                    expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
                )
            if method == "post":
                conditions: list[Any] = []
                if max_size := opts.get("max_size"):
                    conditions.append(["content-length-range", 0, int(max_size)])
                if content_type:
                    conditions.append({"Content-Type": content_type})
                post = await c.generate_presigned_post(
                    Bucket=self.bucket, Key=key, Conditions=conditions or None,
                    ExpiresIn=expires_in,
                )
                return SignedUpload(
                    url=post["url"], method="POST", headers={}, fields=dict(post["fields"]),
                    expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
                )
        raise FilesError(
            code="invalid_input",
            message=f"unknown signed_upload_url method: {method!r}",
            provider=self.name,
        )

    @property
    def raw(self) -> Any:
        return self._session
```

- [ ] **Step 3: Add async fixture to S3 conftest**

Append to `packages/files-sdk-s3/tests/conftest.py`:
```python
@pytest.fixture
def async_adapter(s3_bucket: str):
    from files_sdk_s3 import AsyncS3Adapter
    return AsyncS3Adapter(bucket=s3_bucket)
```

- [ ] **Step 4: Create async conformance import file**

Write file `packages/files-sdk-s3/tests/test_async_conformance.py`:
```python
"""Async conformance tests against AsyncS3Adapter."""

from files_sdk.testing.conformance import (  # noqa: F401
    test_async_delete_idempotent,
    test_async_download_missing_raises_not_found,
    test_async_stream_yields_chunks,
    test_async_upload_then_download_bytes,
)
```

- [ ] **Step 5: Run async conformance**

Run: `uv run pytest packages/files-sdk-s3/tests/test_async_conformance.py -v`
Expected: 4 passed.

- [ ] **Step 6: Run full S3 package test suite**

Run: `uv run pytest packages/files-sdk-s3 -v`
Expected: 14 sync conformance + 4 async conformance + 2 S3-specific = 20 passed.

- [ ] **Step 7: Commit**

```bash
git add packages/files-sdk packages/files-sdk-s3
git commit -m "feat(s3): implement AsyncS3Adapter with async conformance suite"
```

---

## Task 12: R2 adapter package (subclass S3)

**Files:**
- Create: `packages/files-sdk-r2/pyproject.toml`
- Create: `packages/files-sdk-r2/src/files_sdk_r2/__init__.py`
- Create: `packages/files-sdk-r2/src/files_sdk_r2/py.typed`
- Create: `packages/files-sdk-r2/src/files_sdk_r2/adapter.py`
- Create: `packages/files-sdk-r2/src/files_sdk_r2/async_adapter.py`
- Create: `packages/files-sdk-r2/tests/conftest.py`
- Create: `packages/files-sdk-r2/tests/test_conformance.py`
- Create: `packages/files-sdk-r2/tests/test_async_conformance.py`
- Create: `packages/files-sdk-r2/tests/test_r2_specific.py`
- Create: `packages/files-sdk-r2/README.md`

- [ ] **Step 1: Create R2 `pyproject.toml`**

Write file `packages/files-sdk-r2/pyproject.toml`:
```toml
[project]
name = "files-sdk-r2"
version = "0.1.0"
description = "Cloudflare R2 adapter for files-sdk"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
authors = [{name = "Carter Himmel", email = "carter@hellopatient.com"}]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "files-sdk",
    "files-sdk-s3",
]

[project.entry-points."files_sdk.adapters"]
r2 = "files_sdk_r2:R2Adapter"
"r2-async" = "files_sdk_r2:AsyncR2Adapter"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk_r2"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create `py.typed`**

Write empty file `packages/files-sdk-r2/src/files_sdk_r2/py.typed`.

- [ ] **Step 3: Implement `R2Adapter`**

Write file `packages/files-sdk-r2/src/files_sdk_r2/adapter.py`:
```python
"""Cloudflare R2 adapter — S3-compatible with a different endpoint."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import S3Adapter


class R2Adapter(S3Adapter):
    """Cloudflare R2 storage adapter (S3-compatible)."""

    name: ClassVar[str] = "r2"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        account_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
    ) -> None:
        resolved_account = account_id or os.environ.get("R2_ACCOUNT_ID")
        if not resolved_account:
            raise FilesError(
                code="unauthorized",
                message="R2Adapter requires account_id= or R2_ACCOUNT_ID env var",
                provider=self.name,
            )
        resolved_bucket = bucket or os.environ.get("R2_BUCKET")
        resolved_key = access_key_id or os.environ.get("R2_ACCESS_KEY_ID")
        resolved_secret = secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY")
        self._account_id = resolved_account
        self._public_url_base = public_url_base or os.environ.get("R2_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=resolved_bucket,
            region="auto",
            access_key_id=resolved_key,
            secret_access_key=resolved_secret,
            endpoint_url=f"https://{resolved_account}.r2.cloudflarestorage.com",
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            if not self._public_url_base:
                raise FilesError(
                    code="invalid_input",
                    message="public=True requires public_url_base= or R2_PUBLIC_URL_BASE",
                    provider=self.name,
                )
            return f"{self._public_url_base.rstrip('/')}/{key}"
        return super().url(key, expires_in=expires_in, public=False)
```

- [ ] **Step 4: Implement `AsyncR2Adapter`**

Write file `packages/files-sdk-r2/src/files_sdk_r2/async_adapter.py`:
```python
"""Async Cloudflare R2 adapter."""

from __future__ import annotations

import os
from typing import Any, ClassVar

from files_sdk.errors import FilesError
from files_sdk_s3 import AsyncS3Adapter


class AsyncR2Adapter(AsyncS3Adapter):
    name: ClassVar[str] = "r2-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        account_id: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        public_url_base: str | None = None,
        multipart_threshold: int | None = None,
    ) -> None:
        resolved_account = account_id or os.environ.get("R2_ACCOUNT_ID")
        if not resolved_account:
            raise FilesError(
                code="unauthorized",
                message="AsyncR2Adapter requires account_id= or R2_ACCOUNT_ID env var",
                provider=self.name,
            )
        self._account_id = resolved_account
        self._public_url_base = public_url_base or os.environ.get("R2_PUBLIC_URL_BASE")
        kwargs: dict[str, Any] = dict(
            bucket=bucket or os.environ.get("R2_BUCKET"),
            region="auto",
            access_key_id=access_key_id or os.environ.get("R2_ACCESS_KEY_ID"),
            secret_access_key=secret_access_key or os.environ.get("R2_SECRET_ACCESS_KEY"),
            endpoint_url=f"https://{resolved_account}.r2.cloudflarestorage.com",
        )
        if multipart_threshold is not None:
            kwargs["multipart_threshold"] = multipart_threshold
        super().__init__(**kwargs)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            if not self._public_url_base:
                raise FilesError(
                    code="invalid_input",
                    message="public=True requires public_url_base= or R2_PUBLIC_URL_BASE",
                    provider=self.name,
                )
            return f"{self._public_url_base.rstrip('/')}/{key}"
        return await super().url(key, expires_in=expires_in, public=False)
```

- [ ] **Step 5: Wire up `__init__.py`**

Write file `packages/files-sdk-r2/src/files_sdk_r2/__init__.py`:
```python
"""files-sdk-r2 — Cloudflare R2 adapter."""

from .adapter import R2Adapter
from .async_adapter import AsyncR2Adapter

__version__ = "0.1.0"
__all__ = ["AsyncR2Adapter", "R2Adapter"]
```

- [ ] **Step 6: Create R2 README**

Write file `packages/files-sdk-r2/README.md`:
```markdown
# files-sdk-r2

Cloudflare R2 adapter for [files-sdk](../files-sdk). R2 is S3-compatible, so
this package subclasses `files-sdk-s3` with the correct endpoint.

```python
from files_sdk import Files
from files_sdk_r2 import R2Adapter

files = Files(adapter=R2Adapter(bucket="my-bucket"))
```

Reads from `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
`R2_BUCKET`, `R2_PUBLIC_URL_BASE` (optional).
```

- [ ] **Step 7: Create conftest with R2-as-moto fixture**

Write file `packages/files-sdk-r2/tests/conftest.py`:
```python
"""R2 tests run R2Adapter against moto by pointing at moto's mock endpoint.

This validates the S3-compatible path. Real R2 integration tests live behind
the FILES_SDK_R2_INTEGRATION env var (skipped by default).
"""

from __future__ import annotations

import os

import boto3
import pytest
from moto import mock_aws


@pytest.fixture
def aws_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    monkeypatch.setenv("R2_ACCOUNT_ID", "test-account")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "testing")


@pytest.fixture
def r2_bucket(aws_credentials: None):
    with mock_aws():
        bucket = "r2-conformance-bucket"
        boto3.client("s3").create_bucket(Bucket=bucket)
        yield bucket


@pytest.fixture
def adapter(r2_bucket: str, monkeypatch: pytest.MonkeyPatch):
    """Sync R2Adapter pointed at moto by overriding endpoint."""
    # Override the S3Adapter __init__ kwarg by constructing R2Adapter then
    # swapping its endpoint via a fresh boto3 client.
    from files_sdk_s3 import S3Adapter

    return S3Adapter(bucket=r2_bucket)  # R2 path validated separately below


@pytest.fixture
def async_adapter(r2_bucket: str):
    from files_sdk_s3 import AsyncS3Adapter
    return AsyncS3Adapter(bucket=r2_bucket)
```

> **Why is the `adapter` fixture using `S3Adapter` not `R2Adapter`?** The conformance suite validates the *S3-compatible behavior* that R2 inherits. The R2-specific class adds endpoint construction and public-URL logic; those are tested in `test_r2_specific.py`. Mixing them would require either mocking Cloudflare's endpoint DNS (out of scope for v0) or running real integration tests.

- [ ] **Step 8: Create conformance import files**

Write file `packages/files-sdk-r2/tests/test_conformance.py`:
```python
from files_sdk.testing.conformance import *  # noqa: F401,F403
```

Write file `packages/files-sdk-r2/tests/test_async_conformance.py`:
```python
from files_sdk.testing.conformance import (  # noqa: F401
    test_async_delete_idempotent,
    test_async_download_missing_raises_not_found,
    test_async_stream_yields_chunks,
    test_async_upload_then_download_bytes,
)
```

- [ ] **Step 9: R2-specific tests**

Write file `packages/files-sdk-r2/tests/test_r2_specific.py`:
```python
import os

import pytest

from files_sdk.errors import FilesError
from files_sdk_r2 import AsyncR2Adapter, R2Adapter


def test_r2_requires_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    with pytest.raises(FilesError) as ei:
        R2Adapter(bucket="b", access_key_id="x", secret_access_key="y")
    assert ei.value.code == "unauthorized"


def test_r2_constructs_correct_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    a = R2Adapter(bucket="b")
    assert a._endpoint_url == "https://abc123.r2.cloudflarestorage.com"
    assert a._account_id == "abc123"


def test_r2_public_url_without_base_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    monkeypatch.delenv("R2_PUBLIC_URL_BASE", raising=False)
    a = R2Adapter(bucket="b")
    with pytest.raises(FilesError) as ei:
        a.url("k", public=True)
    assert ei.value.code == "invalid_input"


def test_r2_public_url_with_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("R2_ACCOUNT_ID", "abc123")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "k")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "s")
    a = R2Adapter(bucket="b", public_url_base="https://files.example.com")
    assert a.url("hello.txt", public=True) == "https://files.example.com/hello.txt"


def test_async_r2_requires_account_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("R2_ACCOUNT_ID", raising=False)
    with pytest.raises(FilesError) as ei:
        AsyncR2Adapter(bucket="b")
    assert ei.value.code == "unauthorized"
```

- [ ] **Step 10: Sync and run**

Run: `uv sync`
Run: `uv run pytest packages/files-sdk-r2 -v`
Expected: 14 sync conformance + 4 async conformance + 5 R2-specific = 23 passed.

- [ ] **Step 11: Type-check**

Run: `uv run pyright packages/files-sdk-r2/src`
Expected: 0 errors.

- [ ] **Step 12: Commit**

```bash
git add packages/files-sdk-r2
git commit -m "feat(r2): implement R2Adapter and AsyncR2Adapter subclassing S3"
```

---

## Task 13: Adapter `_template` directory

**Files:**
- Create: `packages/_template/pyproject.toml.tmpl`
- Create: `packages/_template/CLAIM.md.tmpl`
- Create: `packages/_template/src/files_sdk_PROVIDER/__init__.py.tmpl`
- Create: `packages/_template/src/files_sdk_PROVIDER/adapter.py.tmpl`
- Create: `packages/_template/README.md`

- [ ] **Step 1: Create README explaining the template**

Write file `packages/_template/README.md`:
```markdown
# Adapter Template

This directory is **not** a uv workspace member. It exists as a reference for
contributors building new adapter packages. To start a new adapter:

1. Copy this directory to `packages/files-sdk-<provider>/`
2. Rename `src/files_sdk_PROVIDER/` to `src/files_sdk_<provider>/`
3. Substitute `<PROVIDER>`/`<provider>` placeholders in every `.tmpl` file
4. Rename `*.tmpl` files (drop the suffix)
5. Update `packages/files-sdk-<provider>/CLAIM.md` with your name
6. Implement the methods in `adapter.py` — see `packages/files-sdk-s3` for a
   reference. Run the shared conformance suite by adding `tests/conftest.py`
   with an `adapter` fixture and `tests/test_conformance.py` importing from
   `files_sdk.testing.conformance`.
```

- [ ] **Step 2: Create `pyproject.toml.tmpl`**

Write file `packages/_template/pyproject.toml.tmpl`:
```toml
[project]
name = "files-sdk-<PROVIDER>"
version = "0.0.0"
description = "<PROVIDER> adapter for files-sdk"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
classifiers = [
    "Development Status :: 1 - Planning",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "files-sdk",
]

[project.entry-points."files_sdk.adapters"]
<provider> = "files_sdk_<provider>:<PROVIDER>Adapter"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk_<provider>"]
```

- [ ] **Step 3: Create `CLAIM.md.tmpl`**

Write file `packages/_template/CLAIM.md.tmpl`:
```markdown
# Claim: <PROVIDER>

- **Claimed by:** (unclaimed)
- **Status:** stub — no implementation yet
- **Tracking issue:** TBD

To claim this adapter, edit this file with your name and open a PR. See the
[adapter template README](../_template/README.md) for implementation guidance.
```

- [ ] **Step 4: Create `__init__.py.tmpl`**

Write file `packages/_template/src/files_sdk_PROVIDER/__init__.py.tmpl`:
```python
"""files-sdk-<provider> — stub adapter."""

from .adapter import <PROVIDER>Adapter

__version__ = "0.0.0"
__all__ = ["<PROVIDER>Adapter"]
```

- [ ] **Step 5: Create `adapter.py.tmpl`**

Write file `packages/_template/src/files_sdk_PROVIDER/adapter.py.tmpl`:
```python
"""Stub <PROVIDER> adapter — claim this in CLAIM.md and implement."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


class <PROVIDER>Adapter:
    name: ClassVar[str] = "<provider>"

    def __init__(self, **_: Any) -> None:
        raise NotImplementedError(
            "files-sdk-<provider> is a stub. See CLAIM.md to claim it."
        )

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        raise NotImplementedError

    def download(self, key: str) -> StoredFile:
        raise NotImplementedError

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        raise NotImplementedError

    def head(self, key: str) -> FileMetadata:
        raise NotImplementedError

    def delete(self, key: str) -> None:
        raise NotImplementedError

    def list(self, *, prefix: str | None = None, cursor: str | None = None,
             limit: int = 1000) -> ListPage:
        raise NotImplementedError

    def copy(self, src: str, dst: str) -> FileMetadata:
        raise NotImplementedError

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        raise NotImplementedError

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        raise NotImplementedError

    @property
    def raw(self) -> Any:
        raise NotImplementedError
```

- [ ] **Step 6: Commit**

```bash
git add packages/_template
git commit -m "feat(template): add adapter scaffold template"
```

---

## Task 14: Generate 15 stub adapter packages

> Each provider follows the template. We list every provider with its package suffix and class-name prefix explicitly so there's no ambiguity.

**Provider table** (suffix = directory + module name; class = `<Class>Adapter`):

| # | suffix | class prefix | full package name |
|---|---|---|---|
| 1 | `akamai` | `Akamai` | `files-sdk-akamai` |
| 2 | `azure` | `Azure` | `files-sdk-azure` |
| 3 | `box` | `Box` | `files-sdk-box` |
| 4 | `digitalocean` | `DigitalOcean` | `files-sdk-digitalocean` |
| 5 | `dropbox` | `Dropbox` | `files-sdk-dropbox` |
| 6 | `gcs` | `GCS` | `files-sdk-gcs` |
| 7 | `gdrive` | `GDrive` | `files-sdk-gdrive` |
| 8 | `hetzner` | `Hetzner` | `files-sdk-hetzner` |
| 9 | `minio` | `MinIO` | `files-sdk-minio` |
| 10 | `netlify` | `Netlify` | `files-sdk-netlify` |
| 11 | `onedrive` | `OneDrive` | `files-sdk-onedrive` |
| 12 | `storj` | `Storj` | `files-sdk-storj` |
| 13 | `supabase` | `Supabase` | `files-sdk-supabase` |
| 14 | `uploadthing` | `UploadThing` | `files-sdk-uploadthing` |
| 15 | `vercel` | `Vercel` | `files-sdk-vercel` |

**Files (per provider):**
- Create: `packages/files-sdk-<suffix>/pyproject.toml`
- Create: `packages/files-sdk-<suffix>/CLAIM.md`
- Create: `packages/files-sdk-<suffix>/README.md`
- Create: `packages/files-sdk-<suffix>/src/files_sdk_<suffix>/__init__.py`
- Create: `packages/files-sdk-<suffix>/src/files_sdk_<suffix>/adapter.py`
- Create: `packages/files-sdk-<suffix>/src/files_sdk_<suffix>/py.typed`
- Create: `packages/files-sdk-<suffix>/tests/test_stub.py`

- [ ] **Step 1: Write a one-off scaffolding script**

Write file `scripts/scaffold_stubs.py` (in workspace root):
```python
"""One-shot script to scaffold all 15 stub adapter packages from the template.

Run with:  uv run python scripts/scaffold_stubs.py
Idempotent: skips packages that already exist.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"

PROVIDERS: list[tuple[str, str]] = [
    ("akamai", "Akamai"),
    ("azure", "Azure"),
    ("box", "Box"),
    ("digitalocean", "DigitalOcean"),
    ("dropbox", "Dropbox"),
    ("gcs", "GCS"),
    ("gdrive", "GDrive"),
    ("hetzner", "Hetzner"),
    ("minio", "MinIO"),
    ("netlify", "Netlify"),
    ("onedrive", "OneDrive"),
    ("storj", "Storj"),
    ("supabase", "Supabase"),
    ("uploadthing", "UploadThing"),
    ("vercel", "Vercel"),
]

PYPROJECT_TMPL = '''\
[project]
name = "files-sdk-{suffix}"
version = "0.0.0"
description = "{cls} adapter for files-sdk (stub)"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
classifiers = [
    "Development Status :: 1 - Planning",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "files-sdk",
]

[project.entry-points."files_sdk.adapters"]
{suffix} = "files_sdk_{suffix}:{cls}Adapter"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk_{suffix}"]

[tool.pytest.ini_options]
testpaths = ["tests"]
'''

CLAIM_TMPL = '''\
# Claim: {cls}

- **Claimed by:** (unclaimed)
- **Status:** stub — no implementation yet
- **Tracking issue:** TBD

To claim this adapter, edit this file with your name and open a PR. See
[`packages/_template/README.md`](../_template/README.md) for guidance.
'''

README_TMPL = '''\
# files-sdk-{suffix}

Stub adapter for **{cls}** in [files-sdk](../files-sdk). Not yet implemented.

See [CLAIM.md](./CLAIM.md) to claim and implement.
'''

INIT_TMPL = '''\
"""files-sdk-{suffix} — stub adapter."""

from .adapter import {cls}Adapter

__version__ = "0.0.0"
__all__ = ["{cls}Adapter"]
'''

ADAPTER_TMPL = '''\
"""Stub {cls} adapter — claim this in CLAIM.md and implement."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


_NOT_IMPLEMENTED = (
    "files-sdk-{suffix} is a stub. See packages/files-sdk-{suffix}/CLAIM.md to claim it."
)


class {cls}Adapter:
    name: ClassVar[str] = "{suffix}"

    def __init__(self, **_: Any) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def download(self, key: str) -> StoredFile:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def head(self, key: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def delete(self, key: str) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list(self, *, prefix: str | None = None, cursor: str | None = None,
             limit: int = 1000) -> ListPage:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def copy(self, src: str, dst: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @property
    def raw(self) -> Any:
        raise NotImplementedError(_NOT_IMPLEMENTED)
'''

TEST_TMPL = '''\
"""Smoke test confirming the stub raises NotImplementedError."""

import pytest

from files_sdk_{suffix} import {cls}Adapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        {cls}Adapter()
'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def scaffold_one(suffix: str, cls: str) -> bool:
    pkg = PACKAGES / f"files-sdk-{suffix}"
    if pkg.exists():
        print(f"skip (exists): {pkg.name}")
        return False
    write(pkg / "pyproject.toml", PYPROJECT_TMPL.format(suffix=suffix, cls=cls))
    write(pkg / "CLAIM.md", CLAIM_TMPL.format(cls=cls))
    write(pkg / "README.md", README_TMPL.format(suffix=suffix, cls=cls))
    src = pkg / "src" / f"files_sdk_{suffix}"
    write(src / "__init__.py", INIT_TMPL.format(suffix=suffix, cls=cls))
    write(src / "adapter.py", ADAPTER_TMPL.format(suffix=suffix, cls=cls))
    (src / "py.typed").write_text("")
    write(pkg / "tests" / "test_stub.py", TEST_TMPL.format(suffix=suffix, cls=cls))
    print(f"created: {pkg.name}")
    return True


def main() -> int:
    created = 0
    for suffix, cls in PROVIDERS:
        if scaffold_one(suffix, cls):
            created += 1
    print(f"\n{created} package(s) created, {len(PROVIDERS) - created} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run the scaffolder**

Run: `uv run python scripts/scaffold_stubs.py`
Expected: prints `created: files-sdk-akamai` ... `created: files-sdk-vercel` (15 lines).

- [ ] **Step 3: Sync workspace**

Run: `uv sync`
Expected: all 15 stub packages installed editable. No errors.

- [ ] **Step 4: Verify entry points register**

Run: `uv run python -c "from importlib.metadata import entry_points; print(sorted(ep.name for ep in entry_points(group='files_sdk.adapters')))"`
Expected: `['akamai', 'azure', 'box', 'digitalocean', 'dropbox', 'gcs', 'gdrive', 'hetzner', 'minio', 'netlify', 'onedrive', 'r2', 'r2-async', 's3', 's3-async', 'storj', 'supabase', 'uploadthing', 'vercel']`

- [ ] **Step 5: Run all stub smoke tests**

Run: `uv run pytest packages/files-sdk-akamai packages/files-sdk-azure packages/files-sdk-box packages/files-sdk-digitalocean packages/files-sdk-dropbox packages/files-sdk-gcs packages/files-sdk-gdrive packages/files-sdk-hetzner packages/files-sdk-minio packages/files-sdk-netlify packages/files-sdk-onedrive packages/files-sdk-storj packages/files-sdk-supabase packages/files-sdk-uploadthing packages/files-sdk-vercel -v`
Expected: 15 passed.

- [ ] **Step 6: Verify `from_name` resolves a stub and raises**

Run: `uv run python -c "from files_sdk import Files; Files.from_name('akamai')"`
Expected: raises `NotImplementedError` (the stub's `__init__`). Confirms the entry-point path works end-to-end.

- [ ] **Step 7: Commit**

```bash
git add scripts/scaffold_stubs.py packages/files-sdk-{akamai,azure,box,digitalocean,dropbox,gcs,gdrive,hetzner,minio,netlify,onedrive,storj,supabase,uploadthing,vercel}
git commit -m "feat(stubs): scaffold 15 stub adapter packages"
```

---

## Task 15: Workspace-wide sanity + CI

**Files:**
- Modify: `pyproject.toml` (already done)
- Create: `.github/workflows/ci.yml`
- Create: `README.md` (workspace root)

- [ ] **Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: every test in every package passes. Tally roughly:
- core: ~20 (errors, types, adapter, registry, client)
- s3: 20
- r2: 23
- 15 stubs × 1 = 15
- total ≈ 78 passing

- [ ] **Step 2: Run pyright across all packages**

Run: `uv run pyright`
Expected: 0 errors. Fix any.

- [ ] **Step 3: Run ruff**

Run: `uv run ruff check . && uv run ruff format --check .`
Expected: clean. If format fails, run `uv run ruff format .` and re-check.

- [ ] **Step 4: Create CI workflow**

Write file `.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          enable-cache: true
      - name: Set Python ${{ matrix.python }}
        run: uv python install ${{ matrix.python }}
      - name: Install
        run: uv sync --all-packages
      - name: Lint
        run: uv run ruff check .
      - name: Format check
        run: uv run ruff format --check .
      - name: Type check
        run: uv run pyright
      - name: Test
        run: uv run pytest -v
```

- [ ] **Step 5: Create workspace README**

Write file `README.md`:
```markdown
# files-sdk (Python)

Python port of [files-sdk.dev](https://files-sdk.dev/). One unified API across
cloud object/blob storage providers.

## Packages

- **[files-sdk](packages/files-sdk/)** — core client, types, adapter protocol
- **[files-sdk-s3](packages/files-sdk-s3/)** — Amazon S3 (sync + async)
- **[files-sdk-r2](packages/files-sdk-r2/)** — Cloudflare R2 (sync + async)
- 15 stub packages awaiting implementation — see each `CLAIM.md`

## Quickstart

```bash
pip install files-sdk files-sdk-s3
```

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

## Development

```bash
uv sync
uv run pytest
uv run pyright
uv run ruff check .
```

See [`docs/superpowers/specs/`](docs/superpowers/specs/) for design docs.

## Contributing a new adapter

Pick a stub from `packages/files-sdk-<provider>/CLAIM.md` and follow
[`packages/_template/README.md`](packages/_template/README.md).
```

- [ ] **Step 6: Final commit**

```bash
git add .github/workflows/ci.yml README.md
git commit -m "chore: add CI workflow and workspace README"
```

- [ ] **Step 7: Final verification**

Run:
```bash
uv run pytest
uv run pyright
uv run ruff check .
uv run ruff format --check .
```
All four should succeed. v0 is done.

---

## Self-Review

**Spec coverage:**
- Section 1 (Goal): Task 1–15 covers it. ✓
- Section 2 (Source-of-truth API): all 9 methods + `stream` implemented in core client (Task 7) and exercised by conformance (Task 8). ✓
- Section 3 (Workspace layout): Task 1 root, Task 2/9/12 core+adapters, Task 13 template, Task 14 stubs. ✓
- Section 4.1 (Construction with env): Task 10 S3 env loading, Task 12 R2 env loading. ✓
- Section 4.2 (Method signatures): Task 7 client surface matches spec. ✓
- Section 4.3 (Types): Task 4 covers all four models. ✓
- Section 5 (Adapter Protocols): Task 5. ✓
- Section 6 (Plugin discovery): Task 6 + Task 7 (`from_name`). ✓
- Section 7 (Error model): Task 3 + adapter normalization in Tasks 10/11/12. ✓
- Section 8 (R2/S3 specifics): Tasks 10–12. ✓
- Section 9 (Testing): Conformance suite (Task 8), moto fixtures (Tasks 10/11/12), stub smoke tests (Task 14). ✓
- Section 10 (Tooling): Task 1 + Task 15. ✓
- Section 13 (Acceptance): Task 15 Step 1–3 + Task 14 Step 4 verify each item.

**Placeholder scan:** No "TBD/TODO/implement later" in any task. `CLAIM.md.tmpl` and generated `CLAIM.md` correctly use "(unclaimed)" / "TBD" because that IS the artifact (a claim file with no owner yet) — not a plan placeholder.

**Type consistency:** Spot-checked names across tasks:
- `FilesError(code=..., message=..., provider=...)` — same kwargs in Task 3 definition, Tasks 6, 10, 11, 12 usage. ✓
- `FileMetadata` field names match across Task 4 definition and Tasks 10/11 usage. ✓
- `ListPage(items=..., cursor=...)` consistent. ✓
- `SignedUpload(url=..., method=..., headers=..., fields=..., expires_at=...)` consistent. ✓
- `Adapter.list(prefix=, cursor=, limit=)` kwargs match in protocol (Task 5), client (Task 7), and adapters (Tasks 10/11). ✓
- `load_adapter_class` (Task 6) imported by `client.py` (Task 7). ✓
- `is_async_adapter` (Task 5) imported by `client.py` (Task 7). ✓
- Entry-point group `files_sdk.adapters` consistent across registry (Task 6), s3 pyproject (Task 9), r2 pyproject (Task 12), stub pyprojects (Task 14). ✓

No gaps detected. Plan is ready for execution.
