# files-sdk-py workspace

Unified Python SDK for cloud object/blob storage. One API, swap the adapter to change backend.

## Layout

```
packages/
  files-sdk/          # core: Protocol, client, types, errors, conformance suite
  files-sdk-s3/            # Amazon S3 — sync (boto3) + async (aioboto3)
  files-sdk-r2/            # Cloudflare R2 — subclasses S3 adapter
  files-sdk-local/         # local filesystem — pure stdlib, zero deps
  files-sdk-uploadthing/   # UploadThing — httpx + ported HMAC presign (sync + async)
  files-sdk-minio/         # MinIO — subclasses S3 adapter
  files-sdk-digitalocean/  # DigitalOcean Spaces — subclasses S3 adapter
  files-sdk-hetzner/       # Hetzner Object Storage — subclasses S3 adapter
  files-sdk-linode/        # Linode Object Storage — subclasses S3 adapter
  files-sdk-storj/         # Storj DCS — subclasses S3 adapter
  files-sdk-<x>/           # 10 stub packages awaiting contributors
  _template/          # scaffold reference (NOT a workspace member)
tests/
  integration/        # live-backend tests (skipped without env vars)
```

## Setup

```bash
uv sync --all-packages   # install everything
uv run pytest            # all unit tests
uv run pyright           # type check
uv run ruff check .      # lint
uv run ruff format .     # format
```

## Testing

- Unit tests: `uv run pytest` — no external services needed
- Integration (rustfs): requires `FILES_SDK_INTEGRATION_ENDPOINT=http://...`
- Integration (real R2): requires `FILES_SDK_R2_INTEGRATION=1` + R2 env creds
- CI matrix: Python 3.11 / 3.12 / 3.13; integration job uses `rustfs/rustfs` Docker image

## Adapter entry points

Group: `files_sdk.adapters`

| name | class |
|---|---|
| `s3` | `files_sdk_s3.S3Adapter` |
| `s3-async` | `files_sdk_s3.AsyncS3Adapter` |
| `r2` | `files_sdk_r2.R2Adapter` |
| `r2-async` | `files_sdk_r2.AsyncR2Adapter` |
| `local` | `files_sdk_local.LocalAdapter` |
| `local-async` | `files_sdk_local.AsyncLocalAdapter` |
| `uploadthing` | `files_sdk_uploadthing.UploadThingAdapter` |
| `uploadthing-async` | `files_sdk_uploadthing.AsyncUploadThingAdapter` |
| `minio` | `files_sdk_minio.MinIOAdapter` |
| `minio-async` | `files_sdk_minio.AsyncMinIOAdapter` |
| `digitalocean` | `files_sdk_digitalocean.DigitalOceanAdapter` |
| `digitalocean-async` | `files_sdk_digitalocean.AsyncDigitalOceanAdapter` |
| `hetzner` | `files_sdk_hetzner.HetznerAdapter` |
| `hetzner-async` | `files_sdk_hetzner.AsyncHetznerAdapter` |
| `linode` | `files_sdk_linode.LinodeAdapter` |
| `linode-async` | `files_sdk_linode.AsyncLinodeAdapter` |
| `storj` | `files_sdk_storj.StorjAdapter` |
| `storj-async` | `files_sdk_storj.AsyncStorjAdapter` |

Look up by name: `Files.from_name("s3", bucket="my-bucket")`

## Error contract

Every adapter must translate provider-native exceptions to `FilesError` before they escape.
Valid codes: `"not_found"`, `"unauthorized"`, `"conflict"`, `"provider"`, `"invalid_input"`.
Never let `botocore.exceptions.ClientError` or equivalent reach the caller.

## Conventions

- pyright strict mode — no `type: ignore` without a comment explaining why
- ruff for lint + format; CI enforces both
- TDD: write conformance test assertions before implementing adapter methods
- `packages/_template` is excluded from `uv.workspace.members` — don't add it
- Stubs raise `NotImplementedError` from every method until claimed
