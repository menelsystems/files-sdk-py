# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

Each package in this workspace is versioned independently, but changes are
recorded here against the workspace as a whole until first publish. Once
published, per-package changelogs may be split out.

## [Unreleased]

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
