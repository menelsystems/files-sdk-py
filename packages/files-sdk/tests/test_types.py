from datetime import UTC, datetime

import pytest
from files_sdk.types import FileMetadata, ListPage, SignedUpload, StoredFile
from pydantic import ValidationError


def _meta() -> FileMetadata:
    return FileMetadata(
        key="a/b.txt",
        size=3,
        etag="abc",
        content_type="text/plain",
        last_modified=datetime(2026, 1, 1, tzinfo=UTC),
        metadata={"k": "v"},
    )


def test_file_metadata_required_fields():
    m = _meta()
    assert m.key == "a/b.txt"
    assert m.size == 3
    assert m.metadata == {"k": "v"}


def test_file_metadata_size_nonnegative():
    with pytest.raises(ValidationError):
        FileMetadata(
            key="x",
            size=-1,
            etag=None,
            content_type=None,
            last_modified=datetime(2026, 1, 1, tzinfo=UTC),
            metadata={},
        )


def test_stored_file_text_decoding():
    sf = StoredFile(metadata=_meta(), data=b"hi!")
    assert sf.text() == "hi!"
    assert sf.as_bytes() == b"hi!"


def test_stored_file_text_custom_encoding():
    sf = StoredFile(metadata=_meta().model_copy(update={"size": 6}), data="héllo".encode())
    assert sf.text(encoding="utf-8") == "héllo"


def test_list_page_terminal_cursor_is_none():
    page = ListPage(items=[_meta()], cursor=None)
    assert page.cursor is None
    assert len(page.items) == 1


def test_signed_upload_method_upper():
    su = SignedUpload(
        url="https://x",
        method="PUT",
        headers={"Content-Type": "text/plain"},
        fields=None,
        expires_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert su.method == "PUT"


def test_signed_upload_post_has_fields():
    su = SignedUpload(
        url="https://x",
        method="POST",
        headers={},
        fields={"key": "a", "policy": "p"},
        expires_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    assert su.fields == {"key": "a", "policy": "p"}
