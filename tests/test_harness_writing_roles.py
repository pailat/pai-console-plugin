"""Zoneless writing roles: Stop blocks them (bounded), the launcher refuses them outside a git worktree."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, HarnessCase  # noqa: E402
from tests.test_harness_hooks import HookCase  # noqa: E402

NO_ZONES = {"PAI_HARNESS_ZONES": None, "PAI_HARNESS_AGENT": "acme-7"}
WRITING = ("implementer", "mechanical", "integrator")
NON_WRITING = ("relay", "watcher", "root-reviewer", "gate-triager", "distiller")


class ZonelessStopTest(HookCase):
    def deltas(self, name: str) -> Path:
        return self.state / "deltas" / name

    def valid_delta(self) -> None:
        self.deltas("acme-7.json").parent.mkdir(parents=True, exist_ok=True)
        self.deltas("acme-7.json").write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))

    def test_a_zoneless_writing_role_blocks_even_with_a_valid_delta(self) -> None:
        self.valid_delta()
        for role in WRITING:
            self.deltas("acme-7.blocks").unlink(missing_ok=True)
            result = self.run_hook("stop.py", "stop", PAI_HARNESS_ROLE=role, **NO_ZONES)
            self.assertEqual(result["decision"], "block", role)
            self.assertIn(f"no write zone configured for {role}; ask your lead", result["reason"])

    def test_it_is_released_after_three_blocks_with_a_marker_listing_the_problem(self) -> None:
        self.valid_delta()
        for attempt in (1, 2, 3):
            self.assertEqual(self.run_hook("stop.py", "stop", **NO_ZONES)["decision"], "block", attempt)
            self.assertFalse(self.deltas("acme-7.missing").exists())
        self.assertIsNone(self.run_hook("stop.py", "stop", **NO_ZONES))
        missing = json.loads(self.deltas("acme-7.missing").read_text())
        self.assertEqual(missing["problem"], "no write zone configured for implementer; ask your lead")
        self.assertEqual(missing["blocks"], 3)

    def test_the_block_also_names_a_missing_delta(self) -> None:
        reason = self.run_hook("stop.py", "stop", **NO_ZONES)["reason"]
        self.assertIn("knowledge delta is required", reason)
        self.assertIn("no write zone configured for implementer; ask your lead", reason)

    def test_non_writing_roles_may_run_zoneless(self) -> None:
        self.valid_delta()
        for role in NON_WRITING:
            self.assertIsNone(self.run_hook("stop.py", "stop", PAI_HARNESS_ROLE=role, **NO_ZONES), role)

    def test_a_writing_role_with_a_zone_still_passes(self) -> None:
        self.valid_delta()
        self.assertIsNone(self.run_hook("stop.py", "stop"))


class LauncherWorktreeTest(HarnessCase):
    def test_a_writing_role_outside_a_git_worktree_is_refused_and_journaled(self) -> None:
        with tempfile.TemporaryDirectory() as plain:
            for role in WRITING:
                done = self.launch("ACME-7", "success", 0, "--role", role, "--cwd", plain)
                self.assertEqual(done.returncode, 1, role)
                self.assertIn(f"BLOCKER ACME-7: writing role {role} must run inside a git worktree", done.stderr)
        blockers = [e for e in self.journal() if e["kind"] == "run.blocked"]
        self.assertEqual(len(blockers), len(WRITING))
        self.assertFalse((self.state / "runs" / "ACME-7.state.json").exists())

    def test_the_default_role_is_a_writing_role(self) -> None:
        with tempfile.TemporaryDirectory() as plain:
            self.assertEqual(self.launch("ACME-7", "success", 0, "--cwd", plain).returncode, 1)

    def test_a_writing_role_inside_a_git_worktree_runs(self) -> None:
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", "-q", repo], check=True, capture_output=True)
            done = self.launch("ACME-7", "success", 0, "--role", "implementer", "--cwd", repo)
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(self.record("ACME-7")["state"], "done")

    def test_a_non_writing_role_runs_outside_a_git_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as plain:
            done = self.launch("ACME-7", "success", 0, "--role", "relay", "--cwd", plain)
            self.assertEqual(done.returncode, 0, done.stderr)


if __name__ == "__main__":
    unittest.main()
