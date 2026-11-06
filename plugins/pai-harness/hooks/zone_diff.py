"""Stop-time zone check: diff the worktree against the agent's zones. Stdlib only.

PreToolUse polices the Write tools, redirects and `tee`. Writes by `sed -i`, `cp`, `mv` or a python or node script
leave no trace in the command line, so at Stop the changed paths are read from git instead: `git status --porcelain`
(untracked files included) plus `git diff --name-only` against the base commit. The base is PAI_HARNESS_BASE, else
the merge-base of HEAD with the config's [project] base_branch (origin/ form first), then origin/HEAD, origin/main, origin/master, main or master (the first that exists).
Every changed path goes through the same `zone_verdict` as the PreToolUse hook, so the state dir and paths outside
the project are never flagged. A role with no zones assigned is not checked. A directory that is in no repository at all is not
flagged. Fail closed: when git fails or times out for a root inside a repository, or no base commit can be found, or a changed
path sits in a directory that resolves outside its root, that is reported as "cannot be checked" with the reason, and Stop blocks.
A changed symlink is judged by its own path, not by where it points. Stop does not lift this block after 3 tries (stop.py): an
unreadable diff must not turn into an allowed stop. Only the roots of zone_roots are diffed; a shell write into another
worktree of the repository is not seen (PreToolUse covers the Write tools and redirects there).
"""
from __future__ import annotations

import os
from pathlib import Path

import pre_tool_use as zones

UNCHECKED = "cannot be checked"
BASE_CANDIDATES = ("origin/HEAD", "origin/main", "origin/master", "main", "master")


def is_unchecked(reason: str) -> bool:
    """True for a verdict that says the diff could not be read (git failure, no base, unresolvable path), not that a path is out of zone."""
    return UNCHECKED in reason


def git(root: Path, *args: str) -> str | None:
    return zones.common.git(root, *args)


def base_commit(root: Path, base_branch: str = "") -> tuple[str, str]:
    """(base commit, "") or ("", reason). There is no HEAD fallback: a base that cannot be found must not hide committed changes."""
    chosen = os.environ.get("PAI_HARNESS_BASE", "").strip()
    configured = [f"origin/{base_branch}", base_branch] if base_branch else []
    candidates = [chosen] if chosen else [*configured, *BASE_CANDIDATES]
    for ref in candidates:
        found = git(root, "merge-base", "HEAD", ref)
        if found and found.strip():
            return found.strip(), ""
    return "", f"no base commit found (tried {', '.join(candidates)}); set PAI_HARNESS_BASE"


def changed_paths(root: Path, base_branch: str = "") -> tuple[list[str], str]:
    """(paths relative to the repository top level changed in the worktree or committed since the base commit, "") or ([], reason)."""
    top = git(root, "rev-parse", "--show-toplevel")
    if top is None:
        return [], ("git failed or timed out" if zones.common.in_repository(root) else "")
    top_dir, found = Path(top.strip()), []
    status = git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    if status is None:
        return [], "git status failed or timed out"
    entries = status.split("\0")
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
    base, problem = base_commit(root, base_branch)
    if problem:
        return [], problem
    diff = git(root, "diff", "--name-only", "-z", base)
    if diff is None:
        return [], "git diff failed or timed out"
    found += [p for p in diff.split("\0") if p]
    seen, out = set(), []
    for relative in found:
        absolute = (top_dir / relative).as_posix()
        if absolute not in seen:
            seen.add(absolute)
            out.append(absolute)
    return out, ""


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
        return [(str(cwd), f"Write zone: {zones.roots_problem(config_path.parent, cwd)}, so the zone diff {UNCHECKED}. Ask your lead.")]
    flagged, seen = [], set()
    for root in roots:
        paths, problem = changed_paths(root, config.get("project", {}).get("base_branch", ""))
        if problem:
            flagged.append((str(root), f"Write zone: {root} {UNCHECKED}: {problem}. Stop is blocked until the zone diff can be read; ask your lead."))
            continue
        for absolute in paths:
            if absolute in seen or zones.zone_root_for(Path(absolute), roots) != root:
                continue
            seen.add(absolute)
            # A changed symlink is judged by its own path; only a parent directory that resolves outside the root is unjudgeable.
            real = Path(os.path.realpath(os.path.dirname(absolute)))
            if not real.is_relative_to(Path(os.path.realpath(root))) and not (state is not None and real.is_relative_to(Path(os.path.realpath(state)))):
                flagged.append((absolute, f"Write zone: {absolute} {UNCHECKED}: its directory resolves to {real}, outside {root}. Stop is blocked; ask your lead."))
                continue
            reason = zones.zone_verdict(absolute, root, config, root, state, agent, follow=False)
            if reason:
                try:
                    shown = Path(os.path.realpath(absolute)).relative_to(Path(os.path.realpath(root))).as_posix()
                except ValueError:
                    shown = absolute
                flagged.append((shown, reason))
    return flagged
