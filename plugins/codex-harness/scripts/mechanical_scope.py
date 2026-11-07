"""The git side of the mechanical lane: which paths a run changed, as repo-root-relative literal paths, and a digest that binds a verdict to them.

Shared by launch.py (baseline before the run), verify_mechanical.py (verdict) and task_done.py (re-check at close). Every failure
is a ScopeError: callers fail closed on it, they never treat it as "nothing changed".

Three sources make the changed set: tracked paths that differ from the start commit (staged or not), untracked paths, and
gitignored paths that are new or different from a baseline (an ignored file like `.env` is invisible to `git diff` and
`git status`, and the lane has Edit).

Ignored paths are fingerprinted cheaply: a dependency/cache directory (BULK_DIRS: node_modules, .venv, target...) is fingerprinted by the
mtimes of its directories only, every other ignored file by size and mtime. Two modes: strict (launch baseline vs the lane's own edits)
and, after the project checks, tolerant: the checks may write caches and build output, so only sensitive ignored names (SENSITIVE) and
the listed files still count. Every git call runs with the repo's own config neutralised (see git()).
"""
from __future__ import annotations

import hashlib
import json
import os
import posixpath
import subprocess
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

import fnmatch

GIT_TIMEOUT_SECONDS = 300
# Dependency/cache directories: the lane may not Edit them anywhere in the tree (a deny glob in launch.py), so a directory-level fingerprint is
# enough here. Names that are often tracked source or build output (vendor, env, dist, target, coverage) are NOT in the set: they are stat'ed per file.
BULK_DIRS = frozenset({"node_modules", ".venv", "venv", ".tox", ".nox", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".next", ".nuxt", ".gradle",
                       ".cache", "__pycache__", ".terraform"})
SENSITIVE = (".env", "*.env", ".env.*", "*.pem", "*.key", ".npmrc", ".netrc", ".pypirc", "*settings?local?json", "*credentials*", "id_rsa*", "*.p12")
# Command-line -c overrides the repository's own config, so a hook, fsmonitor or pager written into .git cannot run inside the verifier.
GIT_HARDENING = ("-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null", "-c", "core.pager=cat", "-c", "core.untrackedCache=false",
                 "-c", "diff.external=", "-c", "protocol.ext.allow=never")


class ScopeError(Exception):
    """git failed, timed out, or the baseline is missing: the scope cannot be established."""


def git(root: str, *argv: str) -> subprocess.CompletedProcess:
    # GIT_LITERAL_PATHSPECS: a path like app/[slug]/page.tsx is a literal name, not a glob.
    env = {**os.environ, "GIT_LITERAL_PATHSPECS": "1", "GIT_OPTIONAL_LOCKS": "0"}
    try:
        return run_process(["git", *GIT_HARDENING, "-C", root, *argv], capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS, env=env)
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


def common_git_dir(root: str) -> str:
    """The absolute common git directory (the main checkout's .git for a linked worktree): where config and hooks live."""
    out = git_ok(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()
    return str(Path(out).resolve()) if out else os.path.join(root, ".git")


def root_relative(prefix: str, files: list[str]) -> list[str]:
    return [posixpath.normpath(prefix + f) for f in files]


def _listing(root: str, *argv: str) -> list[str]:
    return [p for p in git_ok(root, *argv).split("\0") if p]


def _lstat(root: str, path: str) -> list[int] | None:
    try:
        info = os.lstat(os.path.join(root, path))
    except OSError:
        return None
    return [info.st_size, info.st_mtime_ns]


def _dir_fingerprint(root: str, rel: str) -> dict[str, int]:
    """mtime of a directory and of every directory below it: a created or removed entry changes its parent's mtime. Files are not stat'ed."""
    out: dict[str, int] = {}
    for current, dirnames, _ in os.walk(os.path.join(root, rel)):
        try:
            out[os.path.relpath(current, root)] = os.lstat(current).st_mtime_ns
        except OSError:
            continue
        dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(current, d))]
    return out


