"""Synchronous UploadThing adapter.

UploadThing's API has three meaningful mismatches with the `Adapter` protocol;
this module papers over them:

  * **No user-chosen storage path** — files have an opaque `fileKey` chosen by
    the server side. UploadThing supports a parallel `customId` field that
    every read/delete API can be keyed by (`keyType: "customId"`). We map the
    adapter's `key: str` → UT's `customId`, so callers see normal path-like
    keys (`"users/123/avatar.png"`) end-to-end. The internal `fileKey` is
    generated locally and never surfaced.
  * **No prefix filter on listFiles** — we fetch a page from the API and
    filter by prefix in Python. The cursor is a stringified offset.
  * **No server-side copy** — we download then reupload. Costs bandwidth and a
    second presigned URL; documented but unavoidable.

Auth: `UPLOADTHING_TOKEN` is base64 JSON `{apiKey, appId, regions}`; only the
decoded `apiKey` is sent (as the `x-uploadthing-api-key` header). The token
itself never leaves the client.
"""

from __future__ import annotations

import contextlib
import posixpath
import urllib.parse
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar, cast

import httpx
from files_sdk.errors import FilesError
from files_sdk.types import (
    FileMetadata,
    ListPage,
    SignedUpload,
    StoredFile,
    UploadBody,
)

from ._helpers import (
    API_BASE,
    DEFAULT_TTL,
    body_to_bytes,
    clean_etag,
    extract_url_from_get_file_url_response,
    guess_content_type,
    normalize_http_error,
    parse_last_modified,
    resolve_token,
    size_from_range_headers,
)
from ._signing import generate_file_key, generate_signed_url


