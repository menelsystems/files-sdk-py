# packages/files-sdk-akamai

Akamai (Linode) Object Storage adapter. S3-compatible; subclasses
`files-sdk-s3`.

## File map

```
src/files_sdk_akamai/
  adapter.py        # AkamaiAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncAkamaiAdapter(AsyncS3Adapter)
  __init__.py
tests/
  conftest.py
  test_conformance.py
  test_async_conformance.py
  test_akamai_specific.py
```

## What Akamai overrides

- `__init__`: requires `cluster=` (or `AKAMAI_CLUSTER`), constructs
  `https://<cluster>.linodeobjects.com`. Maps `AKAMAI_*` env vars.
- `url(key, public=True)`: defaults to bucket-virtual-host
  `https://<bucket>.<cluster>.linodeobjects.com/<key>`.

## Conformance strategy

Conformance runs `S3Adapter` against moto. Akamai-specific behavior covered
by `test_akamai_specific.py`. `_endpoint_override` kwarg lets tests bypass
the constructed endpoint (undocumented for production).
