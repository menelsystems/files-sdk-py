# packages/files-sdk-s3

Amazon S3 adapter. Ships both sync (`S3Adapter` / boto3) and async (`AsyncS3Adapter` / aioboto3).

## File map

```
src/files_sdk_s3/
  adapter.py        # S3Adapter (sync)
  async_adapter.py  # AsyncS3Adapter
  __init__.py       # re-exports both classes
tests/
  conftest.py       # moto ThreadedMotoServer fixtures
  test_conformance.py
  test_async_conformance.py
  test_s3_specific.py
```

## moto setup — important

Tests use `moto.server.ThreadedMotoServer` (a real HTTP server on a random port), NOT
the `mock_aws()` decorator. The botocore stubber path does not work with aiobotocore 2.x.
Both boto3 and aioboto3 clients point to `endpoint_url=moto_endpoint` — zero monkey-patching.

```python
# conftest.py pattern
server = ThreadedMotoServer(port=0)
server.start()
host, port = server.get_host_and_port()
yield f"http://{host}:{port}"
```

## Error translation

`_wrap(op, fn, *args, **kw)` in `adapter.py:68` is the single choke point. Every boto3
call routes through it. Mapping:

| botocore signal | FilesError code |
|---|---|
| `NoSuchKey`, `NoSuchBucket`, HTTP 404 | `not_found` |
| HTTP 401/403, `AccessDenied`, `SignatureDoesNotMatch` | `unauthorized` |
| HTTP 412 | `conflict` |
| anything else | `provider` |

`AsyncS3Adapter` has an equivalent `_wrap` as an async method.

## Multipart uploads

`multipart_threshold` (default 8 MiB) flows into `boto3.s3.transfer.TransferConfig`.
Only the file-like upload path uses it (`upload_fileobj`); byte payloads use `put_object` directly.

## Entry points

```toml
[project.entry-points."files_sdk.adapters"]
s3 = "files_sdk_s3:S3Adapter"
"s3-async" = "files_sdk_s3:AsyncS3Adapter"
```

## Integration tests

Workspace-level `tests/integration/` contains `test_s3_integration.py` and
`test_multipart.py`. They run only when `FILES_SDK_INTEGRATION_ENDPOINT` is set
(pointing at a live rustfs or real S3 endpoint).
