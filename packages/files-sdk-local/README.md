# files-sdk-local

Local filesystem adapter for [files-sdk](../files-sdk). Zero extra dependencies.
Ideal for dev, tests, demos, and offline tooling.

```python
from files_sdk import Files
from files_sdk_local import LocalAdapter

files = Files(adapter=LocalAdapter(root="/tmp/my-store"))
files.upload("hello.txt", b"hi")
print(files.download("hello.txt").text())
```

## Notes
- Objects live at `<root>/<key>`. Subdirectories are auto-created.
- Sidecar metadata at `<root>/.files-sdk-meta/<key>.json` records content-type and user metadata.
- `signed_upload_url()` is NOT supported (no signing authority on local fs) — raises `FilesError(code="invalid_input")`. The class attribute `supports_signed_upload = False` lets the conformance suite skip cleanly.
- `url(key, public=False)` returns `file://...`. With `public=True` and `public_url_base=` (or env `FILES_SDK_LOCAL_PUBLIC_URL_BASE`) it returns `<base>/<key>` — useful when a webserver serves `root` over HTTP.
- Keys are sanitized: anything that resolves outside `root` raises `FilesError(code="invalid_input")`.
