# files-sdk-digitalocean

[DigitalOcean Spaces](https://www.digitalocean.com/products/spaces) adapter
for [files-sdk](../files-sdk). Spaces is S3-compatible, so this package
subclasses `files-sdk-s3` and points it at the regional endpoint.

```python
from files_sdk import Files
from files_sdk_digitalocean import DigitalOceanAdapter

files = Files(adapter=DigitalOceanAdapter(
    region="nyc3",
    bucket="my-space",
))
```

Reads from `DO_SPACES_REGION`, `DO_SPACES_BUCKET`, `DO_SPACES_KEY`,
`DO_SPACES_SECRET`, `DO_SPACES_PUBLIC_URL_BASE` (optional — defaults to the
bucket-virtual-host endpoint for `url(public=True)`; pass a CDN URL or custom
domain to override).

The async adapter (`AsyncDigitalOceanAdapter`) shares the same configuration.
