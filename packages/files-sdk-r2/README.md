# files-sdk-r2

Cloudflare R2 adapter for [files-sdk](../files-sdk). R2 is S3-compatible, so
this package subclasses `files-sdk-s3` with the correct endpoint.

```python
from files_sdk import Files
from files_sdk_r2 import R2Adapter

files = Files(adapter=R2Adapter(bucket="my-bucket"))
```

Reads from `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`,
`R2_BUCKET`, `R2_PUBLIC_URL_BASE` (optional).
