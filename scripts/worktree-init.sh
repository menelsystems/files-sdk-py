#!/usr/bin/env bash
# SessionStart hook: bootstrap a fresh worktree's Python environment.
#
# `.worktreeinclude` copies gitignored files (`.secrets`) into new worktrees,
# but it does not initialize the environment. This hook builds `.venv` on the
# first session in a worktree that doesn't have one yet. It is a no-op in the
# main checkout and in any worktree that is already synced, so it's cheap to
# run on every session start.
#
# Wired via .claude/settings.json -> hooks.SessionStart.
set -euo pipefail

# CLAUDE_PROJECT_DIR is set by Claude Code to the session's project root.
# Fall back to this script's repo root when run manually.
project_dir="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Already initialized — nothing to do. Keep this fast; SessionStart runs often.
if [ -d "$project_dir/.venv" ]; then
  exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "worktree-init: uv not found on PATH — skipping .venv bootstrap" >&2
  exit 0
fi

# All output goes to stderr: a SessionStart hook's stdout is injected into the
# session as context, and uv's progress chatter has no business being there.
echo "worktree-init: no .venv in $project_dir — running uv sync" >&2
if uv sync --all-packages --directory "$project_dir" >&2; then
  echo "worktree-init: .venv ready" >&2
else
  # Don't brick the session over a sync failure; surface it and move on.
  echo "worktree-init: uv sync failed — run 'uv sync --all-packages' manually" >&2
fi
exit 0
