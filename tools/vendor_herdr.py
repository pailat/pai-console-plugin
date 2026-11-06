#!/usr/bin/env python3
"""Refresh skills/herdr and plugins/pai-harness/skills/herdr, the vendored upstream Herdr skill, from the pin in vendor/herdr/PIN.json.

Usage:
  python3 tools/vendor_herdr.py              re-vendor the pinned commit (restores the files exactly)
  python3 tools/vendor_herdr.py --tag vX.Y.Z move the pin to that upstream release tag, then vendor it
  python3 tools/vendor_herdr.py --latest     move the pin to the newest upstream release, then vendor it

The tool fetches exactly the pinned commit from upstream, checks that its tag still points at it,
copies the upstream skill directory verbatim into both skill directories and rewrites
vendor/herdr/PROVENANCE.json with sha256 digests. Never edit skills/herdr by hand. Afterwards run
`python3 tools/build_codex.py` to regenerate the Codex packages; `make check` fails on any drift
between the pin, the record and the files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
PIN = ROOT / "vendor/herdr/PIN.json"
RECORD = ROOT / "vendor/herdr/PROVENANCE.json"
TARGETS = (ROOT / "skills/herdr", ROOT / "plugins/pai-harness/skills/herdr")  # pai-console and pai-harness each ship the skill
TAG = re.compile(r"^v\d+\.\d+\.\d+$")


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def resolve_tag(repository: str, tag: str) -> tuple[str, str | None]:
    """Return (commit, tag object or None) of an upstream release tag."""
    lines = git(Path.cwd(), "ls-remote", repository, f"refs/tags/{tag}", f"refs/tags/{tag}^{{}}").splitlines()
    by_ref = {line.split()[1]: line.split()[0] for line in lines}
    peeled = f"refs/tags/{tag}^{{}}"
    if peeled in by_ref:  # annotated tag: the tag object differs from its commit
        return by_ref[peeled], by_ref.get(f"refs/tags/{tag}")
    if f"refs/tags/{tag}" in by_ref:
        return by_ref[f"refs/tags/{tag}"], None
    raise ValueError(f"upstream has no tag {tag}")


def latest_tag(repository: str) -> str:
    tags = [line.split("refs/tags/")[1] for line in git(Path.cwd(), "ls-remote", "--tags", "--refs", repository).splitlines()]
    versions = sorted((tuple(int(n) for n in t[1:].split(".")), t) for t in tags if TAG.match(t))
    if not versions:
        raise ValueError("upstream has no release tags")
    return versions[-1][1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--tag", help="move the pin to this upstream release tag")
    group.add_argument("--latest", action="store_true", help="move the pin to the newest upstream release tag")
    args = parser.parse_args()
    pin = json.loads(PIN.read_text())
    url = pin["repository"] + ".git"
    try:
        if args.latest or args.tag:
            tag = latest_tag(url) if args.latest else args.tag
            if not TAG.match(tag):
                raise ValueError(f"{tag!r} is not a release tag like v1.2.3")
            commit, tag_object = resolve_tag(url, tag)
            pin = {**pin, "tag": tag, "tagObject": tag_object, "commit": commit}
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            git(work, "init", "-q", ".")
            git(work, "fetch", "-q", "--depth", "1", url, pin["commit"])
            git(work, "checkout", "-q", "FETCH_HEAD")
            if git(work, "rev-parse", "HEAD") != pin["commit"]:
                raise ValueError("Fetched commit differs from the pinned commit")
            commit, _ = resolve_tag(url, pin["tag"])
            if commit != pin["commit"]:
                raise ValueError(f"Tag {pin['tag']} now points at {commit}, not the pinned {pin['commit']}")
            source = work / pin["path"]
            if any(p.is_symlink() for p in source.rglob("*")):
                raise ValueError("Upstream skill contains symlinks, which are not portable")
            files = {}
            for target in TARGETS:
                for old in sorted(target.rglob("*"), reverse=True) if target.exists() else []:
                    old.unlink() if old.is_file() else old.rmdir()
                for path in sorted(p for p in source.rglob("*") if p.is_file()):
                    relative = path.relative_to(source)
                    (target / relative).parent.mkdir(parents=True, exist_ok=True)
                    (target / relative).write_bytes(path.read_bytes())
                    files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    except (ValueError, subprocess.CalledProcessError) as error:
        print(error, file=sys.stderr)
        return 1
    PIN.write_text(json.dumps(pin, indent=2) + "\n")
    record = {**pin, "files": files}
    RECORD.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Vendored {len(files)} file(s) from {pin['repository']} {pin['tag']} at {pin['commit']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
