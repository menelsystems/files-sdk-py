# files-sdk

Unified Python SDK for cloud object/blob storage. Python port of [files-sdk.dev](https://files-sdk.dev/).

Install an adapter: `pip install files-sdk-s3` or `pip install files-sdk-r2`.

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").data)
```
