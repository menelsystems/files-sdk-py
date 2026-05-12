# packages/files-sdk

Core package. Defines the adapter contract, client, shared types, and error types.
No adapter logic lives here — only the Protocol and test tooling.

## File map

```
src/files_sdk/
  adapter.py       # Adapter + AsyncAdapter Protocols (runtime_checkable)
  client.py        # Files + AsyncFiles — thin dispatch layer
  errors.py        # FilesError, ErrorCode Literal, VALID_CODES frozenset
  types.py         # FileMetadata, StoredFile, ListPage, SignedUpload, UploadBody
  _registry.py     # entry-point lookup for Files.from_name()
  __init__.py      # public re-exports (keep __all__ in sync when adding symbols)
  testing/
    conformance.py # 14 sync + 4 async test functions (imported via *)
```

## Adapter Protocol

Both `Adapter` and `AsyncAdapter` are `@runtime_checkable` but `isinstance` checks are
shallow — they only verify method existence, not signatures. Use `is_async_adapter(obj)`
(`adapter.py:68`) to distinguish sync vs. async at runtime.

## Conformance suite

Adapter packages import and re-export all test functions:

```python
# tests/test_conformance.py in any adapter package
from files_sdk.testing.conformance import *  # noqa: F401,F403
```

pytest discovers each `test_*` function and binds the local `adapter` / `async_adapter`
fixture from that package's `conftest.py`.

- 14 sync tests + 4 async tests
- `signed_upload_url` test skips automatically when `adapter.supports_signed_upload == False`
- An adapter is "done" when the full suite passes against a real backend

## Errors

`FilesError` lives in `errors.py`. `ErrorCode` is a `Literal` type; `VALID_CODES` is a
parallel `frozenset` used at runtime. **Keep them in sync** — the constructor validates
against `VALID_CODES` at runtime.

## Public API

`__init__.py` exports: `Adapter`, `AsyncAdapter`, `AsyncFiles`, `ErrorCode`,
`FileMetadata`, `Files`, `FilesError`, `ListPage`, `SignedUpload`, `StoredFile`,
`UploadBody`. Add new public symbols to `__all__` there when introducing them.
