# Releasing

Lockstep monorepo release: a single tag `v<version>` publishes **all** first-party packages at the same version. Per-package version skew is structurally prevented — every pyproject reads `version` from the shared `VERSION` file at the repo root via hatchling's dynamic-version source.

## One-time PyPI setup (per package)

For each package: `files-sdk`, `files-sdk-s3`, `files-sdk-r2`, `files-sdk-local`.

1. Go to <https://pypi.org/manage/account/publishing/>.
2. **Add a new pending publisher** (the project doesn't exist on PyPI yet on a first release).
3. Fill in:
   - **PyPI project name**: e.g. `files-sdk`, `files-sdk-s3`
   - **Owner**: your GitHub username or org (e.g. `menelsystems`)
   - **Repository name**: `files-sdk-py`
   - **Workflow name**: `release.yml`
   - **Environment**: *leave blank for now; add later if you want manual approval gates*
4. Save. The first successful publish creates the real project on PyPI and converts the pending publisher into a normal one automatically.

## One-time tag protection (immutable tags)

Tags are git's release receipts; force-pushing one rewrites history under the same name. Lock that down:

1. <https://github.com/menelsystems/files-sdk-py/settings/tag_protection>
2. **New rule**, pattern: `v*` (matches every release tag).
3. Save. Only admins can override; collaborators can't force-push or delete a release tag.

Workflow defense-in-depth: `gh release create --verify-tag` (already wired) ensures the GitHub Release matches the underlying tag SHA at create time.

## Releasing

1. **Bump `VERSION`** at the repo root:
   ```sh
   echo "0.1.0a1" > VERSION
   ```
   Must be PEP 440-compliant. Pre-release suffixes: `a1` (alpha), `b1` (beta), `rc1`. Post: `.post1`. Dev: `.dev1`.

2. **Update `CHANGELOG.md`**: move entries from `[Unreleased]` under a new dated heading `## [<version>] - YYYY-MM-DD`. Leave `[Unreleased]` empty for the next round.

3. **Commit and tag**:
   ```sh
   git commit -am "release: v0.1.0a1"
   git tag v0.1.0a1
   git push origin main --tags
   ```

4. **Watch**: <https://github.com/menelsystems/files-sdk-py/actions/workflows/release.yml>. The workflow will:
   - validate the tag matches `VERSION`
   - build wheel + sdist for all 4 packages
   - verify LICENSE is bundled in each
   - record GitHub artifact attestation (SLSA Build L3 provenance to Sigstore)
   - publish each package to PyPI via Trusted Publishing (PEP 740 attestation on each)
   - create a GitHub Release with all 8 artifacts attached

5. **Verify install**:
   ```sh
   uv add files-sdk-s3==0.1.0a1   # or any of the four packages
   ```
   from a scratch directory.

## Dry-run before a real release

Trigger the workflow manually with `dry_run: true` to build + validate + attest without publishing:

```sh
gh workflow run release.yml \
  -f version=0.1.0a1 \
  -f dry_run=true
```

The workflow runs the version check + build + LICENSE verification + GitHub attestation, then stops before the PyPI publish steps.

## Publish order

The workflow publishes in dependency order so downstream installs resolve cleanly during the brief publishing window:

1. `files-sdk` (core — everyone imports `Adapter` / `AsyncAdapter`)
2. `files-sdk-s3`, `files-sdk-local` (independent; sequential here, but order doesn't matter between them)
3. `files-sdk-r2` (depends on `files-sdk-s3` on PyPI)

This only matters for `uv add` calls in the seconds between publish-step-1 and publish-step-4 on the **first** release. Subsequent releases are no-ops dep-wise.

## Pre-release versions

`0.1.0a1`, `0.1.0a2`, … → `0.1.0b1`, … → `0.1.0rc1`, … → `0.1.0`. PyPI treats pre-releases as installable only with `--pre` or an exact pin, so they don't surprise users running `uv add files-sdk`.

## Rolling back

You can't unpublish a version (PyPI policy). If a release is broken:

1. **Yank** it on PyPI (project page → "Manage" → "Yank release"). Yanked versions still resolve for exact pins but won't be picked by `uv add <pkg>` without one.
2. **Bump** `VERSION` (`0.1.0a1` → `0.1.0a2`), commit, re-tag, push. Tag protection prevents force-replacing the bad tag — that's the point.

## Provenance and attestations

Every release artifact has two independent provenance trails, both rooted in Sigstore:

- **GitHub Artifact Attestation** (SLSA Build L3) — signed by GitHub's OIDC identity for `release.yml`. Verifiable via `gh attestation verify <wheel> --owner menelsystems`.
- **PyPI PEP 740 Attestation** — signed by the same OIDC token via the trusted-publishing action. Shown in the PyPI sidebar.

If you ever need to prove a wheel came from this repo at a specific commit, either trail does it.

## Common failures

- **"InvalidVersion"** from the validator: tag isn't PEP 440-compliant. Use `v0.1.0a1` (canonical) or `v0.1.0-alpha.1` (accepted).
- **"version mismatch"** from the validator: `VERSION` doesn't match the tag's version. Either bump `VERSION` and re-commit, or move the tag.
- **"Trusted publisher not configured"** from the publish step: the per-package pending publisher hasn't been set up on PyPI yet. See "One-time PyPI setup" above.
- **Pre-release ignored by `uv add`**: pre-release versions need an explicit pin (`==0.1.0a1`) or `--prerelease=allow`.
