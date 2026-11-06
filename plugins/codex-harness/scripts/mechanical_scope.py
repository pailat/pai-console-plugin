"""The git side of the mechanical lane: which paths a run changed, as repo-root-relative literal paths, and a digest that binds a verdict to them.

Shared by launch.py (baseline before the run), verify_mechanical.py (verdict) and task_done.py (re-check at close). Every failure
is a ScopeError: callers fail closed on it, they never treat it as "nothing changed".

Three sources make the changed set: tracked paths that differ from the start commit (staged or not), untracked paths, and
gitignored paths that are new or different from the baseline taken at launch (an ignored file like `.env` is invisible to
`git diff` and `git status`, and the lane has Edit).
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import subprocess
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

GIT_TIMEOUT_SECONDS = 300


class ScopeError(Exception):
    """git failed, timed out, or the baseline is missing: the scope cannot be established."""


def git(root: str, *argv: str) -> subprocess.CompletedProcess:
    # GIT_LITERAL_PATHSPECS: a path like app/[slug]/page.tsx is a literal name, not a glob.
    env = {**os.environ, "GIT_LITERAL_PATHSPECS": "1"}
    try:
        return run_process(["git", "-C", root, *argv], capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS, env=env)
    except (OSError, subprocess.SubprocessError) as error:
        raise ScopeError(f"git {argv[0]} failed: {error}") from error


def git_ok(root: str, *argv: str) -> str:
    done = git(root, *argv)
    if done.returncode != 0:
        raise ScopeError(f"git {argv[0]} exited {done.returncode}: {done.stderr.strip()}")
    return done.stdout


def toplevel(cwd: str) -> tuple[str, str]:
    """(repo root, cwd prefix relative to it with a trailing slash, or "")."""
    root = git_ok(cwd, "rev-parse", "--show-toplevel").strip()
    prefix = git_ok(cwd, "rev-parse", "--show-prefix").strip()
    if not root:
        raise ScopeError("git reported no worktree root")
    return str(Path(root).resolve()), prefix


def root_relative(prefix: str, files: list[str]) -> list[str]:
    return [posixpath.normpath(prefix + f) for f in files]


def _listing(root: str, *argv: str) -> list[str]:
    return [p for p in git_ok(root, *argv).split("\0") if p]


def ignored_files(root: str) -> dict[str, list[int]]:
    """Every gitignored untracked file with its size and mtime, so a later change to one is visible."""
    out: dict[str, list[int]] = {}
    for path in _listing(root, "ls-files", "--others", "--ignored", "--exclude-standard", "-z"):
        try:
            info = os.lstat(os.path.join(root, path))
        except OSError:
            continue
        out[path] = [info.st_size, info.st_mtime_ns]
    return out


def write_baseline(root: str, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ignored_files(root)), encoding="utf-8")
    return path


def read_baseline(path: str | None) -> dict[str, list[int]]:
    try:
        data = json.loads(Path(path or "").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ScopeError(f"the ignored-files baseline taken at launch is missing or unreadable: {error}") from error
    if not isinstance(data, dict):
        raise ScopeError("the ignored-files baseline is not a mapping")
    return data


def changed_paths(root: str, base: str, baseline: dict[str, list[int]]) -> list[str]:
    """Every path that differs from the start commit: tracked, untracked, and ignored ones new or modified since the baseline."""
    found = set(_listing(root, "diff", "--name-only", "--no-renames", "-z", base))
    found.update(_listing(root, "ls-files", "--others", "--exclude-standard", "-z"))
    now = ignored_files(root)
    found.update(p for p, stat in now.items() if baseline.get(p) != stat)
    found.update(p for p in baseline if p not in now and not os.path.lexists(os.path.join(root, p)))  # an ignored file the run deleted
    return sorted(found)


def head_of(root: str) -> str:
    return git_ok(root, "rev-parse", "HEAD").strip()


def digest(root: str, head: str, paths: list[str]) -> str:
    """A hash of HEAD and the content of every changed path: the identity of exactly the work a verdict covers."""
    h = hashlib.sha256(head.encode() + b"\0")
    for path in sorted(paths):
        full = os.path.join(root, path)
        h.update(path.encode() + b"\0")
        try:
            if os.path.islink(full):
                h.update(b"link:" + os.readlink(full).encode())
            else:
                h.update(hashlib.sha256(Path(full).read_bytes()).digest())
        except OSError:
            h.update(b"absent")
        h.update(b"\0")
    return h.hexdigest()


def snapshot(root: str, base: str, baseline_path: str | None) -> dict:
    """The current scope of a run: head, changed paths and the digest binding them."""
    head = head_of(root)
    changed = changed_paths(root, base, read_baseline(baseline_path))
    return {"head": head, "changed": changed, "digest": digest(root, head, changed)}
