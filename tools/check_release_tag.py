"""Validate that a release tag matches its package's pyproject version.

Tag format: ``<package-name>-v<version>``, e.g. ``files-sdk-s3-v0.1.0a1``.
The version segment is everything after the final ``-v``. Both PEP 440
canonical (``0.1.0a1``) and dash-separated forms (``0.1.0-alpha.1``) are
accepted; comparison happens after canonicalization via packaging.Version.

Exits 0 on match, non-zero with a diagnostic on mismatch.

Usage:
    python tools/check_release_tag.py <tag>
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging>=24", "tomli;python_version<'3.11'"]
# ///

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from packaging.version import InvalidVersion, Version

WORKSPACE = Path(__file__).resolve().parent.parent


def parse_tag(tag: str) -> tuple[str, Version]:
    """Split ``files-sdk-s3-v0.1.0a1`` → (``files-sdk-s3``, Version('0.1.0a1'))."""
    marker = "-v"
    idx = tag.rfind(marker)
    if idx == -1:
        raise SystemExit(f"tag {tag!r} missing '-v' separator (expected <pkg>-v<version>)")
    pkg = tag[:idx]
    raw_version = tag[idx + len(marker) :]
    if not pkg or not raw_version:
        raise SystemExit(f"tag {tag!r} malformed; expected <pkg>-v<version>")
    try:
        version = Version(raw_version)
    except InvalidVersion as e:
        raise SystemExit(f"tag version {raw_version!r} is not PEP 440-compliant: {e}") from e
    return pkg, version


def load_pyproject_version(pkg: str) -> Version:
    path = WORKSPACE / "packages" / pkg / "pyproject.toml"
    if not path.exists():
        raise SystemExit(f"no package directory: {path}")
    with path.open("rb") as f:
        data = tomllib.load(f)
    raw = data.get("project", {}).get("version")
    if not raw:
        raise SystemExit(f"{path} missing [project].version")
    try:
        return Version(raw)
    except InvalidVersion as e:
        raise SystemExit(f"{path} version {raw!r} is not PEP 440-compliant: {e}") from e


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    tag = argv[1]
    pkg, tag_version = parse_tag(tag)
    pyproject_version = load_pyproject_version(pkg)
    if tag_version != pyproject_version:
        print(
            f"mismatch for package {pkg!r}:\n"
            f"  tag:       {tag} → {tag_version}\n"
            f"  pyproject: {pyproject_version}\n"
            f"fix: bump packages/{pkg}/pyproject.toml `version = ...` to {tag_version!s} "
            f"before tagging, or re-tag to match the pyproject version.",
            file=sys.stderr,
        )
        return 1
    print(f"ok: {pkg} {pyproject_version} matches tag")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
