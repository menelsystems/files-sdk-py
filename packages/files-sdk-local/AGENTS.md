# packages/files-sdk-local

Local filesystem adapter. Pure stdlib (pathlib, hashlib, mimetypes, json). Zero external deps.
Intended for dev, tests, demos, and offline tooling.

## File map

```
src/files_sdk_local/
  _storage.py       # _LocalStorage — sync filesystem core shared by both adapters
  adapter.py        # LocalAdapter — thin wrapper around _LocalStorage
  async_adapter.py  # AsyncLocalAdapter — wraps _LocalStorage calls in asyncio.to_thread
  __init__.py
tests/
  conftest.py       # fixtures: LocalAdapter(tmp_path/"store"), AsyncLocalAdapter(tmp_path/"store-async")
  test_conformance.py
  test_async_conformance.py
  test_local_specific.py   # path-safety, sidecar metadata, public URL, signed_upload_url opt-out
```

## Architecture

`_LocalStorage` (`_storage.py`) is the single sync implementation. Both adapters delegate:
- `LocalAdapter` calls `_LocalStorage` methods directly
- `AsyncLocalAdapter` wraps each call in `await asyncio.to_thread(_storage.<method>, ...)`

Do not duplicate logic between adapters — all behavior lives in `_LocalStorage`.

## Path safety

`_safe_path(key)` (`_storage.py:34`) rejects keys that escape root:
- Empty key, leading `/`, or null byte → `invalid_input`
- Resolved path must stay inside `root` (`.resolve()` + `relative_to`) → `invalid_input`
- Keys that are exactly `root` or touch `.files-sdk-meta/` → `invalid_input`

## Sidecar metadata

Content-type, user metadata, and cache-control are stored at
`<root>/.files-sdk-meta/<key>.json` alongside the object file.
The `.files-sdk-meta/` dir is excluded from `list()` results.

## Signed upload opt-out

```python
class LocalAdapter:
    supports_signed_upload = False   # conformance suite skips signed_upload_url tests
```

`signed_upload_url()` raises `FilesError(code="invalid_input")`. There is no signing
authority on a local filesystem.

## Known v0 limitations

- etag is recomputed (full MD5 read) on every `head()` and `list()` — no caching
- No file locking; concurrent writers to the same key may corrupt the object
- `list()` cursor is an integer offset into a sorted file list — not stable across mutations

## Entry points

```toml
[project.entry-points."files_sdk.adapters"]
local = "files_sdk_local:LocalAdapter"
"local-async" = "files_sdk_local:AsyncLocalAdapter"
```
