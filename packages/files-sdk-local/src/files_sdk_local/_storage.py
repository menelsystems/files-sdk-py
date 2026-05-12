"""Sync filesystem storage primitive shared by sync + async adapters."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import shutil
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from files_sdk.errors import FilesError
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile, UploadBody

_META_DIR = ".files-sdk-meta"

__all__ = ["_LocalStorage"]


class _LocalStorage:
    """Filesystem-backed object store. Used by LocalAdapter and AsyncLocalAdapter."""

    def __init__(self, root: str | Path, *, public_url_base: str | None = None) -> None:
        self.root = Path(root).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / _META_DIR).mkdir(exist_ok=True)
        self._public_url_base = public_url_base

    # ---- path helpers --------------------------------------------------------

    def _safe_path(self, key: str) -> Path:
        if not key or key.startswith("/") or "\0" in key:
            raise FilesError(
                code="invalid_input", message=f"invalid key: {key!r}", provider="local"
            )
        target = (self.root / key).resolve()
        try:
            target.relative_to(self.root)
        except ValueError as e:
            raise FilesError(
                code="invalid_input",
                message=f"key escapes root: {key!r}",
                provider="local",
            ) from e
        if target == self.root or _META_DIR in target.parts:
            raise FilesError(
                code="invalid_input", message=f"reserved key: {key!r}", provider="local"
            )
        return target

    def _meta_path(self, key: str) -> Path:
        return self.root / _META_DIR / (key + ".json")

    # ---- metadata sidecar ----------------------------------------------------

    def _write_meta(
        self,
        key: str,
        *,
        content_type: str | None,
        metadata: dict[str, str] | None,
        cache_control: str | None,
    ) -> None:
        mp = self._meta_path(key)
        mp.parent.mkdir(parents=True, exist_ok=True)
        mp.write_text(
            json.dumps(
                {
                    "content_type": content_type,
                    "metadata": dict(metadata or {}),
                    "cache_control": cache_control,
                }
            )
        )

    def _read_meta(self, key: str) -> dict[str, Any]:
        mp = self._meta_path(key)
        if not mp.exists():
            return {"content_type": None, "metadata": {}, "cache_control": None}
        return json.loads(mp.read_text())

    def _build_metadata(self, key: str, path: Path) -> FileMetadata:
        stat = path.stat()
        meta = self._read_meta(key)
        content_type = meta.get("content_type") or mimetypes.guess_type(key)[0]
        with path.open("rb") as f:
            etag = hashlib.md5(f.read()).hexdigest()
        return FileMetadata(
            key=key,
            size=stat.st_size,
            etag=etag,
            content_type=content_type,
            last_modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
            metadata=dict(meta.get("metadata") or {}),
        )

    # ---- API surface ---------------------------------------------------------

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        target = self._safe_path(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(body, (bytes, bytearray)):
            target.write_bytes(bytes(body))
        elif isinstance(body, str):
            target.write_bytes(body.encode("utf-8"))
        elif isinstance(body, Path):
            shutil.copyfile(body, target)
        else:
            # file-like
            with target.open("wb") as out:
                shutil.copyfileobj(body, out)
        self._write_meta(
            key,
            content_type=opts.get("content_type"),
            metadata=opts.get("metadata"),
            cache_control=opts.get("cache_control"),
        )
        return self._build_metadata(key, target)

    def download(self, key: str) -> StoredFile:
        target = self._safe_path(key)
        if not target.exists():
            raise FilesError(code="not_found", message=f"no such key: {key!r}", provider="local")
        data = target.read_bytes()
        meta = self._build_metadata(key, target)
        return StoredFile(metadata=meta, data=data)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        target = self._safe_path(key)
        if not target.exists():
            raise FilesError(code="not_found", message=f"no such key: {key!r}", provider="local")
        with target.open("rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    return
                yield chunk

    def head(self, key: str) -> FileMetadata:
        target = self._safe_path(key)
        if not target.exists():
            raise FilesError(code="not_found", message=f"no such key: {key!r}", provider="local")
        return self._build_metadata(key, target)

    def delete(self, key: str) -> None:
        target = self._safe_path(key)
        if target.exists():
            target.unlink()
        mp = self._meta_path(key)
        if mp.exists():
            mp.unlink()
        # idempotent — missing key is not an error

    def list(
        self, *, prefix: str | None = None, cursor: str | None = None, limit: int = 1000
    ) -> ListPage:
        items: list[FileMetadata] = []
        all_keys: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(self.root).as_posix()
            if rel.startswith(_META_DIR + "/") or rel == _META_DIR:
                continue
            if prefix is not None and not rel.startswith(prefix):
                continue
            all_keys.append(rel)

        start = 0
        if cursor is not None:
            try:
                start = int(cursor)
            except ValueError as e:
                raise FilesError(
                    code="invalid_input", message=f"bad cursor: {cursor!r}", provider="local"
                ) from e
        slice_keys = all_keys[start : start + limit]
        for key in slice_keys:
            items.append(self._build_metadata(key, self.root / key))
        next_cursor = str(start + limit) if start + limit < len(all_keys) else None
        return ListPage(items=items, cursor=next_cursor)

    def copy(self, src: str, dst: str) -> FileMetadata:
        src_path = self._safe_path(src)
        dst_path = self._safe_path(dst)
        if not src_path.exists():
            raise FilesError(code="not_found", message=f"no such key: {src!r}", provider="local")
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src_path, dst_path)
        src_meta = self._meta_path(src)
        if src_meta.exists():
            dst_meta = self._meta_path(dst)
            dst_meta.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src_meta, dst_meta)
        return self._build_metadata(dst, dst_path)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        target = self._safe_path(key)
        if public:
            base = self._public_url_base or os.environ.get("FILES_SDK_LOCAL_PUBLIC_URL_BASE")
            if not base:
                raise FilesError(
                    code="invalid_input",
                    message="public=True requires public_url_base= or FILES_SDK_LOCAL_PUBLIC_URL_BASE",
                    provider="local",
                )
            return f"{base.rstrip('/')}/{key}"
        return target.as_uri()

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        raise FilesError(
            code="invalid_input",
            message="signed_upload_url is not supported by LocalAdapter",
            provider="local",
        )
