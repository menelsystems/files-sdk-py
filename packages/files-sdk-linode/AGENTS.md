# packages/files-sdk-linode

Linode Object Storage adapter. S3-compatible; subclasses `files-sdk-s3`.

Linode (now an Akamai company) ships Object Storage as an S3-compatible
product. This package is **not** an Akamai NetStorage adapter — that uses a
different protocol with HMAC-SHA256 header signing and would live in its own
package.

## File map

```
src/files_sdk_linode/
  adapter.py        # LinodeAdapter(S3Adapter) — overrides __init__ and url()
  async_adapter.py  # AsyncLinodeAdapter(AsyncS3Adapter)
  __init__.py
tests/
  conftest.py
  test_conformance.py
  test_async_conformance.py
  test_linode_specific.py
```

## What Linode overrides

- `__init__`: requires `cluster=` (or `LINODE_CLUSTER`), constructs
  `https://<cluster>.linodeobjects.com`. Maps `LINODE_*` env vars.
- `url(key, public=True)`: defaults to bucket-virtual-host
  `https://<bucket>.<cluster>.linodeobjects.com/<key>`.

## Conformance strategy

Conformance runs `S3Adapter` against moto. Linode-specific behavior covered
by `test_linode_specific.py`. `_endpoint_override` kwarg lets tests bypass
the constructed endpoint (undocumented for production).
