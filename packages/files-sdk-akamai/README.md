# files-sdk-akamai

[Akamai (Linode) Object Storage](https://www.linode.com/products/object-storage/)
adapter for [files-sdk](../files-sdk). S3-compatible; this package subclasses
`files-sdk-s3` and points it at the cluster endpoint.

```python
from files_sdk import Files
from files_sdk_akamai import AkamaiAdapter

files = Files(adapter=AkamaiAdapter(
    cluster="us-east-1",   # or "us-iad-1", "eu-central-1", "ap-south-1", etc.
    bucket="my-bucket",
))
```

Reads from `AKAMAI_CLUSTER`, `AKAMAI_BUCKET`, `AKAMAI_ACCESS_KEY_ID`,
`AKAMAI_SECRET_ACCESS_KEY`, `AKAMAI_PUBLIC_URL_BASE` (optional — defaults to
the bucket-virtual-host endpoint for `url(public=True)`).

The async adapter (`AsyncAkamaiAdapter`) shares the same configuration.
