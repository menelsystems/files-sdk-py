# files-sdk-s3

S3 adapter for [files-sdk](../files-sdk).

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
```

Reads credentials from the standard AWS environment (`AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_SESSION_TOKEN`).
