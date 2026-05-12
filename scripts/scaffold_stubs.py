"""One-shot script to scaffold all 15 stub adapter packages from the template.

Run with:  uv run python scripts/scaffold_stubs.py
Idempotent: skips packages that already exist.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"

PROVIDERS: list[tuple[str, str]] = [
    ("akamai", "Akamai"),
    ("azure", "Azure"),
    ("box", "Box"),
    ("digitalocean", "DigitalOcean"),
    ("dropbox", "Dropbox"),
    ("gcs", "GCS"),
    ("gdrive", "GDrive"),
    ("hetzner", "Hetzner"),
    ("minio", "MinIO"),
    ("netlify", "Netlify"),
    ("onedrive", "OneDrive"),
    ("storj", "Storj"),
    ("supabase", "Supabase"),
    ("uploadthing", "UploadThing"),
    ("vercel", "Vercel"),
]

PYPROJECT_TMPL = '''\
[project]
name = "files-sdk-{suffix}"
version = "0.0.0"
description = "{cls} adapter for files-sdk (stub)"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
classifiers = [
    "Development Status :: 1 - Planning",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Typing :: Typed",
]
dependencies = [
    "files-sdk",
]

[project.entry-points."files_sdk.adapters"]
{suffix} = "files_sdk_{suffix}:{cls}Adapter"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/files_sdk_{suffix}"]

[tool.pytest.ini_options]
testpaths = ["tests"]
'''

CLAIM_TMPL = '''\
# Claim: {cls}

- **Claimed by:** (unclaimed)
- **Status:** stub — no implementation yet
- **Tracking issue:** TBD

To claim this adapter, edit this file with your name and open a PR. See
[`packages/_template/README.md`](../_template/README.md) for guidance.
'''

README_TMPL = '''\
# files-sdk-{suffix}

Stub adapter for **{cls}** in [files-sdk](../files-sdk). Not yet implemented.

See [CLAIM.md](./CLAIM.md) to claim and implement.
'''

INIT_TMPL = '''\
"""files-sdk-{suffix} — stub adapter."""

from .adapter import {cls}Adapter

__version__ = "0.0.0"
__all__ = ["{cls}Adapter"]
'''

ADAPTER_TMPL = '''\
"""Stub {cls} adapter — claim this in CLAIM.md and implement."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any, ClassVar

from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody


_NOT_IMPLEMENTED = (
    "files-sdk-{suffix} is a stub. See packages/files-sdk-{suffix}/CLAIM.md to claim it."
)


class {cls}Adapter:
    name: ClassVar[str] = "{suffix}"

    def __init__(self, **_: Any) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def download(self, key: str) -> StoredFile:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def head(self, key: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def delete(self, key: str) -> None:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def list(self, *, prefix: str | None = None, cursor: str | None = None,
             limit: int = 1000) -> ListPage:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def copy(self, src: str, dst: str) -> FileMetadata:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        raise NotImplementedError(_NOT_IMPLEMENTED)

    @property
    def raw(self) -> Any:
        raise NotImplementedError(_NOT_IMPLEMENTED)
'''

TEST_TMPL = '''\
"""Smoke test confirming the stub raises NotImplementedError."""

import pytest

from files_sdk_{suffix} import {cls}Adapter


def test_stub_raises_not_implemented() -> None:
    with pytest.raises(NotImplementedError):
        {cls}Adapter()
'''


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def scaffold_one(suffix: str, cls: str) -> bool:
    pkg = PACKAGES / f"files-sdk-{suffix}"
    if pkg.exists():
        print(f"skip (exists): {pkg.name}")
        return False
    write(pkg / "pyproject.toml", PYPROJECT_TMPL.format(suffix=suffix, cls=cls))
    write(pkg / "CLAIM.md", CLAIM_TMPL.format(cls=cls))
    write(pkg / "README.md", README_TMPL.format(suffix=suffix, cls=cls))
    src = pkg / "src" / f"files_sdk_{suffix}"
    write(src / "__init__.py", INIT_TMPL.format(suffix=suffix, cls=cls))
    write(src / "adapter.py", ADAPTER_TMPL.format(suffix=suffix, cls=cls))
    (src / "py.typed").write_text("")
    write(pkg / "tests" / "test_stub.py", TEST_TMPL.format(suffix=suffix, cls=cls))
    print(f"created: {pkg.name}")
    return True


def main() -> int:
    created = 0
    for suffix, cls in PROVIDERS:
        if scaffold_one(suffix, cls):
            created += 1
    print(f"\n{created} package(s) created, {len(PROVIDERS) - created} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
