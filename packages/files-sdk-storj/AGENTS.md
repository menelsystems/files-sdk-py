# packages/files-sdk-storj

Storj DCS adapter. The S3-compatible gateway makes Storj look like S3 to
clients; this package subclasses `files-sdk-s3`.

## File map

```
src/files_sdk_storj/
  adapter.py        # StorjAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncStorjAdapter(AsyncS3Adapter)
  __init__.py
tests/
  conftest.py
  test_conformance.py
  test_async_conformance.py
  test_storj_specific.py
```

## What Storj overrides

- `__init__`: defaults to the global gateway `https://gateway.storjshare.io`.
  `gateway_region=` (or `STORJ_GATEWAY_REGION`) selects a regional gateway
  (`us1`, `eu1`, `ap1`) and constructs `https://gateway.<region>.storjshare.io`.
  Sets `region=global` for sigv4. Maps `STORJ_*` env vars.
- `url(key, public=True)`: requires `public_url_base=` (no canonical pattern;
  Storj public URLs go through the Linksharing service).

## Conformance strategy

Conformance runs `S3Adapter` against moto. Storj-specific behavior covered
by `test_storj_specific.py`. `_endpoint_override` kwarg lets tests bypass
the gateway URL (undocumented for production).
