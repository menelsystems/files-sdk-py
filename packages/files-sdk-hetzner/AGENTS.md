# packages/files-sdk-hetzner

Hetzner Object Storage adapter. S3-compatible; subclasses `files-sdk-s3`.

## File map

```
src/files_sdk_hetzner/
  adapter.py        # HetznerAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncHetznerAdapter(AsyncS3Adapter)
  __init__.py
tests/
  conftest.py
  test_conformance.py
  test_async_conformance.py
  test_hetzner_specific.py
```

## What Hetzner overrides

- `__init__`: requires `region=` (or `HETZNER_REGION`), constructs
  `https://<region>.your-objectstorage.com`. Maps `HETZNER_*` env vars.
- `url(key, public=True)`: defaults to bucket-virtual-host
  `https://<bucket>.<region>.your-objectstorage.com/<key>`.

## Conformance strategy

Conformance runs `S3Adapter` against moto. Hetzner-specific behavior covered
by `test_hetzner_specific.py`. `_endpoint_override` kwarg lets tests bypass
the constructed endpoint (undocumented for production).
