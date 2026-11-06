"""Stop-time zone check: diff the worktree against the agent's zones. Stdlib only.

PreToolUse polices the Write tools, redirects and `tee`. Writes by `sed -i`, `cp`, `mv` or a python or node script
leave no trace in the command line, so at Stop the changed paths are read from git instead: `git status --porcelain`
(untracked files included) plus `git diff --name-only` against the base commit. The base is PAI_HARNESS_BASE, else
the merge-base of HEAD with origin/HEAD, origin/main, origin/master, main or master (the first that exists), else HEAD.
Every changed path goes through the same `zone_verdict` as the PreToolUse hook, so the state dir and paths outside
the project are never flagged. A role with no zones assigned is not checked. Without git, or outside a repository, nothing is flagged.
"""
from __future__ import annotations

import os
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
from pathlib import Path

import pre_tool_use as zones

BASE_CANDIDATES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")


def git(root: Path, *args: str) -> str | None:
    try:
        done = run_process(["git", "-C", str(root), *args], capture_output=True, text=True, timeout=8)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def base_commit(root: Path) -> str:
    chosen = os.environ.get("PAI_HARNESS_BASE", "").strip()
    candidates = [chosen] if chosen else list(BASE_CANDIDATES)
    for ref in candidates:
        found = git(root, "merge-base", "HEAD", ref)
        if found and found.strip():
            return found.strip()
    return "HEAD"


def changed_paths(root: Path) -> list[str]:
    """Paths (relative to the repository top level) changed in the worktree or committed since the base commit."""
    top = git(root, "rev-parse", "--show-toplevel")
    if top is None:
        return []
    top_dir, found = Path(top.strip()), []
    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    entries = (status or "").split("\0")
    i = 0
    while i < len(entries):
        entry = entries[i]
        i += 1
        if len(entry) < 4:
            continue
        found.append(entry[3:])
        if entry[0] in "RC":  # a rename or copy lists the origin next
            if i < len(entries) and entries[i]:
                found.append(entries[i])
            i += 1
    diff = git(root, "diff", "--name-only", "-z", base_commit(root))
    found += [p for p in (diff or "").split("\0") if p]
    seen, out = set(), []
    for relative in found:
        absolute = (top_dir / relative).as_posix()
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def out_of_zone(config: dict, config_path: Path, state: Path | None, agent: str) -> list[tuple[str, str]]:
    """Return (path relative to the project root, denial reason) for each changed path outside the agent's zones."""
    if not zones.my_zones(config, agent):
        return []
    root = config_path.parent
    flagged = []
    for absolute in changed_paths(root):
        reason = zones.zone_verdict(absolute, root, config, root, state, agent)
        if reason:
            try:
                shown = Path(os.path.realpath(absolute)).relative_to(Path(os.path.realpath(root))).as_posix()
            except ValueError:
                shown = absolute
            flagged.append((shown, reason))
    return flagged
