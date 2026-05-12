# Releasing

Tag-driven, OIDC-based publishing. No API tokens stored anywhere.

## One-time PyPI setup (per package)

For each package you intend to publish (`files-sdk`, `files-sdk-s3`, `files-sdk-r2`, `files-sdk-local`):

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Click **Add a new pending publisher** (the project doesn't exist on PyPI yet on a first release).
3. Fill in:
   - **PyPI project name**: `files-sdk`, `files-sdk-s3`, etc.
   - **Owner**: your GitHub username or org (e.g. `menelsystems`)
   - **Repository name**: `files-sdk-py`
   - **Workflow name**: `release.yml`
   - **Environment**: *(leave blank for now; add later if you want manual approval gates)*
4. Save. PyPI now trusts the OIDC token issued by `release.yml` for this project name.

The first successful publish creates the real project on PyPI; the pending publisher converts to a normal one automatically.

## Releasing a package

1. **Bump the version** in `packages/<pkg>/pyproject.toml`:
   ```toml
   version = "0.1.0a1"
   ```
   Must be PEP 440-compliant. Pre-release suffixes: `a1` (alpha), `b1` (beta), `rc1` (release candidate). Post-release: `.post1`. Dev: `.dev1`.

2. **Update `CHANGELOG.md`**: move entries from `[Unreleased]` under a new dated heading `## [<version>] - YYYY-MM-DD`. Leave `[Unreleased]` as an empty placeholder for the next round.

3. **Commit and tag**:
   ```sh
   git commit -am "release: <pkg> <version>"
   git tag <pkg>-v<version>      # e.g. files-sdk-s3-v0.1.0a1
   git push origin main --tags
   ```

4. **Watch the release workflow**: <https://github.com/menelsystems/files-sdk-py/actions/workflows/release.yml>. It will:
   - validate the tag's version against the pyproject version
   - build wheel + sdist
   - verify LICENSE is bundled
   - publish to PyPI via Trusted Publishing
   - create a matching GitHub release with artifacts attached

5. **Verify install**:
   ```sh
   uv add <pkg>==<version>
   ```
   from a scratch directory.

## Dry-run before a real release

Trigger the workflow manually with `dry_run: true` to build + validate without publishing:

```sh
gh workflow run release.yml \
  -f package=files-sdk-s3 \
  -f version=0.1.0a1 \
  -f dry_run=true
```

The workflow runs the version check + build + LICENSE verification, then stops before the publish step.

## Cascade order on first publish

Each package gets tagged independently, but downstream packages can't resolve their PyPI deps until their upstreams are published. Recommended order for first release:

1. `files-sdk` (core — has the `Adapter`/`AsyncAdapter` Protocols everything else imports)
2. `files-sdk-s3` and `files-sdk-local` (independent of each other, parallel OK)
3. `files-sdk-r2` (depends on `files-sdk-s3` via PyPI metadata)

After all four have a first release, subsequent tag pushes can happen in any order — each release is self-contained.

## Pre-release versions

`0.1.0a1`, `0.1.0a2`, … → `0.1.0b1`, `0.1.0b2`, … → `0.1.0rc1`, … → `0.1.0`. PyPI treats pre-releases as installable only with `--pre` (or explicit version pin), so they don't surprise users who run `uv add files-sdk`.

## Rolling back

You can't unpublish a version (PyPI policy). If a release is broken:

1. Yank it on PyPI (project page → "Manage" → "Yank release"). Yanked versions still resolve for exact pins but won't be picked up by `uv add <pkg>` without a pin.
2. Bump version (`0.1.0a1` → `0.1.0a2`) and re-tag.

## Common failures

- **"InvalidVersion"** from the validator: your tag isn't PEP 440-compliant. Use `0.1.0a1` (canonical) or `0.1.0-alpha.1` (accepted). Avoid spaces, leading `v`, etc.
- **"mismatch for package …"** from the validator: tag version doesn't match `pyproject.toml`. Either bump the pyproject and re-commit, or move the tag.
- **"Trusted publisher not configured"** from the publish step: the per-package pending publisher hasn't been set up on PyPI yet (or doesn't match owner/repo/workflow). See "One-time PyPI setup" above.
- **Pre-release ignored by `uv add`**: pre-release versions are skipped unless explicitly requested. Install with `uv add <pkg>==<version>` or `uv add --prerelease=allow <pkg>`.
