# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Each package in this workspace is versioned independently, but changes are
recorded here against the workspace as a whole until first publish. Once
published, per-package changelogs may be split out.

## [Unreleased]

## [0.1.0a2] - 2026-05-14

### Added

- `files-sdk-uploadthing` adapter (#25): sync + async classes mapping the
  adapter key to UploadThing's `customId`, with locally-computed HMAC-SHA256
  presigned URLs (no UT-side roundtrip) and a CDN-via-API fallback for
  non-ASCII keys. 77/77 conformance (14 sync live + 14 async live + 35
  offline). Migrated to lockstep VERSION + LICENSE-bundled + OIDC publish
  wiring alongside the tier-1 batch (#29 — was merged before the release
  pipeline scaled out).
- Tier-1 S3-compatible adapters (closes #21, #22, #23, #24): `files-sdk-minio`,
  `files-sdk-digitalocean`, `files-sdk-hetzner`, `files-sdk-storj`. Each ships
  sync + async classes that subclass the S3 adapter, expose provider env-var
  resolution, and reuse the shared moto-backed conformance suite. Drops the
  stub-package count from 14 to 10 (post-#25).
- `files-sdk-linode` adapter for Linode Object Storage (Akamai-owned,
  S3-compatible). Same subclassing pattern. The `files-sdk-akamai` stub for
  the original NetStorage HTTP API + HMAC-SHA256 issue (#20) remains
  unimplemented and is **not** closed by #26 — NetStorage is a different
  protocol and warrants its own package.

### Changed

- Release pipeline: reverted the temporary account-scoped api-token auth used
  for the a1 emergency release back to PyPI Trusted Publishing (OIDC) + PEP 740
  attestations (#9), then scaled the build/verify/publish wiring to all 10
  first-party packages (#26, #29).
- READMEs showcase sync + async as first-class: side-by-side quickstarts, a
  sync↔async pair table, and contrasting streaming examples (#27).

## [0.1.0a1] - 2026-05-12

### Added

- `files-sdk` core package: `FilesError` with code enum, pydantic types
  (metadata, stored file, list page), `Adapter` and `AsyncAdapter` Protocols,
  entry-point-based adapter registry, and sync/async `Files`/`AsyncFiles`
  clients with `from_name` sugar.
- Conformance test suite for adapters, expanded async coverage from 4 to 14
  paths, and a shared testing harness for adapter authors.
- `files-sdk-s3` adapter: sync `S3Adapter` and `AsyncS3Adapter`, multipart
  threshold plumbed through `TransferConfig`, real-AWS-S3 integration job, and
  a 19-test conformance suite.
- `files-sdk-r2` adapter: `R2Adapter` and `AsyncR2Adapter` subclassing the S3
  adapter, with a real-Cloudflare-R2 integration job and act-friendly secrets
  template.
- `files-sdk-local` pure-stdlib filesystem adapter for dev/test.
- 15 stub adapter packages scaffolded from a shared adapter template.
- rustfs-backed integration suite covering multipart uploads.
- Workspace README, per-package READMEs, AGENTS.md at root and each
  first-party package, design spec and v0 implementation plan, PEP 723
  inline-deps example in quickstart, and a Protocol-conformance tripwire in
  each adapter package's `__init__`.

### Changed

- Replaced aiobotocore monkey-patches in `files-sdk-s3` tests with
  `ThreadedMotoServer`.
- Dropped unneeded `arbitrary_types_allowed` in core; default options
  reorganised.
- Quickstart docs now lead with `uv`.

### Fixed

- `AsyncAdapter.stream()` no longer requires a double await — matches the
  documented Protocol (breaking change for any caller that worked around the
  old behaviour).
- CI rustfs healthcheck no longer uses `curl -f` (rustfs returns 403 on bare
  `GET /`, which is fine).
