# packages/files-sdk-minio

MinIO adapter. MinIO is S3-compatible; this package subclasses `files-sdk-s3`
and points it at a user-supplied endpoint.

## File map

```
src/files_sdk_minio/
  adapter.py        # MinIOAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncMinIOAdapter(AsyncS3Adapter) — same overrides
  __init__.py
tests/
  conftest.py       # re-uses moto ThreadedMotoServer; adapter fixture uses S3Adapter
  test_conformance.py
  test_async_conformance.py
  test_minio_specific.py   # MinIO-specific logic: endpoint required, public URL behavior
```

## What MinIO overrides

- `__init__`: requires `endpoint=` (or `MINIO_ENDPOINT` env), maps `MINIO_*`
  env vars to S3 kwargs. Defaults `region` to `us-east-1` (standard MinIO
  default).
- `url(key, public=True)`: returns `<public_url_base>/<key>`; raises
  `invalid_input` if `public_url_base` is unset (no canonical pattern — MinIO
  is typically fronted by a reverse proxy or CDN).

Everything else is inherited unchanged from `S3Adapter` / `AsyncS3Adapter`.

## Conformance strategy

Conformance runs `S3Adapter` (not `MinIOAdapter`) against moto. MinIO-specific
behavior is covered by `test_minio_specific.py` with monkeypatched env vars.
This avoids needing a live MinIO server in CI; integration tests run against
the rustfs fixture (also S3-compatible) at the workspace level.

## Entry points

```toml
[project.entry-points."files_sdk.adapters"]
minio = "files_sdk_minio:MinIOAdapter"
"minio-async" = "files_sdk_minio:AsyncMinIOAdapter"
```
