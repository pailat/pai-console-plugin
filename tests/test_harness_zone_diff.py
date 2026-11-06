"""Stop-time zone diff of the pai-harness hooks: a real git repo in a temp dir, writes the PreToolUse hook cannot see."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from tests.test_harness_hooks import HOOKS, HookCase


class ZoneDiffCase(HookCase):
    def setUp(self) -> None:
        super().setUp()
        self.git("init", "-q", "-b", "main")
        for relative in ("apps/acme-app/page.ts", "packages/contracts/api.ts", "AGENTS.md", "docs/guide.md", "notes.txt"):
            self.write(relative, "one\n")
        self.git("add", "-A")
        self.git("-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "-m", "base")
        self.git("checkout", "-q", "-b", "feature")
        self.delta = self.state / "deltas" / "acme-7.json"
        self.delta.parent.mkdir(parents=True)
        self.delta.write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))

    def git(self, *args: str) -> None:
        subprocess.run(["git", "-C", str(self.project), *args], check=True, capture_output=True, env={**os.environ, "HOME": self._tmp.name})

    def write(self, relative: str, text: str) -> None:
        path = self.project / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)

    def stop(self, **env: str | None) -> dict | None:
        return self.run_hook("stop.py", "stop", **env)

    def sh(self, command: str) -> None:
        subprocess.run(command, shell=True, cwd=self.project, check=True, capture_output=True)

    def assertBlocked(self, result: dict | None, *paths: str) -> str:
        self.assertIsNotNone(result)
        self.assertEqual(result["decision"], "block")
        for path in paths:
            self.assertIn(path, result["reason"])
        self.assertIn("owned by acme-lead", result["reason"])
        return result["reason"]


class StopZoneDiffTest(ZoneDiffCase):
    def test_clean_worktree_and_in_zone_changes_pass(self) -> None:
        self.assertIsNone(self.stop())
        self.sh("sed -i s/one/two/ apps/acme-app/page.ts && echo new > docs/new.md && echo x > apps/acme-app/added.ts")
        self.assertIsNone(self.stop())

    def test_sed_in_place_outside_the_zone_is_caught(self) -> None:
        self.sh("sed -i s/one/two/ packages/contracts/api.ts")
        reason = self.assertBlocked(self.stop(), "packages/contracts/api.ts")
        self.assertIn("ROOT zone", reason)

    def test_cp_and_mv_outside_the_zone_are_caught(self) -> None:
        self.sh("cp apps/acme-app/page.ts packages/contracts/copied.ts && mv AGENTS.md AGENTS.old")
        reason = self.assertBlocked(self.stop(), "packages/contracts/copied.ts", "AGENTS.md")
        self.assertIn("AGENTS.old", reason)  # the new name is outside the zone too (no zone covers it)

    def test_a_python_write_outside_the_zone_is_caught(self) -> None:
        self.sh("python3 -c \"open('packages/contracts/api.ts', 'a').write('two')\"")
        self.assertBlocked(self.stop(), "packages/contracts/api.ts")

    def test_a_staged_or_committed_change_outside_the_zone_is_caught(self) -> None:
        self.sh("echo two > packages/contracts/api.ts && git add -A")
        self.assertBlocked(self.stop(), "packages/contracts/api.ts")
        self.git("-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "-m", "work")
        self.assertBlocked(self.stop(), "packages/contracts/api.ts")

    def test_a_path_no_zone_covers_is_outside_the_agents_zones(self) -> None:
        self.sh("echo two > notes.txt")
        result = self.stop()
        self.assertEqual(result["decision"], "block")
        self.assertIn("notes.txt is outside your zones (frontend) and no declared zone covers it", result["reason"])

    def test_the_state_dir_passes(self) -> None:
        inside = self.project / "state"
        env = {"PAI_HARNESS_STATE_DIR": str(inside)}
        (inside / "deltas").mkdir(parents=True)
        (inside / "deltas" / "acme-7.json").write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))
        (inside / "journal.jsonl").write_text("{}\n")
        self.assertIsNone(self.stop(**env))

    def test_a_non_writing_role_with_no_zones_assigned_is_not_checked(self) -> None:
        self.sh("sed -i s/one/two/ packages/contracts/api.ts")
        self.assertIsNone(self.stop(PAI_HARNESS_ZONES=None, PAI_HARNESS_AGENT="acme-7", PAI_HARNESS_ROLE="watcher"))

    def test_the_block_names_the_delta_problem_too(self) -> None:
        self.delta.unlink()
        self.sh("sed -i s/one/two/ packages/contracts/api.ts")
        reason = self.assertBlocked(self.stop(), "packages/contracts/api.ts")
        self.assertIn("a knowledge delta is required", reason)

    def test_the_stop_retry_bound_holds_and_the_missing_marker_lists_the_paths(self) -> None:
        self.sh("mv AGENTS.md packages/contracts/AGENTS.md")
        for attempt in (1, 2, 3):
            self.assertEqual(self.stop()["decision"], "block", attempt)
        self.assertIsNone(self.stop())
        missing = json.loads((self.state / "deltas" / "acme-7.missing").read_text())
        self.assertEqual((missing["agent"], missing["blocks"]), ("acme-7", 3))
        self.assertEqual(sorted(missing["out_of_zone"]), ["AGENTS.md", "packages/contracts/AGENTS.md"])
        self.assertEqual(missing["problem"], "changes outside the agent's zones")

    def test_reverting_the_change_clears_the_block_count(self) -> None:
        self.sh("echo two > packages/contracts/api.ts")
        self.assertEqual(self.stop()["decision"], "block")
        self.sh("git checkout -- packages/contracts/api.ts")
        self.assertIsNone(self.stop())
        self.assertFalse((self.state / "deltas" / "acme-7.blocks").exists())

    def test_a_non_git_project_is_not_flagged(self) -> None:
        self.sh("rm -rf .git")
        self.assertIsNone(self.stop())

    def test_the_agent_zones_come_from_owners_when_no_zones_are_exported(self) -> None:
        self.sh("sed -i s/one/two/ apps/acme-app/page.ts && echo x > packages/contracts/new.ts")
        self.assertBlocked(self.stop(PAI_HARNESS_ZONES=None, PAI_HARNESS_AGENT="acme-app-owner"), "packages/contracts/new.ts")


if __name__ == "__main__":
    unittest.main()