def ignored_state(root: str) -> dict:
    """The gitignored untracked files (size, mtime) and, for the BULK_DIRS, a directory-level fingerprint."""
    files: dict[str, list[int]] = {}
    dirs: dict[str, dict[str, int]] = {}
    for entry in _listing(root, "ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"):
        if not entry.endswith("/"):
            stat = _lstat(root, entry)
            if stat:
                files[entry] = stat
            continue
        rel = entry.rstrip("/")
        if posixpath.basename(rel) in BULK_DIRS:
            dirs[rel] = _dir_fingerprint(root, rel)
            continue
        for current, dirnames, filenames in os.walk(os.path.join(root, rel)):
            for name in (*filenames, *[d for d in dirnames if os.path.islink(os.path.join(current, d))]):
                path = os.path.relpath(os.path.join(current, name), root)
                stat = _lstat(root, path)
                if stat:
                    files[path] = stat
            dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(current, d))]
    return {"files": files, "dirs": dirs}


def write_state(path: Path, state: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")
    return path


def write_baseline(root: str, path: Path) -> Path:
    return write_state(path, ignored_state(root))


def read_baseline(path: str | None) -> dict:
    try:
        data = json.loads(Path(path or "").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ScopeError(f"the ignored-files baseline is missing or unreadable: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("files"), dict) or not isinstance(data.get("dirs"), dict):
        raise ScopeError("the ignored-files baseline is not in the expected shape")
    return data


def sensitive(path: str) -> bool:
    name = posixpath.basename(path.rstrip("/"))
    return any(fnmatch.fnmatch(name, pattern) for pattern in SENSITIVE)


def ignored_diff(baseline: dict, now: dict) -> set[str]:
    out = {p for p, stat in now["files"].items() if baseline["files"].get(p) != stat}
    out.update(p for p in baseline["files"] if p not in now["files"])
    for d, fingerprint in now["dirs"].items():
        old = baseline["dirs"].get(d)
        if old is None:
            out.add(d + "/")
            continue
        out.update(sub + "/" for sub in {*fingerprint, *old} if fingerprint.get(sub) != old.get(sub))
    out.update(d + "/" for d in baseline["dirs"] if d not in now["dirs"])
    return out


def tracked_and_untracked(root: str, base: str) -> set[str]:
    found = set(_listing(root, "diff", "--name-only", "--no-renames", "--no-ext-diff", "--no-textconv", "-z", base))
    found.update(_listing(root, "ls-files", "--others", "--exclude-standard", "-z"))
    return found


def changed_paths(root: str, base: str, baseline: dict, now: dict | None = None, tolerant: bool = False, listed: list[str] | None = None) -> list[str]:
    """Every path that differs from the start commit. Strict: ignored paths new or changed since the baseline all count.

    Tolerant (after the checks, which may legitimately write caches and build output): of the ignored paths only the sensitive names
    and the listed files count; tracked and untracked paths always count.
    """
    found = tracked_and_untracked(root, base)
    ignored = ignored_diff(baseline, now if now is not None else ignored_state(root))
    if tolerant:
        ignored = {p for p in ignored if sensitive(p) or p in (listed or [])}
    return sorted(found | ignored)


def head_of(root: str) -> str:
    return git_ok(root, "rev-parse", "HEAD").strip()


def is_ancestor(root: str, base: str, head: str) -> bool:
    return git(root, "merge-base", "--is-ancestor", base, head).returncode == 0


def digest(root: str, paths: list[str]) -> str:
    """A hash of the content of every changed path (against the start commit): the identity of exactly the work a verdict covers.

    HEAD is not part of it: committing the verified work (a descendant of the start commit with the same net change) keeps the digest.
    """
    h = hashlib.sha256()
    for path in sorted(paths):
        full = os.path.join(root, path)
        h.update(path.encode() + b"\0")
        try:
            info = os.lstat(full)
            h.update(f"mode:{info.st_mode:o}:".encode())  # file type and permission bits
            if os.path.islink(full):
                h.update(b"link:" + os.readlink(full).encode())
            elif not os.path.isdir(full):
                h.update(hashlib.sha256(Path(full).read_bytes()).digest())
        except OSError:
            h.update(b"absent")
        h.update(b"\0")
    return h.hexdigest()


def snapshot(root: str, base: str, baseline: dict, tolerant: bool = False, listed: list[str] | None = None) -> dict:
    """The current scope of a run: head, changed paths, the digest binding them and the ignored state that was scanned (reusable as a baseline)."""
    head = head_of(root)
    now = ignored_state(root)
    changed = changed_paths(root, base, baseline, now, tolerant, listed)
    return {"head": head, "changed": changed, "digest": digest(root, changed), "ignored": now}


# Every config key is watched EXCEPT the few that ordinary git activity rewrites in the shared common dir (push -u, fetch, gh pr create, a new
# branch, gc): an unknown key that runs a program must never pass unnoticed, so this is an ignore-list, not a watch-list.
IGNORED_PREFIXES = ("branch.", "user.", "maintenance.")
IGNORED_REMOTE_VARS = frozenset({"url", "fetch", "pushurl", "push", "tagopt", "prune", "gh-resolved"})
HARMLESS_CORE = frozenset({"core.repositoryformatversion", "core.filemode", "core.bare", "core.logallrefupdates", "core.ignorecase", "core.symlinks",
                           "core.precomposeunicode", "core.worktree", "core.commitgraph", "core.multipackindex", "core.untrackedcache"})


def ignored_key(key: str) -> bool:
    """True for a config key that ordinary git activity rewrites and that cannot make git run a program."""
    var = key.rsplit(".", 1)[-1]
    if key.startswith(IGNORED_PREFIXES) or key in HARMLESS_CORE:
        return True
    if key.startswith("gc."):
        return not key.endswith(".command")
    return key.startswith("remote.") and var in IGNORED_REMOTE_VARS


def _config_keys(path: str) -> list[str]:
    """Every watched key of one config file (all but ignored_key) as sorted key=value lines (the file is read by git itself, includes are not followed)."""
    if not os.path.isfile(path):
        return []
    done = run_process(["git", "config", "--file", path, "--list", "-z"], capture_output=True, text=True, timeout=60)
    if done.returncode != 0:
        raise ScopeError(f"git config could not read {path}: {done.stderr.strip()}")
    keys = []
    for entry in done.stdout.split("\0"):
        key, _, value = entry.partition("\n")
        key = key.lower()
        if key and not ignored_key(key):
            keys.append(f"{key}={value}")
    return sorted(keys)


def git_integrity(root: str) -> str:
    """A hash of what in .git makes git run code: every config key but the ignore-list (repo, common, per-worktree and modules/*/config), hook files, info/attributes.

    The common git dir of a linked worktree is the main checkout's, shared with every other worktree, so ordinary git activity elsewhere
    (push -u, fetch, gh pr create, a new branch) must not change the hash: ignored_key keys, sample hooks and info/exclude are skipped.
    Any other key, a new hook or a changed attributes file does change it.
    """
    h = hashlib.sha256()
    git_dir = git_ok(root, "rev-parse", "--path-format=absolute", "--git-dir").strip()
    common = common_git_dir(root)
    for d in dict.fromkeys((git_dir, common)):
        for name in ("config", "config.worktree"):
            h.update(f"{d}/{name}\0".encode() + "\n".join(_config_keys(os.path.join(d, name))).encode() + b"\0")
        attributes = os.path.join(d, "info/attributes")
        h.update(f"{attributes}\0".encode() + (Path(attributes).read_bytes() if os.path.isfile(attributes) else b"-") + b"\0")
    for d in dict.fromkeys((git_dir, common)):
        modules = os.path.join(d, "modules")
        if os.path.isdir(modules):
            for current, _, files in sorted(os.walk(modules)):
                if "config" in files:
                    h.update(f"{current}/config\0".encode() + "\n".join(_config_keys(os.path.join(current, "config"))).encode() + b"\0")
    for hooks in dict.fromkeys((os.path.join(git_dir, "hooks"), os.path.join(common, "hooks"))):
        if os.path.isdir(hooks):
            for name in sorted(os.listdir(hooks)):
                if name.endswith(".sample"):
                    continue
                full = os.path.join(hooks, name)
                try:
                    h.update(f"{full}\0{os.lstat(full).st_mode:o}\0".encode() + (hashlib.sha256(Path(full).read_bytes()).digest() if os.path.isfile(full) else b"-") + b"\0")
                except OSError:
                    h.update(f"{full}\0unreadable\0".encode())
    return h.hexdigest()
