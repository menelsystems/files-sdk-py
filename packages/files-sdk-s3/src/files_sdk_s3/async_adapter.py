"""Asynchronous S3 adapter using aioboto3."""

from __future__ import annotations

import io
import os
from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, ClassVar

import aioboto3
from botocore.exceptions import ClientError
from files_sdk.errors import FilesError
from files_sdk.types import (
    FileMetadata,
    ListPage,
    SignedUpload,
    StoredFile,
    UploadBody,
)

_DEFAULT_MULTIPART_THRESHOLD = 8 * 1024 * 1024


class AsyncS3Adapter:
    """Async S3-compatible storage adapter."""

    name: ClassVar[str] = "s3-async"

    def __init__(
        self,
        *,
        bucket: str | None = None,
        region: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        session_token: str | None = None,
        endpoint_url: str | None = None,
        multipart_threshold: int = _DEFAULT_MULTIPART_THRESHOLD,
    ) -> None:
        resolved_bucket = bucket or os.environ.get("AWS_S3_BUCKET")
        if not resolved_bucket:
            raise FilesError(
                code="unauthorized",
                message="AsyncS3Adapter requires bucket= or AWS_S3_BUCKET env var",
                provider=self.name,
            )
        self.bucket = resolved_bucket
        self.multipart_threshold = multipart_threshold
        self._endpoint_url = endpoint_url
        self._session: Any = aioboto3.Session(
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=session_token or os.environ.get("AWS_SESSION_TOKEN"),
            region_name=region
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION"),
        )

    def _client(self):  # type: ignore[no-untyped-def]
        return self._session.client("s3", endpoint_url=self._endpoint_url)

    def _normalize_error(self, op: str, e: ClientError) -> FilesError:
        resp: dict[str, Any] = e.response  # type: ignore[assignment]
        code = resp.get("Error", {}).get("Code", "")
        status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
        if code in ("NoSuchKey", "NoSuchBucket") or status == 404:
            return FilesError(code="not_found", message=str(e), provider=self.name)
        if status in (401, 403) or "AccessDenied" in code or "SignatureDoesNotMatch" in code:
            return FilesError(code="unauthorized", message=str(e), provider=self.name)
        if status == 412:
            return FilesError(code="conflict", message=str(e), provider=self.name)
        return FilesError(code="provider", message=f"{op}: {e}", provider=self.name)

    def _to_body(self, body: UploadBody) -> bytes | io.IOBase:
        if isinstance(body, (bytes, bytearray)):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        if isinstance(body, Path):
            return body.read_bytes()
        return body  # type: ignore[return-value]

    def _meta(self, key: str, resp: dict[str, Any]) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=int(resp.get("ContentLength", 0)),
            etag=(resp.get("ETag") or "").strip('"') or None,
            content_type=resp.get("ContentType"),
            last_modified=resp.get("LastModified") or datetime.now(UTC),
            metadata=dict(resp.get("Metadata") or {}),
        )

    async def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        extra: dict[str, Any] = {}
        if ct := opts.get("content_type"):
            extra["ContentType"] = ct
        if meta := opts.get("metadata"):
            extra["Metadata"] = meta
        if cc := opts.get("cache_control"):
            extra["CacheControl"] = cc
        payload = self._to_body(body)
        async with self._client() as c:
            try:
                if isinstance(payload, (bytes, bytearray)):
                    await c.put_object(Bucket=self.bucket, Key=key, Body=payload, **extra)
                else:
                    await c.upload_fileobj(payload, self.bucket, key, ExtraArgs=extra or None)
            except ClientError as e:
                raise self._normalize_error("upload", e) from e
        return await self.head(key)

    async def download(self, key: str) -> StoredFile:
        async with self._client() as c:
            try:
                resp = await c.get_object(Bucket=self.bucket, Key=key)
                data = await resp["Body"].read()
            except ClientError as e:
                raise self._normalize_error("download", e) from e
        meta = self._meta(key, resp)
        return StoredFile(metadata=meta.model_copy(update={"size": len(data)}), data=data)

    async def stream(self, key: str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]:
        async def gen() -> AsyncIterator[bytes]:
            async with self._client() as c:
                try:
                    resp = await c.get_object(Bucket=self.bucket, Key=key)
                    async for chunk in resp["Body"].iter_chunks(chunk_size=chunk_size):
                        yield chunk
                except ClientError as e:
                    raise self._normalize_error("stream", e) from e

        return gen()

    async def head(self, key: str) -> FileMetadata:
        async with self._client() as c:
            try:
                resp = await c.head_object(Bucket=self.bucket, Key=key)
            except ClientError as e:
                raise self._normalize_error("head", e) from e
        return self._meta(key, resp)

    async def delete(self, key: str) -> None:
        async with self._client() as c:
            try:
                await c.delete_object(Bucket=self.bucket, Key=key)
            except ClientError as e:
                raise self._normalize_error("delete", e) from e

    async def list(
        self,
        *,
        prefix: str | None = None,
        cursor: str | None = None,
        limit: int = 1000,
    ) -> ListPage:
        params: dict[str, Any] = {"Bucket": self.bucket, "MaxKeys": limit}
        if prefix is not None:
            params["Prefix"] = prefix
        if cursor is not None:
            params["ContinuationToken"] = cursor
        async with self._client() as c:
            try:
                resp = await c.list_objects_v2(**params)
            except ClientError as e:
                raise self._normalize_error("list", e) from e
        items = [
            FileMetadata(
                key=obj["Key"],
                size=int(obj.get("Size", 0)),
                etag=(obj.get("ETag") or "").strip('"') or None,
                content_type=None,
                last_modified=obj.get("LastModified") or datetime.now(UTC),
                metadata={},
            )
            for obj in resp.get("Contents", [])
        ]
        next_cursor = resp.get("NextContinuationToken") if resp.get("IsTruncated") else None
        return ListPage(items=items, cursor=next_cursor)

    async def copy(self, src: str, dst: str) -> FileMetadata:
        async with self._client() as c:
            try:
                await c.copy_object(
                    Bucket=self.bucket,
                    Key=dst,
                    CopySource={"Bucket": self.bucket, "Key": src},
                )
            except ClientError as e:
                raise self._normalize_error("copy", e) from e
        return await self.head(dst)

    async def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = self._endpoint_url or f"https://{self.bucket}.s3.amazonaws.com"
            return f"{base.rstrip('/')}/{key}"
        async with self._client() as c:
            return await c.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )

    async def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        method = str(opts.get("method", "put")).lower()
        expires_in = int(opts.get("expires_in", 3600))
        content_type = opts.get("content_type")
        async with self._client() as c:
            if method == "put":
                params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
                if content_type:
                    params["ContentType"] = content_type
                url = await c.generate_presigned_url(
                    "put_object",
                    Params=params,
                    ExpiresIn=expires_in,
                )
                headers = {"Content-Type": content_type} if content_type else {}
                return SignedUpload(
                    url=url,
                    method="PUT",
                    headers=headers,
                    fields=None,
                    expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
                )
            if method == "post":
                conditions: list[Any] = []
                if max_size := opts.get("max_size"):
                    conditions.append(["content-length-range", 0, int(max_size)])
                if content_type:
                    conditions.append({"Content-Type": content_type})
                post = await c.generate_presigned_post(
                    Bucket=self.bucket,
                    Key=key,
                    Conditions=conditions or None,
                    ExpiresIn=expires_in,
                )
                return SignedUpload(
                    url=post["url"],
                    method="POST",
                    headers={},
                    fields=dict(post["fields"]),
                    expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
                )
        raise FilesError(
            code="invalid_input",
            message=f"unknown signed_upload_url method: {method!r}",
            provider=self.name,
        )

    @property
    def raw(self) -> Any:
        return self._session
