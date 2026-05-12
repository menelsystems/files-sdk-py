# files-sdk (Python)

Python port of [files-sdk.dev](https://files-sdk.dev/). One unified API across
cloud object/blob storage providers.

## Packages

- **[files-sdk](packages/files-sdk/)** — core client, types, adapter protocol
- **[files-sdk-local](packages/files-sdk-local/)** — local filesystem (zero deps, ideal for dev/test)
- **[files-sdk-s3](packages/files-sdk-s3/)** — Amazon S3 (sync + async)
- **[files-sdk-r2](packages/files-sdk-r2/)** — Cloudflare R2 (sync + async)
- 15 stub packages awaiting implementation — see each `CLAIM.md`

## Quickstart (no cloud needed)

```bash
uv init my-app && cd my-app
uv add files-sdk files-sdk-local
```

```python
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

## Quickstart (S3)

```bash
uv add files-sdk files-sdk-s3
```

```python
from files_sdk import Files
from files_sdk_s3 import S3Adapter

files = Files(adapter=S3Adapter(bucket="my-bucket"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

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
