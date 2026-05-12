# Adapter Template

This directory is **not** a uv workspace member. It exists as a reference for
contributors building new adapter packages. To start a new adapter:

1. Copy this directory to `packages/files-sdk-<provider>/`
2. Rename `src/files_sdk_PROVIDER/` to `src/files_sdk_<provider>/`
3. Substitute `<PROVIDER>`/`<provider>` placeholders in every `.tmpl` file
4. Rename `*.tmpl` files (drop the suffix)
5. Update `packages/files-sdk-<provider>/CLAIM.md` with your name
6. Implement the methods in `adapter.py` — see `packages/files-sdk-s3` for a
   reference. Run the shared conformance suite by adding `tests/conftest.py`
   with an `adapter` fixture and `tests/test_conformance.py` importing from
   `files_sdk.testing.conformance`.
