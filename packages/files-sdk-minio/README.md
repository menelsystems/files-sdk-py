# files-sdk-minio

[MinIO](https://min.io) adapter for [files-sdk](../files-sdk). MinIO speaks
S3, so this package subclasses `files-sdk-s3` and points it at your MinIO
endpoint.

```python
from files_sdk import Files
from files_sdk_minio import MinIOAdapter

files = Files(adapter=MinIOAdapter(
    endpoint="http://localhost:9000",
    bucket="my-bucket",
))
```

Reads from `MINIO_ENDPOINT`, `MINIO_BUCKET`, `MINIO_ACCESS_KEY_ID`,
`MINIO_SECRET_ACCESS_KEY`, `MINIO_REGION` (default `us-east-1`),
`MINIO_PUBLIC_URL_BASE` (optional, required for `url(public=True)`).

The async adapter (`AsyncMinIOAdapter`) shares the same configuration and
uses `aioboto3` under the hood.
