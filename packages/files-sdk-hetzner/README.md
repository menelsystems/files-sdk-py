# files-sdk-hetzner

[Hetzner Object Storage](https://www.hetzner.com/storage/object-storage/)
adapter for [files-sdk](../files-sdk). S3-compatible; this package subclasses
`files-sdk-s3` and points it at the regional endpoint.

```python
from files_sdk import Files
from files_sdk_hetzner import HetznerAdapter

files = Files(adapter=HetznerAdapter(
    region="fsn1",   # or "nbg1", "hel1"
    bucket="my-bucket",
))
```

Reads from `HETZNER_REGION`, `HETZNER_BUCKET`, `HETZNER_ACCESS_KEY_ID`,
`HETZNER_SECRET_ACCESS_KEY`, `HETZNER_PUBLIC_URL_BASE` (optional — defaults
to the bucket-virtual-host endpoint for `url(public=True)`).

The async adapter (`AsyncHetznerAdapter`) shares the same configuration.
