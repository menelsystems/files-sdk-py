"""Smoke tests for the Claude Code worktree bootstrap wiring.

Covers the static contract — `.worktreeinclude`, `.claude/settings.json`, and
the `scripts/worktree-init.sh` hook — plus the hook's idempotency guard. The
actual `uv sync` in a fresh worktree is left to manual verification; spinning a
real worktree and syncing it is too slow and heavy for the unit suite.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
HOOK_SCRIPT = REPO_ROOT / "scripts" / "worktree-init.sh"


def test_worktreeinclude_lists_secrets() -> None:
    worktreeinclude = REPO_ROOT / ".worktreeinclude"
    assert worktreeinclude.is_file(), ".worktreeinclude missing from repo root"
    patterns = [
        line.strip()
        for line in worktreeinclude.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]
    assert ".secrets" in patterns


def test_secrets_is_gitignored() -> None:
    # .worktreeinclude only copies files that are ALSO gitignored, so this is a
    # precondition for `.secrets` actually landing in new worktrees.
    result = subprocess.run(
        ["git", "check-ignore", ".secrets"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, ".secrets must be gitignored for .worktreeinclude to copy it"


def test_worktrees_dir_is_gitignored() -> None:
    # Probe a path *under* the dir: a trailing-slash pattern only matches a path
    # git can confirm is a directory, and `.claude/` does not exist in a fresh
    # worktree checkout. A child path matches the pattern unconditionally.
    result = subprocess.run(
        ["git", "check-ignore", ".claude/worktrees/probe"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, ".claude/worktrees/ should be gitignored"


def test_hook_script_is_valid_and_executable() -> None:
    assert HOOK_SCRIPT.is_file(), "scripts/worktree-init.sh missing"
    assert os.access(HOOK_SCRIPT, os.X_OK), "scripts/worktree-init.sh must be executable"
    syntax = subprocess.run(["bash", "-n", str(HOOK_SCRIPT)], capture_output=True, text=True)
    assert syntax.returncode == 0, syntax.stderr


def test_settings_wires_sessionstart_to_hook() -> None:
    settings = json.loads((REPO_ROOT / ".claude" / "settings.json").read_text())
    commands = [
        hook["command"] for group in settings["hooks"]["SessionStart"] for hook in group["hooks"]
    ]
    assert any("worktree-init.sh" in command for command in commands)


def test_hook_is_noop_when_venv_exists(tmp_path: Path) -> None:
    # When the project dir already has a .venv, the hook must short-circuit to
    # exit 0 without touching uv and without emitting anything on stdout (which
    # SessionStart would otherwise inject into the session as context).
    (tmp_path / ".venv").mkdir()
    result = subprocess.run(
        [str(HOOK_SCRIPT)],
        env={**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert result.stdout == ""
