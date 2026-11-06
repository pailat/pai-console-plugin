"""Shared fixtures for the harness script tests: an isolated state dir, the Acme config, the fake claude and herdr."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "plugins/pai-harness/scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures/harness"


PLUGIN_ROOT = ROOT / "plugins/pai-harness"


def materialize(name: str, dest: Path, drop_skill: str | None = None, hooks_dir: Path | None = None) -> Path:
    """Copy fixture `name` to `dest`, filling the init event: this checkout's plugin path and its real skill list.

    The placeholders keep the fixtures independent of where the repo is checked out and of how many skills it has.
    `drop_skill` omits one skill from the init; `hooks_dir` reports a different plugin directory (for a hooks.json variant).
    """
    skills = sorted(f"pai-harness:{d.name}" for d in (PLUGIN_ROOT / "skills").glob("*") if (d / "SKILL.md").is_file())
    out = []
    for line in (FIXTURES / f"{name}.jsonl").read_text().splitlines():
        frame = json.loads(line)
        if frame.get("subtype") == "init":
            for plugin in frame["plugins"]:
                if plugin["path"] == "__PLUGIN_ROOT__":
                    plugin["path"] = str(hooks_dir or PLUGIN_ROOT)
            frame["skills"] = [s for s in frame["skills"] if s != "__PAI_HARNESS_SKILLS__"] + [s for s in skills if s != drop_skill]
        out.append(json.dumps(frame))
    dest.write_text("\n".join(out) + "\n")
    return dest


class HarnessCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.state = self.tmp / "state"
        self.env = {**os.environ, "PAI_HARNESS_CONFIG": str(FIXTURES / "acme.pai-harness.toml"), "PAI_HARNESS_STATE_DIR": str(self.state),
                    "PAI_HARNESS_CLAUDE": str(FIXTURES / "fake_claude.py"), "PAI_HARNESS_INSTALLED_PLUGINS": str(self._tmp.name + "/none.json"), "FAKE_CLAUDE_LOG": str(self.tmp / "claude.json")}
        for name in ("PAI_HARNESS_MCP_CMD", "LINEAR_API_KEY", "LINEAR_API_URL", "PAI_HARNESS_HERDR"):
            self.env.pop(name, None)
        for name in [k for k in self.env if k.startswith("HERDR_")]:
            self.env.pop(name)  # a launch under test must not open a tab in the developer's own Herdr session
        self.prompt = self.tmp / "prompt.md"
        self.prompt.write_text("Implement ACME-7 for the Acme app.\n")

    def run_script(self, script: str, *args: str, stdin: str | None = None, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(SCRIPTS / script), *args], input=stdin, text=True, capture_output=True, env={**self.env, **env}, timeout=60)

    def fixture(self, name: str, **options: object) -> Path:
        return materialize(name, self.tmp / f"{name}.materialized.jsonl", **options)

    def launch(self, issue: str, fixture: str, exit_code: int = 0, *extra: str, **env: str) -> subprocess.CompletedProcess:
        return self.run_script("launch.sh", issue, "--prompt-file", str(self.prompt), *extra,
                               FAKE_CLAUDE_FIXTURE=str(self.fixture(fixture)), FAKE_CLAUDE_EXIT=str(exit_code), **env)

    def record(self, issue: str) -> dict:
        return json.loads((self.state / "runs" / f"{issue}.state.json").read_text())

    def journal(self) -> list[dict]:
        path = self.state / "journal.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
