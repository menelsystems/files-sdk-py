# packages/_template

Scaffold reference for new adapter packages. This directory is NOT a uv workspace member
(excluded in root `pyproject.toml`) and is never installed.

## Scaffolding a new adapter

1. Copy this directory to `packages/files-sdk-<provider>/`
2. Rename `src/files_sdk_PROVIDER/` to `src/files_sdk_<provider>/`
3. Substitute `<PROVIDER>` / `<provider>` placeholders in every `.tmpl` file
4. Rename `*.tmpl` files (drop the `.tmpl` suffix)
5. Update `CLAIM.md` with your name and GitHub handle
6. Add the new package to `[tool.uv.sources]` in the root `pyproject.toml` if it
   has workspace dependencies (e.g., `files-sdk-s3`)

## Implementing the adapter

- Reference implementation: `packages/files-sdk-s3/src/files_sdk_s3/adapter.py`
- Must implement every method in `files_sdk.adapter.Adapter` (and `AsyncAdapter` if shipping async)
- Translate all provider-native exceptions to `FilesError` before they escape — use a
  `_wrap` pattern like `files-sdk-s3` does
- Never raise anything other than `FilesError`; valid codes: `not_found`, `unauthorized`,
  `conflict`, `provider`, `invalid_input`
- If `signed_upload_url` is not supportable, set `supports_signed_upload = False` on the
  class (see `files-sdk-local` for the pattern)

## Wiring up the conformance suite

```python
# tests/conftest.py — provide adapter fixture pointing at a real or mocked backend
@pytest.fixture
def adapter():
    from files_sdk_<provider> import <PROVIDER>Adapter
    return <PROVIDER>Adapter(...)

# tests/test_conformance.py
from files_sdk.testing.conformance import *  # noqa: F401,F403
```

Your adapter is "done" when all 14 conformance tests pass against a real backend.
The async variant requires an `async_adapter` fixture and `test_async_conformance.py`.

## Stub packages

Each of the 15 stub packages under `packages/files-sdk-*/` already has this scaffold in
place. Every method raises `NotImplementedError`. Pick a stub from its `CLAIM.md`,
implement the methods, and add the conformance suite.

## Entry point

Register in `pyproject.toml`:

```toml
[project.entry-points."files_sdk.adapters"]
<provider> = "files_sdk_<provider>:<PROVIDER>Adapter"
```
