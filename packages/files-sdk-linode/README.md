# files-sdk-linode

[Linode Object Storage](https://www.linode.com/products/object-storage/)
adapter for [files-sdk](../files-sdk). Linode (now an Akamai company) exposes
its Object Storage product over an S3-compatible API; this package subclasses
`files-sdk-s3` and points it at the cluster endpoint.

```python
from files_sdk import Files
from files_sdk_linode import LinodeAdapter

files = Files(adapter=LinodeAdapter(
    cluster="us-east-1",   # or "us-iad-1", "eu-central-1", "ap-south-1", etc.
    bucket="my-bucket",
))
```

Reads from `LINODE_CLUSTER`, `LINODE_BUCKET`, `LINODE_ACCESS_KEY_ID`,
`LINODE_SECRET_ACCESS_KEY`, `LINODE_PUBLIC_URL_BASE` (optional — defaults to
the bucket-virtual-host endpoint for `url(public=True)`).

The async adapter (`AsyncLinodeAdapter`) shares the same configuration.

> **Note:** this is the Linode Object Storage product. Akamai NetStorage is a
> separate product with a different protocol (custom HTTP API + HMAC-SHA256
> header signing); a NetStorage adapter would live in a different package.
