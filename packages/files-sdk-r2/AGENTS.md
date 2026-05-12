# packages/files-sdk-r2

Cloudflare R2 adapter. R2 is S3-compatible; this package subclasses `files-sdk-s3`.

## File map

```
src/files_sdk_r2/
  adapter.py        # R2Adapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncR2Adapter(AsyncS3Adapter) — same overrides
  __init__.py
tests/
  conftest.py       # re-uses moto ThreadedMotoServer; adapter fixture uses S3Adapter
  test_conformance.py
  test_async_conformance.py
  test_r2_specific.py   # R2-specific logic: endpoint construction, public URL, account_id req
```

## What R2 overrides

- `__init__`: resolves `account_id` (required; env `R2_ACCOUNT_ID`), builds
  `https://<account_id>.r2.cloudflarestorage.com` endpoint, maps R2 env vars to S3 kwargs
- `url(key, public=True)`: returns `<public_url_base>/<key>`; raises `invalid_input` if
  `public_url_base` is not set. `public=False` delegates to `super().url()` (presigned URL).

Everything else — `upload`, `download`, `stream`, `head`, `delete`, `list`, `copy`,
`signed_upload_url`, `_wrap` — is inherited unchanged from `S3Adapter`.

## Conformance strategy

The conformance suite runs `S3Adapter` (not `R2Adapter`) against moto. This is intentional:
it exercises the full S3 protocol surface without needing an R2 account. R2-specific
behavior is covered by `test_r2_specific.py` with monkeypatched env vars.

## Testing gotchas

- `_endpoint_override` kwarg on `R2Adapter.__init__` bypasses the Cloudflare URL for
  moto-based round-trip tests. It is undocumented for production use.
- `test_r2_roundtrip_via_moto_endpoint` in `test_r2_specific.py` is the smoke test for
  kwargs forwarding through `super().__init__`.

## Entry points

```toml
[project.entry-points."files_sdk.adapters"]
r2 = "files_sdk_r2:R2Adapter"
"r2-async" = "files_sdk_r2:AsyncR2Adapter"
```

## Real R2 integration

`tests/integration/test_r2_real.py` at workspace root. Gated on `FILES_SDK_R2_INTEGRATION=1`.
CI job is `workflow_dispatch` only (avoids burning Cloudflare class-A ops on every PR).
