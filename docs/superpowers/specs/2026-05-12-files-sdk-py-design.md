# files-sdk-py — Design Spec

**Date:** 2026-05-12
**Status:** Approved (autonomous mode; design presented in conversation, no objections raised before writing)
**Owner:** Carter Himmel
**Target:** Python recreation of [files-sdk.dev](https://files-sdk.dev/)

---

## 1. Goal

Recreate `files-sdk.dev` (a JS unified-storage SDK) in Python with one unified API across cloud object/blob storage providers. v0 ships R2, S3, and Local (filesystem) adapters; the other 15 cloud providers are scaffolded as claimable stub packages.

**Why the Local adapter:** Pure-stdlib, zero-dep adapter that writes to a directory on disk. Makes the SDK immediately usable for dev/test/demo without any cloud credentials, and serves as a reference implementation that exercises the conformance suite without mocking.

**Non-goals (v0):**
- Not a CLI tool. Library only.
- Not an AI tool-factory layer. Deferred to v0.2.
- Not a streaming/multipart abstraction beyond what S3-style multipart already gives us.
- Not a port of the JS test suite. We write idiomatic Python tests.

## 2. Source-of-Truth API (JS SDK)

The JS `Files` class exposes nine methods. We mirror these one-to-one, renaming to snake_case:

| JS | Python |
|---|---|
| `files.upload(key, body, opts?)` | `files.upload(key, body, **opts)` |
| `files.download(key, opts?)` | `files.download(key, **opts)` |
| `files.head(key)` | `files.head(key)` |
| `files.delete(key)` | `files.delete(key)` |
| `files.list(opts?)` | `files.list(prefix=..., cursor=..., limit=...)` |
| `files.copy(from, to)` | `files.copy(src, dst)` |
| `files.url(key, opts?)` | `files.url(key, expires_in=..., public=...)` |
| `files.signedUploadUrl(key, opts)` | `files.signed_upload_url(key, method="put"\|"post", expires_in=...)` |
| `files.raw` | `files.raw` (property → provider-native client) |

Plus one Python-specific addition: `files.stream(key)` — yields chunks for memory-bounded reads. JS gets this implicitly via `ReadableStream`; Python needs an explicit method.

## 3. Workspace Layout

`uv` workspace with member packages:

```
files-sdk/
├── pyproject.toml                       # workspace root, declares members
├── uv.lock
├── README.md
├── docs/superpowers/specs/              # this spec lives here
├── packages/
│   ├── files-sdk/                       # core, no adapters
│   │   ├── pyproject.toml
│   │   └── src/files_sdk/
│   │       ├── __init__.py              # exports Files, AsyncFiles, FilesError
│   │       ├── client.py                # Files, AsyncFiles
│   │       ├── adapter.py               # Adapter, AsyncAdapter Protocols
│   │       ├── types.py                 # StoredFile, FileMetadata, ListPage
│   │       ├── errors.py                # FilesError + codes
│   │       ├── testing.py               # conformance_suite(adapter)
│   │       └── _registry.py             # entry-point resolver
│   ├── files-sdk-r2/
│   │   ├── pyproject.toml               # entry point: r2 = files_sdk_r2:R2Adapter
│   │   └── src/files_sdk_r2/
│   │       ├── __init__.py
│   │       └── adapter.py
│   ├── files-sdk-s3/
│   │   ├── pyproject.toml
│   │   └── src/files_sdk_s3/{__init__.py,adapter.py}
│   ├── files-sdk-local/                 # filesystem adapter, zero extra deps
│   │   ├── pyproject.toml               # entry point: local = files_sdk_local:LocalAdapter
│   │   └── src/files_sdk_local/
│   │       ├── __init__.py
│   │       ├── adapter.py               # LocalAdapter (sync)
│   │       └── async_adapter.py         # AsyncLocalAdapter (uses asyncio.to_thread)
│   ├── _template/                       # reference impl for contributors
│   │   ├── pyproject.toml.tmpl
│   │   ├── CLAIM.md.tmpl
│   │   └── src/files_sdk_PROVIDER/{__init__.py,adapter.py}
│   ├── files-sdk-akamai/                # stub
│   ├── files-sdk-azure/                 # stub
│   ├── files-sdk-box/                   # stub
│   ├── files-sdk-digitalocean/          # stub
│   ├── files-sdk-dropbox/               # stub
│   ├── files-sdk-gcs/                   # stub  (Google Cloud Storage)
│   ├── files-sdk-gdrive/                # stub  (Google Drive)
│   ├── files-sdk-hetzner/               # stub
│   ├── files-sdk-minio/                 # stub
│   ├── files-sdk-netlify/               # stub  (Netlify Blobs)
│   ├── files-sdk-onedrive/              # stub
│   ├── files-sdk-storj/                 # stub
│   ├── files-sdk-supabase/              # stub
│   ├── files-sdk-uploadthing/           # stub
│   └── files-sdk-vercel/                # stub  (Vercel Blob)
└── tests/                               # cross-package integration tests
```

Each stub package contains:
- `pyproject.toml` with name `files-sdk-<provider>` and a `[project.entry-points."files_sdk.adapters"]` registration
- `src/files_sdk_<provider>/adapter.py` defining `<Provider>Adapter` that raises `NotImplementedError("adapter not yet implemented; see CLAIM.md")` on every method
- `CLAIM.md` with template: `# Claim: <provider>\n\nClaimed by: (unclaimed)\nStatus: stub\nTracking issue: TBD`

## 4. Public API

### 4.1 Construction

```python
from files_sdk import Files, AsyncFiles
from files_sdk_r2 import R2Adapter
from files_sdk_s3 import S3Adapter

# Explicit (primary, type-safe):
files = Files(adapter=R2Adapter(
    bucket="my-bucket",
    account_id="...",                # or env: R2_ACCOUNT_ID
    access_key_id="...",             # or env: R2_ACCESS_KEY_ID
    secret_access_key="...",         # or env: R2_SECRET_ACCESS_KEY
))

# By name (sugar, resolved via entry points):
files = Files.from_name("s3", bucket="my-bucket", region="us-east-1")

# Async equivalent:
afiles = AsyncFiles(adapter=R2Adapter(...))
```

`R2Adapter()` and `S3Adapter()` called with **no args** auto-load from env. If required vars are missing, raises `FilesError(code="unauthorized")` at construction.

### 4.2 Methods

```python
# Returns FileMetadata
files.upload(
    key: str,
    body: bytes | str | BinaryIO | Path,
    *,
    content_type: str | None = None,
    metadata: dict[str, str] | None = None,
    cache_control: str | None = None,
) -> FileMetadata

# Returns StoredFile (fully buffered)
files.download(key: str) -> StoredFile

# Returns Iterator[bytes] / AsyncIterator[bytes]
files.stream(key: str, *, chunk_size: int = 65536) -> Iterator[bytes]

files.head(key: str) -> FileMetadata
files.delete(key: str) -> None                    # idempotent; no error on missing
files.list(*, prefix: str | None = None,
           cursor: str | None = None,
           limit: int = 1000) -> ListPage
files.copy(src: str, dst: str) -> FileMetadata
files.url(key: str, *, expires_in: int = 3600,
          public: bool = False) -> str
files.signed_upload_url(
    key: str, *,
    expires_in: int = 3600,
    method: Literal["put", "post"] = "put",
    content_type: str | None = None,
    max_size: int | None = None,
) -> SignedUpload                                  # url + headers + (for POST) fields

files.raw                                           # property -> provider-native client
```

### 4.3 Types

```python
# pydantic v2 models
class FileMetadata(BaseModel):
    key: str
    size: int
    etag: str | None
    content_type: str | None
    last_modified: datetime
    metadata: dict[str, str]

class StoredFile(BaseModel):
    metadata: FileMetadata
    data: bytes
    # convenience: stored.as_bytes(), stored.text(encoding="utf-8")

class ListPage(BaseModel):
    items: list[FileMetadata]
    cursor: str | None        # next page token; None = end

class SignedUpload(BaseModel):
    url: str
    method: Literal["PUT", "POST"]
    headers: dict[str, str]
    fields: dict[str, str] | None    # form fields for POST
    expires_at: datetime
```

## 5. Adapter Protocol

`files_sdk.adapter` defines two `Protocol` classes (PEP 544, `runtime_checkable`):

```python
class Adapter(Protocol):
    name: ClassVar[str]
    def upload(self, key, body, **opts) -> FileMetadata: ...
    def download(self, key) -> StoredFile: ...
    def stream(self, key, *, chunk_size) -> Iterator[bytes]: ...
    def head(self, key) -> FileMetadata: ...
    def delete(self, key) -> None: ...
    def list(self, *, prefix, cursor, limit) -> ListPage: ...
    def copy(self, src, dst) -> FileMetadata: ...
    def url(self, key, *, expires_in, public) -> str: ...
    def signed_upload_url(self, key, **opts) -> SignedUpload: ...
    @property
    def raw(self) -> Any: ...

class AsyncAdapter(Protocol):
    # Identical surface but all methods are async (stream returns AsyncIterator)
    ...
```

An adapter package may ship **either or both** sync/async adapter classes. `Files(adapter=...)` rejects an `AsyncAdapter`; `AsyncFiles(adapter=...)` rejects a sync `Adapter`. Both checks happen at construction with a clear `FilesError(code="invalid_input")`.

## 6. Plugin Discovery

Two equivalent paths:

**1. Explicit imports (primary):**
```python
from files_sdk_r2 import R2Adapter
Files(adapter=R2Adapter(...))
```

**2. Name lookup (sugar):**
```python
Files.from_name("r2", bucket=...)
```

Backed by `importlib.metadata.entry_points(group="files_sdk.adapters")`. Each adapter package registers:

```toml
[project.entry-points."files_sdk.adapters"]
r2 = "files_sdk_r2:R2Adapter"
```

Unknown name → `FilesError(code="invalid_input", message="no adapter named 'foo'; install files-sdk-foo")`.

## 7. Error Model

```python
class FilesError(Exception):
    code: Literal["not_found", "unauthorized", "conflict",
                  "provider", "invalid_input"]
    provider: str | None     # adapter.name when raised by an adapter
    message: str
    # original exception always preserved via raise ... from original
```

Adapter rule: **never let a provider-native exception escape**. Each adapter wraps boundary calls in try/except and translates:
- 404 / NoSuchKey → `not_found`
- 401/403 / SignatureDoesNotMatch → `unauthorized`
- 412 / PreconditionFailed → `conflict`
- everything else → `provider` (with original as `__cause__`)
- adapter-internal validation failures → `invalid_input`

`delete()` on a missing key does **not** raise — matches JS SDK idempotency.

## 8. Adapter Implementation (v0)

### S3Adapter (`files-sdk-s3`)
- v0 ships **both** sync (`S3Adapter`) and async (`AsyncS3Adapter`) classes from the same package.
- Sync uses `boto3`; async uses `aioboto3`. Async is a default dependency (not an extra) in v0 to keep the matrix simple.
- Env vars: standard AWS chain (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `AWS_SESSION_TOKEN`).
- Multipart threshold: `multipart_threshold` constructor arg, default 8 MiB.
- `signed_upload_url(method="post")` returns a POST policy doc.
- Entry points register both: `s3 = files_sdk_s3:S3Adapter`, `s3-async = files_sdk_s3:AsyncS3Adapter`. (Convention: `<name>-async` suffix for async variant when both shipped.)

### R2Adapter (`files-sdk-r2`)
- v0 ships **both** sync (`R2Adapter`) and async (`AsyncR2Adapter`).
- Cloudflare R2 is S3-compatible. Implementation: `R2Adapter` subclasses `S3Adapter` (and `AsyncR2Adapter` subclasses `AsyncS3Adapter`), overriding endpoint URL to `https://<account_id>.r2.cloudflarestorage.com`. This means `files-sdk-r2` declares `files-sdk-s3` as a dependency.
- Env vars: `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_BUCKET` (optional default).
- `public=True` on `url()` returns the public r2.dev URL when bucket has public access enabled; otherwise raises `invalid_input`.

### LocalAdapter (`files-sdk-local`)
- v0 ships **both** sync (`LocalAdapter`) and async (`AsyncLocalAdapter`).
- Zero extra deps. Pure stdlib (`pathlib`, `hashlib`, `mimetypes`, `asyncio`, `secrets`).
- Constructor: `LocalAdapter(root: str | Path, *, public_url_base: str | None = None)`. `root` is created if it doesn't exist. All keys are stored under `root/`.
- **Key layout:** the object key is interpreted as a relative path under `root`. Subdirectories are auto-created on upload. Reject keys that escape `root` (resolved real path must stay inside) — raises `invalid_input`.
- **Metadata:** Stored side-by-side in `root/.files-sdk-meta/<key>.json` (content_type, user metadata, cache_control, etag-as-md5). `head()` reads this; if absent, infers content_type from `mimetypes.guess_type` and computes etag lazily.
- **`url()`:**
  - `public=True` requires `public_url_base` (or `FILES_SDK_LOCAL_PUBLIC_URL_BASE` env). Returns `f"{base}/{key}"`. Raises `invalid_input` otherwise.
  - `public=False` returns a `file://` URL pointing at the resolved path. `expires_in` is ignored (no signing for local fs; documented).
- **`signed_upload_url()`:** Not meaningfully supported on a local fs. Raises `FilesError(code="invalid_input", message="signed_upload_url is not supported by LocalAdapter")`. Documented exception in the conformance suite (skip on `LocalAdapter`).
- **Async impl:** `AsyncLocalAdapter` wraps the sync calls in `asyncio.to_thread` to avoid blocking the event loop on disk I/O. Acceptable for v0; a fully native aiofiles-based impl is a follow-up.
- Entry points: `local = files_sdk_local:LocalAdapter`, `local-async = files_sdk_local:AsyncLocalAdapter`.

## 9. Testing Strategy

### 9.1 Conformance Suite
`files_sdk.testing.conformance_suite()` is a parametrized pytest fixture every adapter package imports:

```python
# packages/files-sdk-s3/tests/test_conformance.py
from files_sdk.testing import conformance_suite
from files_sdk_s3 import S3Adapter

@pytest.fixture
def adapter():
    return S3Adapter(bucket="test-bucket", endpoint_url="http://localhost:9000")

conformance_suite()   # injects all 30+ test cases
```

Tests cover: upload-then-download round-trip, head metadata correctness, list pagination, delete idempotency, copy, signed URL validity, error code mapping (force a 404 → assert `not_found`), Unicode keys, zero-byte uploads, large (>multipart threshold) uploads.

### 9.2 Backends for tests
- **S3:** `moto` (in-process mock) for unit; `minio` via testcontainers for integration.
- **R2:** the S3 moto path covers ~95%; gated real-R2 tests behind `FILES_SDK_R2_INTEGRATION=1`.
- **Local:** uses `tmp_path` pytest fixture for an isolated dir per test. No mocks needed — this adapter is the cleanest target for the conformance suite. `signed_upload_url` cases are skipped via `pytest.mark.skip` injected into the conformance suite when the adapter has `supports_signed_upload = False` (class attribute, defaults to `True`).

### 9.3 Stub adapters
Every stub adapter package ships a test that asserts `NotImplementedError` is raised so the conformance suite doesn't silently regress.

## 10. Tooling

- **Package manager / workspace:** `uv` (workspace mode)
- **Build backend:** `hatchling` per package
- **Linter + formatter:** `ruff` (single config at root, inherited)
- **Type checker:** `pyright` in strict mode
- **Tests:** `pytest`, `pytest-asyncio` (mode=auto), `moto[s3]`
- **CI:** GitHub Actions matrix over Python 3.11, 3.12, 3.13
- **Versions:** independent per package, but workspace ships them in lockstep for v0

`pyproject.toml` at root:
```toml
[tool.uv.workspace]
members = ["packages/*"]
exclude = ["packages/_template"]
```

## 11. Deferred / Out of Scope (v0)

- AI tool factories (`files_sdk.tools.openai`, `.anthropic`, `.pydantic_ai`) — v0.2.
- CLI (`files-sdk ls s3://...`) — not planned.
- Retry/backoff middleware — adapters delegate to their underlying SDK's retry config.
- Browser/Worker runtime parity — N/A in Python.
- Tree-shaking analog — Python imports are already lazy at the module level.

## 12. Decided (was "unresolved" in brainstorm)

| Question | Decision |
|---|---|
| Stream API? | Both: `download()` buffers, `stream()` yields chunks. |
| Multipart threshold? | Adapter-init kwarg `multipart_threshold`, default 8 MiB. |
| AI tools in v0? | No, defer to v0.2. |
| Sync, async, or both? | Both — `Files` and `AsyncFiles`, matching `anthropic`/`openai` SDK convention. |
| Plugin discovery? | Explicit imports primary; `Files.from_name()` sugar via entry points. |
| Stub packages — publishable? | Yes, but with `0.0.0` version and a `Development Status :: 1 - Planning` classifier. Prevents name-squatting and gives contributors a real handle. |

## 13. Acceptance Criteria for v0

- [ ] `uv sync` at workspace root resolves all packages
- [ ] `pytest` passes for `files-sdk`, `files-sdk-r2`, `files-sdk-s3`, `files-sdk-local`
- [ ] `pyright --strict` clean on all four first-party packages
- [ ] Conformance suite passes for: Local (tmp_path), R2 (via moto+endpoint shim), S3 (moto)
- [ ] `Files.from_name("r2", ...)`, `Files.from_name("s3", ...)`, `Files.from_name("local", root=...)` all resolve correctly
- [ ] All 15 stub packages installable, register entry points, and raise `NotImplementedError` from the conformance suite
- [ ] README in `packages/files-sdk` shows the 9-method API with a worked R2 example AND a Local quickstart that needs no credentials

## 14. Open Items (not blocking implementation)

None — all v0 decisions are made above. Items that arise during plan-writing get tracked in the implementation plan, not here.
