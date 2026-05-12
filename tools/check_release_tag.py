"""Validate that a release tag matches the workspace VERSION file.

Tag format: ``v<version>``, e.g. ``v0.1.0a1``. The workspace is versioned in
lockstep — a single tag publishes all first-party packages at the same
version. Both PEP 440 canonical (``v0.1.0a1``) and dash-separated forms
(``v0.1.0-alpha.1``) are accepted; comparison happens after canonicalisation
via packaging.Version.

Exits 0 on match, non-zero with a diagnostic on mismatch.

Usage:
    python tools/check_release_tag.py <tag>
"""

# /// script
# requires-python = ">=3.11"
# dependencies = ["packaging>=24"]
# ///

from __future__ import annotations

import sys
from pathlib import Path

from packaging.version import InvalidVersion, Version

WORKSPACE = Path(__file__).resolve().parent.parent
VERSION_FILE = WORKSPACE / "VERSION"


def parse_tag(tag: str) -> Version:
    if not tag.startswith("v"):
        raise SystemExit(f"tag {tag!r} must start with 'v' (expected v<version>, e.g. v0.1.0a1)")
    raw = tag[1:]
    if not raw:
        raise SystemExit(f"tag {tag!r} has no version after 'v'")
    try:
        return Version(raw)
    except InvalidVersion as e:
        raise SystemExit(f"tag version {raw!r} is not PEP 440-compliant: {e}") from e


def load_workspace_version() -> Version:
    if not VERSION_FILE.exists():
        raise SystemExit(f"no workspace VERSION file at {VERSION_FILE}")
    raw = VERSION_FILE.read_text().strip()
    if not raw:
        raise SystemExit(f"{VERSION_FILE} is empty")
    try:
        return Version(raw)
    except InvalidVersion as e:
        raise SystemExit(f"VERSION file content {raw!r} is not PEP 440-compliant: {e}") from e


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    tag = argv[1]
    tag_version = parse_tag(tag)
    workspace_version = load_workspace_version()
    if tag_version != workspace_version:
        print(
            f"version mismatch:\n"
            f"  tag:        {tag} → {tag_version}\n"
            f"  VERSION:    {workspace_version}\n"
            f"fix: bump VERSION to {tag_version!s} before tagging, or re-tag to match.",
            file=sys.stderr,
        )
        return 1
    print(f"ok: workspace VERSION {workspace_version} matches tag {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
