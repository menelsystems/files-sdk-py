# packages/files-sdk-digitalocean

DigitalOcean Spaces adapter. Spaces is S3-compatible; this package subclasses
`files-sdk-s3`.

## File map

```
src/files_sdk_digitalocean/
  adapter.py        # DigitalOceanAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncDigitalOceanAdapter(AsyncS3Adapter)
  __init__.py
tests/
  conftest.py
  test_conformance.py
  test_async_conformance.py
  test_digitalocean_specific.py
```

## What DigitalOcean overrides

- `__init__`: requires `region=` (or `DO_SPACES_REGION`), constructs
  `https://<region>.digitaloceanspaces.com`. Maps `DO_SPACES_*` env vars.
- `url(key, public=True)`: defaults to bucket-virtual-host
  `https://<bucket>.<region>.digitaloceanspaces.com/<key>`. Override with
  `public_url_base=` (CDN, custom domain).

## Conformance strategy

Conformance runs `S3Adapter` against moto. DO-specific behavior covered by
`test_digitalocean_specific.py`. The `_endpoint_override` kwarg on
`DigitalOceanAdapter.__init__` lets tests bypass the constructed endpoint
and exercise the full init path against moto (undocumented for production).
