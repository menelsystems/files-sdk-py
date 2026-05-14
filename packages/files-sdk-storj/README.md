# files-sdk-storj

[Storj DCS](https://www.storj.io/) adapter for [files-sdk](../files-sdk).
Storj's S3-compatible gateway looks like S3 to clients; this package
subclasses `files-sdk-s3` and points it at the gateway endpoint.

```python
from files_sdk import Files
from files_sdk_storj import StorjAdapter

files = Files(adapter=StorjAdapter(
    bucket="my-bucket",
    access_key_id="...",
    secret_access_key="...",
))
```

Reads from `STORJ_BUCKET`, `STORJ_ACCESS_KEY_ID`, `STORJ_SECRET_ACCESS_KEY`,
`STORJ_GATEWAY_REGION` (optional — selects a regional gateway like `us1`,
`eu1`, or `ap1`; defaults to the global gateway), `STORJ_PUBLIC_URL_BASE`
(optional, required for `url(public=True)` — typically a
[Linksharing](https://docs.storj.io/dcs/api/linksharing/) root URL).

The async adapter (`AsyncStorjAdapter`) shares the same configuration.
