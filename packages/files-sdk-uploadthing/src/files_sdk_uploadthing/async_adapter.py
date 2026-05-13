"""Asynchronous UploadThing adapter — mirrors `UploadThingAdapter`."""

from __future__ import annotations

import posixpath
import urllib.parse
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
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


async def _read_async_body(body: UploadBody) -> bytes:
    if isinstance(body, (bytes, bytearray, str, Path)):
        return body_to_bytes(body)
    return body.read()  # file-like — sync read; users wanting true-async should hand bytes


class AsyncUploadThingAdapter:
    name: ClassVar[str] = "uploadthing-async"

    def __init__(
        self,
        *,
        token: str | None = None,
        region: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._token = resolve_token(token, adapter_name="AsyncUploadThingAdapter")
        self._region = region or self._token.primary_region
        self._ingest_url = f"https://{self._region}.ingest.uploadthing.com"
        self._cdn_base = f"https://{self._token.app_id}.ufs.sh/f"
        self._timeout = timeout
        self._client = httpx.AsyncClient(
            base_url=API_BASE,
            headers={
                "x-uploadthing-api-key": self._token.api_key,
                "x-uploadthing-be-adapter": "files-sdk-python",
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    # ---- helpers -----------------------------------------------------------

    async def _post(self, op: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            resp = await self._client.post(path, json=payload)
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
        path = urllib.parse.quote(key.lstrip("/"), safe="/")
        return f"{self._cdn_base}/{path}"

    async def _resolve_cdn_url_via_api(self, key: str) -> str:
        resp = await self._post(
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

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        data = await _read_async_body(body)
        content_type = guess_content_type(key, opts.get("content_type"))
        file_name = posixpath.basename(key) or "file"
        signed_url, _ = self._presigned_upload_url(
            custom_id=key,
            file_name=file_name,
            file_size=len(data),
            content_type=content_type,
        )
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                resp = await client.put(
                    signed_url,
                    files={"file": (file_name, data, content_type)},
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

    async def download(self, key: str) -> StoredFile:
        url = self._cdn_url(key)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(url)
                if resp.status_code == 404:
                    url = await self._resolve_cdn_url_via_api(key)
                    resp = await client.get(url)
            except httpx.HTTPError as e:
                raise FilesError(
                    code="provider", message=f"download: {e}", provider=self.name
                ) from e
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

    def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        adapter = self

        async def gen() -> AsyncIterator[bytes]:
            url = adapter._cdn_url(key)
            async with httpx.AsyncClient(timeout=adapter._timeout, follow_redirects=True) as client:
                try:
                    probe = await client.get(url, headers={"Range": "bytes=0-0"})
                    if probe.status_code == 404:
                        url = await adapter._resolve_cdn_url_via_api(key)
                    async with client.stream("GET", url) as resp:
                        if resp.status_code == 404:
                            raise FilesError(
                                code="not_found",
                                message=f"stream: {key}",
                                provider=adapter.name,
                            )
                        if resp.status_code >= 400:
                            await resp.aread()
                            raise normalize_http_error("stream", resp.status_code, resp.content)
                        async for chunk in resp.aiter_bytes(chunk_size=chunk_size):
                            yield chunk
                except httpx.HTTPError as e:
                    raise FilesError(
                        code="provider", message=f"stream: {e}", provider=adapter.name
                    ) from e

        return gen()

    async def head(self, key: str) -> FileMetadata:
        url = self._cdn_url(key)
        async with httpx.AsyncClient(timeout=self._timeout, follow_redirects=True) as client:
            try:
                resp = await client.get(url, headers={"Range": "bytes=0-0"})
                if resp.status_code == 404:
                    url = await self._resolve_cdn_url_via_api(key)
                    resp = await client.get(url, headers={"Range": "bytes=0-0"})
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

    async def delete(self, key: str) -> None:
        try:
            await self._post(
                "delete",
                "/v6/deleteFiles",
                {"customIds": [key], "keyType": "customId"},
            )
        except FilesError as e:
            if e.code == "not_found":
                return
            raise

    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        offset = int(cursor) if cursor else 0
        resp = await self._post(
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

    async def copy(self, src: str, dst: str) -> FileMetadata:
        stored = await self.download(src)
        return await self.upload(dst, stored.data, content_type=stored.metadata.content_type)

    async def url(self, key: str, *, expires_in: int = DEFAULT_TTL, public: bool = False) -> str:
        if public:
            return self._cdn_url(key)
        resp = await self._post(
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

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
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
