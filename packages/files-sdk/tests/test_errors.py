import pytest
from files_sdk.errors import FilesError, ErrorCode


def test_files_error_holds_code_and_message():
    err = FilesError(code="not_found", message="missing")
    assert err.code == "not_found"
    assert err.message == "missing"
    assert str(err) == "missing"


def test_files_error_optional_provider():
    err = FilesError(code="provider", message="boom", provider="s3")
    assert err.provider == "s3"


def test_files_error_preserves_cause():
    original = ValueError("oops")
    try:
        try:
            raise original
        except ValueError as e:
            raise FilesError(code="provider", message="wrapped") from e
    except FilesError as wrapped:
        assert wrapped.__cause__ is original


def test_files_error_rejects_invalid_code():
    with pytest.raises(ValueError):
        FilesError(code="totally_made_up", message="x")  # type: ignore[arg-type]


def test_error_code_literal_values():
    expected = {"not_found", "unauthorized", "conflict", "provider", "invalid_input"}
    # ErrorCode is a Literal alias; validate the set defined as VALID_CODES
    from files_sdk.errors import VALID_CODES
    assert VALID_CODES == expected
