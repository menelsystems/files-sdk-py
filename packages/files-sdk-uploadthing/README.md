# files-sdk-uploadthing

[UploadThing](https://uploadthing.com) adapter for [files-sdk](../files-sdk).
Sync and async variants over `httpx`, with locally-computed HMAC presigned
URLs (ported from the upstream TypeScript SDK — no UT-side roundtrip for
upload URL generation).

## Install

```bash
uv add files-sdk files-sdk-uploadthing
```

## Usage

```python
from files_sdk import Files
from files_sdk_uploadthing import UploadThingAdapter

files = Files(adapter=UploadThingAdapter())   # reads UPLOADTHING_TOKEN
files.upload("users/123/avatar.png", b"...")
print(files.download("users/123/avatar.png").as_bytes())
```

Async:

```python
from files_sdk_uploadthing import AsyncUploadThingAdapter

a = AsyncUploadThingAdapter()
await a.upload("users/123/avatar.png", b"...")
```

## Auth

Set `UPLOADTHING_TOKEN` (the base64 JSON token from your UploadThing
dashboard's API Keys page) in the environment, or pass `token=` explicitly.
The decoded `apiKey` is the only secret sent — the token's `appId` and
`regions` are extracted client-side.

## Notes on the protocol mapping

The adapter's `key: str` maps to UploadThing's `customId`, so paths like
`users/123/avatar.png` round-trip cleanly. The opaque per-file `fileKey` is
generated client-side and never surfaced. A few protocol mismatches are
handled transparently:

- **No prefix filter on `listFiles`** — fetched pages are filtered in Python.
  The `cursor` is a stringified offset. Large accounts will see this.
- **No server-side `copy`** — implemented as download + reupload.
- **No HEAD endpoint** — `head()` uses a one-byte ranged GET; the
  `Content-Range` header carries the true size.
- **CDN routing by `customId` doesn't resolve unicode keys** — falls back
  to `/v6/getFileUrl` (one extra API roundtrip) when the direct fetch 404s.

## Development

Live conformance tests require `UPLOADTHING_TOKEN`:

```bash
export UPLOADTHING_TOKEN=eyJh...
uv run pytest packages/files-sdk-uploadthing/
```

Without the token, only the offline tests (`_token`, `_signing`, `_hash`)
run; the conformance suite skips.
