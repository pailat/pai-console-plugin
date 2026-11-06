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


class HarnessCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.state = self.tmp / "state"
        self.env = {**os.environ, "PAI_HARNESS_CONFIG": str(FIXTURES / "acme.pai-harness.toml"), "PAI_HARNESS_STATE_DIR": str(self.state),
                    "PAI_HARNESS_CLAUDE": str(FIXTURES / "fake_claude.py"), "FAKE_CLAUDE_LOG": str(self.tmp / "claude.json")}
        for name in ("PAI_HARNESS_MCP_CMD", "LINEAR_API_KEY", "LINEAR_API_URL", "PAI_HARNESS_HERDR"):
            self.env.pop(name, None)
        self.prompt = self.tmp / "prompt.md"
        self.prompt.write_text("Implement ACME-7 for the Acme app.\n")

    def run_script(self, script: str, *args: str, stdin: str | None = None, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([str(SCRIPTS / script), *args], input=stdin, text=True, capture_output=True, env={**self.env, **env}, timeout=60)

    def launch(self, issue: str, fixture: str, exit_code: int = 0, *extra: str) -> subprocess.CompletedProcess:
        return self.run_script("launch.sh", issue, "--prompt-file", str(self.prompt), *extra,
                               FAKE_CLAUDE_FIXTURE=str(FIXTURES / f"{fixture}.jsonl"), FAKE_CLAUDE_EXIT=str(exit_code))

    def record(self, issue: str) -> dict:
        return json.loads((self.state / "runs" / f"{issue}.state.json").read_text())

    def journal(self) -> list[dict]:
        path = self.state / "journal.jsonl"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
