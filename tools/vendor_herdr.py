#!/usr/bin/env python3
"""Refresh vendor/herdr from the commit pinned in .claude-plugin/marketplace.json.

The marketplace entry is the single source of the pin. This tool fetches exactly that
commit from upstream, checks that its tag still points at it, copies the skill
directory and rewrites vendor/herdr/PROVENANCE.json with sha256 digests.
Then run tools/build_codex.py to regenerate the Codex packages.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout.strip()


def main() -> int:
    marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text())
    pin = next(p["source"] for p in marketplace["plugins"] if p["name"] == "herdr")
    url = pin["url"] if "://" in pin["url"] else f"https://github.com/{pin['url']}.git"
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        git(work, "init", "-q", ".")
        git(work, "fetch", "-q", "--depth", "1", url, pin["sha"])
        git(work, "checkout", "-q", "FETCH_HEAD")
        if git(work, "rev-parse", "HEAD") != pin["sha"]:
            print("Fetched commit differs from the pinned sha", file=sys.stderr)
            return 1
        tags = git(work, "ls-remote", url, f"refs/tags/{pin['ref']}", f"refs/tags/{pin['ref']}^{{}}").splitlines()
        by_ref = {line.split()[1]: line.split()[0] for line in tags}
        peeled = by_ref.get(f"refs/tags/{pin['ref']}^{{}}", by_ref.get(f"refs/tags/{pin['ref']}"))
        if peeled != pin["sha"]:
            print(f"Tag {pin['ref']} now points at {peeled}, not the pinned {pin['sha']}", file=sys.stderr)
            return 1
        source = work / pin["path"]
        if any(p.is_symlink() for p in source.rglob("*")):
            print("Upstream skill contains symlinks, which are not portable", file=sys.stderr)
            return 1
        target = ROOT / "vendor/herdr" / pin["path"]
        for old in sorted(target.rglob("*"), reverse=True) if target.exists() else []:
            old.unlink() if old.is_file() else old.rmdir()
        files = {}
        for path in sorted(p for p in source.rglob("*") if p.is_file()):
            relative = Path(pin["path"]) / path.relative_to(source)
            (ROOT / "vendor/herdr" / relative).parent.mkdir(parents=True, exist_ok=True)
            (ROOT / "vendor/herdr" / relative).write_bytes(path.read_bytes())
            files[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    record = {"repository": url.removesuffix(".git"), "tag": pin["ref"], "tagObject": json.loads((ROOT / "vendor/herdr/PROVENANCE.json").read_text()).get("tagObject"),
              "commit": pin["sha"], "path": pin["path"], "files": files}
    (ROOT / "vendor/herdr/PROVENANCE.json").write_text(json.dumps(record, indent=2) + "\n")
    print(f"Vendored {len(files)} file(s) from {record['repository']} at {pin['sha']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
