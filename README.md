# files-sdk (Python)

Python port of [files-sdk.dev](https://files-sdk.dev/). One unified API across
cloud object/blob storage providers — **sync and async, both first-class**.

Every adapter ships in two flavours that mirror each other line-for-line:

| Sync | Async |
|---|---|
| `Files` + `LocalAdapter` / `S3Adapter` / `R2Adapter` | `AsyncFiles` + `AsyncLocalAdapter` / `AsyncS3Adapter` / `AsyncR2Adapter` |

Pick whichever fits your stack — no `asyncio.run` glue, no sync-wrapped-around-async hack. Same method names, same return types, same errors.

## Packages

- **[files-sdk](packages/files-sdk/)** — core clients (`Files`, `AsyncFiles`), types, adapter protocols
- **[files-sdk-local](packages/files-sdk-local/)** — local filesystem, sync + async (zero deps, ideal for dev/test)
- **[files-sdk-s3](packages/files-sdk-s3/)** — Amazon S3, sync + async
- **[files-sdk-r2](packages/files-sdk-r2/)** — Cloudflare R2, sync + async
- **[files-sdk-uploadthing](packages/files-sdk-uploadthing/)** — UploadThing, sync + async
- **[files-sdk-minio](packages/files-sdk-minio/)** — MinIO, sync + async
- **[files-sdk-digitalocean](packages/files-sdk-digitalocean/)** — DigitalOcean Spaces, sync + async
- **[files-sdk-hetzner](packages/files-sdk-hetzner/)** — Hetzner Object Storage, sync + async
- **[files-sdk-linode](packages/files-sdk-linode/)** — Linode Object Storage, sync + async
- **[files-sdk-storj](packages/files-sdk-storj/)** — Storj DCS, sync + async
- 10 stub packages awaiting implementation (including `files-sdk-akamai` for Akamai NetStorage, distinct from the Linode adapter above) — see each `CLAIM.md`

## Quickstart (no cloud needed)

```bash
uv init my-app && cd my-app
uv add files-sdk files-sdk-local
```

Sync:

```python
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

Async — same API, just `await`:

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

## Quickstart (S3)

```bash
uv add files-sdk files-sdk-s3
```

Sync:

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

Async:

```python
from files_sdk import AsyncFiles
from files_sdk_s3 import AsyncS3Adapter

files = AsyncFiles(adapter=AsyncS3Adapter(bucket="my-bucket"))
await files.upload("hello.txt", b"hi")
print((await files.download("hello.txt")).text())
```

`AsyncFiles.stream(key)` returns an `AsyncIterator[bytes]` (use `async for`); `Files.stream(key)` returns a regular `Iterator[bytes]`. Every other method is a 1:1 sync↔async pairing.

## Adapter lookup by name

```python
from files_sdk import AsyncFiles, Files

files  = Files.from_name("s3", bucket="my-bucket")            # sync
afiles = AsyncFiles.from_name("s3-async", bucket="my-bucket")  # async
```

Registry slugs follow `<provider>` for sync and `<provider>-async` for async (`local` / `local-async`, `s3` / `s3-async`, `r2` / `r2-async`). Crossing the wires — handing a sync adapter to `AsyncFiles` or vice versa — raises `FilesError("invalid_input")` at construction.

## One-shot script (no project setup)

Embed dependencies inline with [PEP 723](https://peps.python.org/pep-0723/):

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["files-sdk", "files-sdk-local"]
# ///
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
```

Don't have `uv`? Install it: `curl -LsSf https://astral.sh/uv/install.sh | sh` ([docs](https://docs.astral.sh/uv/)). `pip install files-sdk files-sdk-local` works too.

## Development

```bash
uv sync
uv run pytest
uv run pyright
uv run ruff check .
```

See [`docs/superpowers/specs/`](docs/superpowers/specs/) for design docs.

## Contributing a new adapter

Pick a stub from `packages/files-sdk-<provider>/CLAIM.md` and follow
[`packages/_template/README.md`](packages/_template/README.md).
