"""Synchronous S3 adapter."""

from __future__ import annotations

import os
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import IO, Any, ClassVar

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from files_sdk.errors import FilesError
from files_sdk.types import (
    FileMetadata,
    ListPage,
    SignedUpload,
    StoredFile,
    UploadBody,
)

_DEFAULT_MULTIPART_THRESHOLD = 8 * 1024 * 1024  # 8 MiB


class S3Adapter:
    """Synchronous S3-compatible storage adapter."""

    name: ClassVar[str] = "s3"

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
                message="S3Adapter requires bucket= or AWS_S3_BUCKET env var",
                provider=self.name,
            )
        self.bucket = resolved_bucket
        self.multipart_threshold = multipart_threshold
        self._endpoint_url = endpoint_url
        self._client: Any = boto3.client(  # type: ignore[no-untyped-call]
            "s3",
            region_name=region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION"),
            aws_access_key_id=access_key_id or os.environ.get("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=session_token or os.environ.get("AWS_SESSION_TOKEN"),
            endpoint_url=endpoint_url,
            config=Config(signature_version="s3v4"),
        )

    # ---- normalization helpers ----------------------------------------------

    def _wrap(self, op: str, fn: Any, *args: Any, **kw: Any) -> Any:
        try:
            return fn(*args, **kw)
        except ClientError as e:
            resp: dict[str, Any] = e.response  # type: ignore[assignment]
            code = resp.get("Error", {}).get("Code", "")
            status = resp.get("ResponseMetadata", {}).get("HTTPStatusCode", 0)
            if code in ("NoSuchKey", "NoSuchBucket") or status == 404:
                raise FilesError(code="not_found", message=str(e), provider=self.name) from e
            if status in (401, 403) or "AccessDenied" in code or "SignatureDoesNotMatch" in code:
                raise FilesError(code="unauthorized", message=str(e), provider=self.name) from e
            if status == 412:
                raise FilesError(code="conflict", message=str(e), provider=self.name) from e
            raise FilesError(code="provider", message=f"{op}: {e}", provider=self.name) from e

    def _to_body(self, body: UploadBody) -> bytes | IO[bytes]:
        if isinstance(body, (bytes, bytearray)):
            return bytes(body)
        if isinstance(body, str):
            return body.encode("utf-8")
        if isinstance(body, Path):
            return body.read_bytes()
        return body  # file-like

    def _meta_from_head(self, key: str, resp: dict[str, Any]) -> FileMetadata:
        return FileMetadata(
            key=key,
            size=int(resp.get("ContentLength", 0)),
            etag=(resp.get("ETag") or "").strip('"') or None,
            content_type=resp.get("ContentType"),
            last_modified=resp.get("LastModified") or datetime.now(timezone.utc),
            metadata=dict(resp.get("Metadata") or {}),
        )

    # ---- public API ---------------------------------------------------------

    def upload(self, key: str, body: UploadBody, **opts: Any) -> FileMetadata:
        extra: dict[str, Any] = {}
        if ct := opts.get("content_type"):
            extra["ContentType"] = ct
        if meta := opts.get("metadata"):
            extra["Metadata"] = meta
        if cc := opts.get("cache_control"):
            extra["CacheControl"] = cc
        payload = self._to_body(body)
        if isinstance(payload, (bytes, bytearray)):
            self._wrap(
                "upload",
                self._client.put_object,
                Bucket=self.bucket, Key=key, Body=payload, **extra,
            )
        else:
            self._wrap(
                "upload",
                self._client.upload_fileobj,
                payload, self.bucket, key, ExtraArgs=extra or None,
            )
        return self.head(key)

    def download(self, key: str) -> StoredFile:
        resp = self._wrap(
            "download", self._client.get_object, Bucket=self.bucket, Key=key,
        )
        data = resp["Body"].read()
        meta = self._meta_from_head(key, resp)
        # ContentLength in get_object may not reflect actual bytes streamed
        return StoredFile(metadata=meta.model_copy(update={"size": len(data)}), data=data)

    def stream(self, key: str, *, chunk_size: int = 65536) -> Iterator[bytes]:
        resp = self._wrap(
            "stream", self._client.get_object, Bucket=self.bucket, Key=key,
        )
        body = resp["Body"]
        try:
            while True:
                chunk = body.read(chunk_size)
                if not chunk:
                    return
                yield chunk
        finally:
            body.close()

    def head(self, key: str) -> FileMetadata:
        resp = self._wrap(
            "head", self._client.head_object, Bucket=self.bucket, Key=key,
        )
        return self._meta_from_head(key, resp)

    def delete(self, key: str) -> None:
        # S3 delete_object is idempotent and does not 404 on missing keys
        self._wrap(
            "delete", self._client.delete_object, Bucket=self.bucket, Key=key,
        )

    def list(
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
        resp = self._wrap("list", self._client.list_objects_v2, **params)
        items = [
            FileMetadata(
                key=obj["Key"],
                size=int(obj.get("Size", 0)),
                etag=(obj.get("ETag") or "").strip('"') or None,
                content_type=None,
                last_modified=obj.get("LastModified") or datetime.now(timezone.utc),
                metadata={},
            )
            for obj in resp.get("Contents", [])
        ]
        next_cursor = resp.get("NextContinuationToken") if resp.get("IsTruncated") else None
        return ListPage(items=items, cursor=next_cursor)

    def copy(self, src: str, dst: str) -> FileMetadata:
        self._wrap(
            "copy",
            self._client.copy_object,
            Bucket=self.bucket,
            Key=dst,
            CopySource={"Bucket": self.bucket, "Key": src},
        )
        return self.head(dst)

    def url(self, key: str, *, expires_in: int = 3600, public: bool = False) -> str:
        if public:
            base = self._endpoint_url or f"https://{self.bucket}.s3.amazonaws.com"
            return f"{base.rstrip('/')}/{key}"
        return self._wrap(  # type: ignore[no-any-return]
            "url",
            self._client.generate_presigned_url,
            ClientMethod="get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    def signed_upload_url(self, key: str, **opts: Any) -> SignedUpload:
        method = str(opts.get("method", "put")).lower()
        expires_in = int(opts.get("expires_in", 3600))
        content_type = opts.get("content_type")
        if method == "put":
            params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
            if content_type:
                params["ContentType"] = content_type
            url = self._wrap(
                "signed_upload_url",
                self._client.generate_presigned_url,
                ClientMethod="put_object",
                Params=params,
                ExpiresIn=expires_in,
            )
            headers = {"Content-Type": content_type} if content_type else {}
            return SignedUpload(
                url=url, method="PUT", headers=headers, fields=None,
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        if method == "post":
            conditions: list[Any] = []
            if max_size := opts.get("max_size"):
                conditions.append(["content-length-range", 0, int(max_size)])
            if content_type:
                conditions.append({"Content-Type": content_type})
            post = self._wrap(
                "signed_upload_url",
                self._client.generate_presigned_post,
                Bucket=self.bucket, Key=key, Conditions=conditions or None,
                ExpiresIn=expires_in,
            )
            return SignedUpload(
                url=post["url"], method="POST", headers={}, fields=dict(post["fields"]),
                expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            )
        raise FilesError(
            code="invalid_input",
            message=f"unknown signed_upload_url method: {method!r}",
            provider=self.name,
        )

    @property
    def raw(self) -> Any:
        return self._client
