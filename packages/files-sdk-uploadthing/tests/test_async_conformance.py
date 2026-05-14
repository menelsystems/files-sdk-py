"""Async conformance suite against AsyncUploadThingAdapter."""

from files_sdk.testing.conformance import (  # noqa: F401
    test_async_copy_creates_destination,
    test_async_delete_idempotent,
    test_async_download_missing_raises_not_found,
    test_async_head_returns_metadata,
    test_async_list_pagination_cursor,
    test_async_list_prefix_filters,
    test_async_signed_upload_url_put,
    test_async_stream_yields_chunks,
    test_async_unicode_key_roundtrip,
    test_async_upload_from_file_like,
    test_async_upload_then_download_bytes,
    test_async_upload_then_download_str,
    test_async_url_returns_http_string,
    test_async_zero_byte_upload,
)
