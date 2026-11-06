"""Stop-time zone check: diff the worktree against the agent's zones. Stdlib only.

PreToolUse polices the Write tools, redirects and `tee`. Writes by `sed -i`, `cp`, `mv` or a python or node script
leave no trace in the command line, so at Stop the changed paths are read from git instead: `git status --porcelain`
(untracked files included) plus `git diff --name-only` against the base commit. The base is PAI_HARNESS_BASE, else
the merge-base of HEAD with the config's [project] base_branch (origin/ form first), then origin/HEAD, origin/main, origin/master, main or master (the first that exists), else HEAD.
Every changed path goes through the same `zone_verdict` as the PreToolUse hook, so the state dir and paths outside
the project are never flagged. A role with no zones assigned is not checked. Without git, or outside a repository, nothing is flagged.
"""
from __future__ import annotations

import os
from pathlib import Path

import pre_tool_use as zones

BASE_CANDIDATES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")


def git(root: Path, *args: str) -> str | None:
    return zones.common.git(root, *args)


def base_commit(root: Path, base_branch: str = "") -> str:
    chosen = os.environ.get("PAI_HARNESS_BASE", "").strip()
    configured = [f"origin/{base_branch}", base_branch] if base_branch else []
    candidates = [chosen] if chosen else [*configured, *BASE_CANDIDATES]
    for ref in candidates:
        found = git(root, "merge-base", "HEAD", ref)
        if found and found.strip():
            return found.strip()
    return "HEAD"


def changed_paths(root: Path, base_branch: str = "") -> list[str]:
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
    diff = git(root, "diff", "--name-only", "-z", base_commit(root, base_branch))
    found += [p for p in (diff or "").split("\0") if p]
    seen, out = set(), []
    for relative in found:
        absolute = (top_dir / relative).as_posix()
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out


def out_of_zone(config: dict, config_path: Path, state: Path | None, agent: str, cwd: Path | None = None) -> list[tuple[str, str]]:
    """Return (path relative to its zone root, denial reason) for each changed path outside the agent's zones.

    Every zone root is diffed: the checkout the agent works in and the config's own checkout when they differ, because shell
    writes (sed -i, cp, mv) can reach either. A path that lies inside a more specific root (a nested worktree seen from the
    config checkout) is judged under that root only. If cwd is outside the config's directory and not in a git work tree no
    root can be derived, so the stop is flagged (fail closed)."""
    if not zones.my_zones(config, agent):
        return []
    cwd = cwd or Path.cwd()
    roots = zones.zone_roots(config_path.parent, cwd)
    if not roots:
        return [(str(cwd), f"Write zone: the working directory {cwd} is outside the harness config's directory and is not a git work tree, "
                           "so the zone diff cannot be checked. Ask your lead.")]
    flagged, seen = [], set()
    for root in roots:
        for absolute in changed_paths(root, config.get("project", {}).get("base_branch", "")):
            if absolute in seen or zones.zone_root_for(Path(absolute), roots) != root:
                continue
            seen.add(absolute)
            reason = zones.zone_verdict(absolute, root, config, root, state, agent)
            if reason:
                try:
                    shown = Path(os.path.realpath(absolute)).relative_to(Path(os.path.realpath(root))).as_posix()
                except ValueError:
                    shown = absolute
                flagged.append((shown, reason))
    return flagged
