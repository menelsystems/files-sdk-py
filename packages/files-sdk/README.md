# files-sdk

Unified Python SDK for cloud object/blob storage. Python port of [files-sdk.dev](https://files-sdk.dev/).

One API, swap the adapter to change backend. v0 ships R2, S3, and Local adapters; 15 cloud providers scaffolded for contributors.

```bash
uv add files-sdk
uv add files-sdk-local             # zero deps, ideal for dev/test
uv add files-sdk-s3                # Amazon S3 (sync + async)
uv add files-sdk-r2                # Cloudflare R2 (sync + async)
```

`pip install ...` works too if you're not on uv yet. Get uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## Quickstart — no credentials (Local)

```python
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

## Quickstart — Cloudflare R2

```python
from files_sdk import Files
from files_sdk_r2 import R2Adapter

# Reads R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY from env
files = Files(adapter=R2Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
```

## Quickstart — Amazon S3

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

# Reads standard AWS env: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
files = Files(adapter=S3Adapter(bucket="my-bucket"))
```

## Async equivalent

```python
from files_sdk import AsyncFiles
from files_sdk_s3 import AsyncS3Adapter

afiles = AsyncFiles(adapter=AsyncS3Adapter(bucket="my-bucket"))
await afiles.upload("hello.txt", b"hi")
```

## Adapter lookup by name

```python
files = Files.from_name("local", root="/tmp/my-store")
files = Files.from_name("s3", bucket="my-bucket")
```

## API

| Method | Purpose |
|---|---|
| `files.upload(key, body, *, content_type=None, metadata=None, cache_control=None)` | Store an object. `body` is `bytes`, `str`, `Path`, or a file-like. |
| `files.download(key)` | Return a `StoredFile` (fully buffered). |
| `files.stream(key, *, chunk_size=65536)` | Yield chunks (memory-bounded). |
| `files.head(key)` | Return `FileMetadata` without the body. |
| `files.delete(key)` | Remove an object. Idempotent (no error on missing). |
| `files.list(*, prefix=None, cursor=None, limit=1000)` | Paginated listing. Returns `ListPage`. |
| `files.copy(src, dst)` | Server-side copy. |
| `files.url(key, *, expires_in=3600, public=False)` | Signed or public URL. |
| `files.signed_upload_url(key, *, method="put"\|"post", expires_in=3600, ...)` | Browser-direct upload contract. |
| `files.raw` | Escape hatch — provider-native client. |

Errors raise `FilesError` with `code` in `{"not_found", "unauthorized", "conflict", "provider", "invalid_input"}` and the original exception preserved via `__cause__`.