class UploadThingAdapter:
    """Synchronous UploadThing storage adapter.

    Keys are mapped to UploadThing's `customId` field, so the same path used
    here can be used to read/delete the file later. The opaque per-file
    `fileKey` is generated locally and never surfaced through this interface.
    """

    name: ClassVar[str] = "uploadthing"

    def __init__(
        self,
        *,
        token: str | None = None,
        region: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._token = resolve_token(token, adapter_name="UploadThingAdapter")
        self._region = region or self._token.primary_region
        self._ingest_url = f"https://{self._region}.ingest.uploadthing.com"
        self._cdn_base = f"https://{self._token.app_id}.ufs.sh/f"
        self._client = httpx.Client(
            base_url=API_BASE,
            headers={
                "x-uploadthing-api-key": self._token.api_key,
                "x-uploadthing-be-adapter": "files-sdk-python",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    # ---- helpers -----------------------------------------------------------

    def _post(self, op: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = self._client.post(path, json=payload)
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"{op}: {e}", provider=self.name) from e
        if resp.status_code >= 400:
            raise normalize_http_error(op, resp.status_code, resp.content)
        if not resp.content:
            return {}
        try:
            data: object = resp.json()
        except ValueError:
            return {}
        if isinstance(data, dict):
            return cast("dict[str, Any]", data)
        return {"data": data}

    def _cdn_url(self, key: str) -> str:
        # Preserve `/` separators in the customId path; encode everything else
        # (unicode, spaces, reserved chars) so the request URL is well-formed.
        path = urllib.parse.quote(key.lstrip("/"), safe="/")
        return f"{self._cdn_base}/{path}"

    def _resolve_cdn_url_via_api(self, key: str) -> str:
        """Resolve a customId to its fileKey-based CDN URL via `/v6/getFileUrl`.

        Used as a fallback when direct CDN routing by customId returns 404 —
        UploadThing's CDN edge doesn't resolve customIds with unicode or
        whitespace, even though the file exists. The API does the
        customId→fileKey lookup server-side, and the returned URL routes
        by fileKey which always works.
        """
        resp = self._post(
            "getFileUrl",
            "/v6/getFileUrl",
            {"customIds": [key], "keyType": "customId"},
        )
        url = extract_url_from_get_file_url_response(resp)
        if url is None:
            raise FilesError(code="not_found", message=f"getFileUrl: {key}", provider=self.name)
        return url

    def _presigned_upload_url(
        self,
        *,
        custom_id: str,
        file_name: str,
        file_size: int,
        content_type: str,
        ttl_seconds: int = DEFAULT_TTL,
    ) -> tuple[str, str]:
        """Return `(signed_url, file_key)`."""
        file_key = generate_file_key(
            self._token.app_id,
            file_name=file_name,
            file_size=file_size,
            file_type=content_type,
        )
        url = f"{self._ingest_url}/{file_key}"
        signed = generate_signed_url(
            url,
            secret=self._token.api_key,
            ttl_seconds=ttl_seconds,
            data={
                "x-ut-identifier": self._token.app_id,
                "x-ut-file-name": file_name,
                "x-ut-file-size": file_size,
                "x-ut-file-type": content_type,
                "x-ut-custom-id": custom_id,
                "x-ut-content-disposition": "inline",
            },
        )
        return signed, file_key

    # ---- public API --------------------------------------------------------

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        data = body_to_bytes(body)
        content_type = guess_content_type(key, opts.get("content_type"))
        file_name = posixpath.basename(key) or "file"
        signed_url, _ = self._presigned_upload_url(
            custom_id=key,
            file_name=file_name,
            file_size=len(data),
            content_type=content_type,
        )
        try:
            resp = httpx.put(
                signed_url,
                files={"file": (file_name, data, content_type)},
                timeout=self._client.timeout,
            )
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"upload: {e}", provider=self.name) from e
        if resp.status_code >= 400:
            raise normalize_http_error("upload", resp.status_code, resp.content)
        return FileMetadata(
            key=key,
            size=len(data),
            etag=None,
            content_type=content_type,
            last_modified=datetime.now(UTC),
            metadata={},
        )

    def download(self, key: str) -> StoredFile:
        url = self._cdn_url(key)
        try:
            resp = httpx.get(url, timeout=self._client.timeout, follow_redirects=True)
            if resp.status_code == 404:
                url = self._resolve_cdn_url_via_api(key)
                resp = httpx.get(url, timeout=self._client.timeout, follow_redirects=True)
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"download: {e}", provider=self.name) from e
        if resp.status_code == 404:
            raise FilesError(code="not_found", message=f"download: {key}", provider=self.name)
        if resp.status_code >= 400:
            raise normalize_http_error("download", resp.status_code, resp.content)
        return StoredFile(
            metadata=FileMetadata(
                key=key,
                size=len(resp.content),
                etag=clean_etag(resp.headers.get("etag")),
                content_type=resp.headers.get("content-type"),
                last_modified=parse_last_modified(resp.headers.get("last-modified")),
                metadata={},
            ),
            data=resp.content,
        )

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        url = self._cdn_url(key)
        # Probe with a ranged GET to spot 404s before opening a streaming
        # connection. If the customId doesn't resolve directly, fall back to
        # the fileKey URL via /v6/getFileUrl.
        try:
            probe = httpx.get(
                url,
                headers={"Range": "bytes=0-0"},
                timeout=self._client.timeout,
                follow_redirects=True,
            )
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"stream: {e}", provider=self.name) from e
        if probe.status_code == 404:
            url = self._resolve_cdn_url_via_api(key)
        try:
            with httpx.stream(
                "GET", url, timeout=self._client.timeout, follow_redirects=True
            ) as resp:
                if resp.status_code == 404:
                    raise FilesError(code="not_found", message=f"stream: {key}", provider=self.name)
                if resp.status_code >= 400:
                    resp.read()
                    raise normalize_http_error("stream", resp.status_code, resp.content)
                yield from resp.iter_bytes(chunk_size=chunk_size)
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"stream: {e}", provider=self.name) from e

    def head(self, key: str) -> FileMetadata:
        url = self._cdn_url(key)
        # Cloudflare's CDN returns `content-length: 0` on cold HEAD for some
        # paths; a one-byte ranged GET reliably surfaces the full size via
        # `Content-Range: bytes 0-0/N`. Trades 1 byte of network per call for
        # correct metadata.
        try:
            resp = httpx.get(
                url,
                headers={"Range": "bytes=0-0"},
                timeout=self._client.timeout,
                follow_redirects=True,
            )
            if resp.status_code == 404:
                url = self._resolve_cdn_url_via_api(key)
                resp = httpx.get(
                    url,
                    headers={"Range": "bytes=0-0"},
                    timeout=self._client.timeout,
                    follow_redirects=True,
                )
        except httpx.HTTPError as e:
            raise FilesError(code="provider", message=f"head: {e}", provider=self.name) from e
        if resp.status_code == 404:
            raise FilesError(code="not_found", message=f"head: {key}", provider=self.name)
        if resp.status_code >= 400:
            raise normalize_http_error("head", resp.status_code, resp.content)
        return FileMetadata(
            key=key,
            size=size_from_range_headers(resp.headers),
            etag=clean_etag(resp.headers.get("etag")),
            content_type=resp.headers.get("content-type"),
            last_modified=parse_last_modified(resp.headers.get("last-modified")),
            metadata={},
        )

    def delete(self, key: str) -> None:
        try:
            self._post(
                "delete",
                "/v6/deleteFiles",
                {"customIds": [key], "keyType": "customId"},
            )
        except FilesError as e:
            # UploadThing's `deleteFiles` is documented to succeed with
            # `deletedCount: 0` on missing keys, but empirically this hasn't
            # been verified — swallow `not_found` to keep the contract.
            if e.code == "not_found":
                return
            raise

    def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        # UploadThing's listFiles is offset-based with no prefix filter.
        # We fetch one page, filter client-side, and stringify the next offset
        # as the cursor. For accounts with many files outside the prefix this
        # is wasteful — document the trade-off; users with very large blobs
        # should reach for a real object store.
        offset = int(cursor) if cursor else 0
        resp = self._post(
            "list",
            "/v6/listFiles",
            {"limit": limit, "offset": offset},
        )
        raw_files = resp.get("files", [])
        items: list[FileMetadata] = []
        for f in raw_files:
            cid = f.get("customId") or f.get("key")
            if not isinstance(cid, str):
                continue
            if prefix and not cid.startswith(prefix):
                continue
            items.append(
                FileMetadata(
                    key=cid,
                    size=int(f.get("size", 0)),
                    etag=None,
                    content_type=None,
                    last_modified=datetime.fromtimestamp(int(f.get("uploadedAt", 0)) / 1000, tz=UTC)
                    if f.get("uploadedAt")
                    else datetime.now(UTC),
                    metadata={},
                )
            )
        has_more = bool(resp.get("hasMore"))
        next_offset = offset + len(raw_files) if has_more else None
        return ListPage(items=items, cursor=str(next_offset) if next_offset is not None else None)

    def copy(self, src: str, dst: str) -> FileMetadata:
        # UploadThing has no server-side copy. Round-trip through the client.
        stored = self.download(src)
        return self.upload(dst, stored.data, content_type=stored.metadata.content_type)

    def url(self, key: str, *, expires_in: int = DEFAULT_TTL, public: bool = False) -> str:
        if public:
            return self._cdn_url(key)
        resp = self._post(
            "url",
            "/v6/requestFileAccess",
            {"customId": key, "expiresIn": expires_in},
        )
        signed = resp.get("url")
        if not isinstance(signed, str):
            raise FilesError(
                code="provider",
                message="url: requestFileAccess did not return a url",
                provider=self.name,
            )
        return signed

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        method = str(opts.get("method", "put")).lower()
        if method != "put":
            raise FilesError(
                code="invalid_input",
                message=(
                    f"unknown signed_upload_url method: {method!r} "
                    "(uploadthing only supports method='put')"
                ),
                provider=self.name,
            )
        expires_in = int(opts.get("expires_in", DEFAULT_TTL))
        content_type = opts.get("content_type") or "application/octet-stream"
        file_size = int(opts.get("max_size", 0))
        file_name = posixpath.basename(key) or "file"
        signed_url, _ = self._presigned_upload_url(
            custom_id=key,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            ttl_seconds=expires_in,
        )
        # Note: uploads to this URL must use multipart/form-data with the file
        # in the `file` field — not a raw PUT body. We surface method="PUT"
        # to match the adapter protocol; the Content-Type header is the
        # multipart boundary, set by the HTTP client at request time.
        return SignedUpload(
            url=signed_url,
            method="PUT",
            headers={},
            fields=None,
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
        )

    @property
    def raw(self) -> Any:
        return self._client

    def __del__(self) -> None:
        client = getattr(self, "_client", None)
        if client is not None:
            with contextlib.suppress(Exception):
                client.close()
