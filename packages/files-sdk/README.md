# files-sdk

Unified Python SDK for cloud object/blob storage. Python port of [files-sdk.dev](https://files-sdk.dev/).

One API, swap the adapter to change backend. **Sync and async are both first-class** — every adapter ships an `XAdapter` (sync) and `AsyncXAdapter` (async) sibling, driven by `Files` or `AsyncFiles`. v0 ships R2, S3, and Local adapters; 15 cloud providers scaffolded for contributors.

```bash
uv add files-sdk
uv add files-sdk-local             # zero deps, ideal for dev/test
uv add files-sdk-s3                # Amazon S3 (sync + async)
uv add files-sdk-r2                # Cloudflare R2 (sync + async)
```

`pip install ...` works too if you're not on uv yet. Get uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`.

## Sync ↔ async pairs

| | Sync | Async |
|---|---|---|
| Client | `Files` | `AsyncFiles` |
| Local | `LocalAdapter` | `AsyncLocalAdapter` |
| S3 | `S3Adapter` | `AsyncS3Adapter` |
| R2 | `R2Adapter` | `AsyncR2Adapter` |
| Registry slug | `local` / `s3` / `r2` | `local-async` / `s3-async` / `r2-async` |

Method signatures, kwargs, and return types are identical across the two — the async versions just need `await`. `stream()` is the one principled split: `Iterator[bytes]` on `Files`, `AsyncIterator[bytes]` on `AsyncFiles` (consume with `async for`).

## Quickstart — no credentials (Local)

Sync:

```python
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

Async:

```python
import asyncio
from files_sdk import AsyncFiles
from files_sdk_local import AsyncLocalAdapter

async def main():
    files = AsyncFiles(adapter=AsyncLocalAdapter(root="/tmp/my-store"))
    await files.upload("hello.txt", b"hi")
    print((await files.download("hello.txt")).text())

asyncio.run(main())
```

## Quickstart — Cloudflare R2

Sync:

```python
from files_sdk import Files
from files_sdk_r2 import R2Adapter

# Reads R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY from env
files = Files(adapter=R2Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
```

Async:

```python
from files_sdk import AsyncFiles
from files_sdk_r2 import AsyncR2Adapter

files = AsyncFiles(adapter=AsyncR2Adapter(bucket="my-bucket"))
await files.upload("hello.txt", b"hi")
```

## Quickstart — Amazon S3

Sync:

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

# Reads standard AWS env: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
files = Files(adapter=S3Adapter(bucket="my-bucket"))
```

Async:

```python
from files_sdk import AsyncFiles
from files_sdk_s3 import AsyncS3Adapter

files = AsyncFiles(adapter=AsyncS3Adapter(bucket="my-bucket"))
await files.upload("hello.txt", b"hi")
```

## Streaming (bounded memory)

```python
# Sync
with open("out.bin", "wb") as f:
    for chunk in files.stream("big.bin", chunk_size=1 << 20):
        f.write(chunk)

# Async
async for chunk in afiles.stream("big.bin", chunk_size=1 << 20):
    ...
```

## Adapter lookup by name

```python
from files_sdk import AsyncFiles, Files

files  = Files.from_name("local", root="/tmp/my-store")         # sync
files  = Files.from_name("s3", bucket="my-bucket")               # sync
afiles = AsyncFiles.from_name("s3-async", bucket="my-bucket")    # async
```

Crossing the wires — handing a sync adapter to `AsyncFiles` or vice versa — raises `FilesError("invalid_input")` at construction, so the two paths can never silently blend.

## API

Both `Files` and `AsyncFiles` expose the same surface. `await` the async ones.

| Method | Purpose |
|---|---|
| `upload(key, body, *, content_type=None, metadata=None, cache_control=None)` | Store an object. `body` is `bytes`, `str`, `Path`, or a file-like. |
| `download(key)` | Return a `StoredFile` (fully buffered). |
| `stream(key, *, chunk_size=65536)` | Yield chunks. `Iterator[bytes]` on `Files`, `AsyncIterator[bytes]` on `AsyncFiles`. |
| `head(key)` | Return `FileMetadata` without the body. |
| `delete(key)` | Remove an object. Idempotent (no error on missing). |
| `list(*, prefix=None, cursor=None, limit=1000)` | Paginated listing. Returns `ListPage`. |
| `copy(src, dst)` | Server-side copy. |
| `url(key, *, expires_in=3600, public=False)` | Signed or public URL. |
| `signed_upload_url(key, *, method="put"\|"post", expires_in=3600, ...)` | Browser-direct upload contract. |
| `raw` | Escape hatch — provider-native client (sync or async, matching the wrapper). |

Errors raise `FilesError` with `code` in `{"not_found", "unauthorized", "conflict", "provider", "invalid_input"}` and the original exception preserved via `__cause__`. The error type is shared across sync and async.
