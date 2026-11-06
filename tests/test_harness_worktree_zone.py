"""Zone checks when PAI_HARNESS_CONFIG lives in another checkout than the agent's worktree (ATE-1214). Acme fixture only."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from tests.test_harness_hooks import HookCase, deny


class WorktreeCase(HookCase):
    NESTED = False  # True: the worktree lives under the config's checkout, as <repo>/.claude/worktrees/x does

    def setUp(self) -> None:
        super().setUp()
        self.git(self.project, "init", "-q", "-b", "main")
        for relative in ("apps/acme-app/page.ts", "packages/contracts/api.ts"):
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("one\n")
        self.git(self.project, "add", "-A")
        self.git(self.project, "-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "-m", "base")
        self.worktree = (self.project / ".claude/worktrees/x") if self.NESTED else Path(self._tmp.name).resolve() / "worktree"
        self.worktree.parent.mkdir(parents=True, exist_ok=True)
        self.git(self.project, "worktree", "add", "-q", "-b", "feature", str(self.worktree))
        self.config = str(self.project / ".pai-harness.toml")  # the primary checkout's config, not the worktree's
        delta = self.state / "deltas" / "acme-7.json"
        delta.parent.mkdir(parents=True)
        delta.write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))

    def git(self, where: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(where), *args], check=True, capture_output=True, env={**os.environ, "HOME": self._tmp.name})

    def run_in(self, script: str, name: str, cwd: Path, **env: str | None) -> dict | None:
        merged = {k: v for k, v in {**self.env, "PAI_HARNESS_CONFIG": self.config, **env}.items() if v is not None}
        done = subprocess.run(["python3", str(self.hooks / script)], input=self.event(name), text=True, capture_output=True, env=merged, cwd=cwd, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    @property
    def hooks(self) -> Path:
        from tests.test_harness_hooks import HOOKS
        return HOOKS


class WorktreePreToolUseTest(WorktreeCase):
    CONTRACTS = ("Write zone: packages/contracts/c.txt belongs to zone 'contracts', owned by acme-lead. It is a ROOT zone: the change needs "
                 "the orchestrator's ROOT go. Your zones: frontend. File a zone request with the owner instead of writing it.")

    def test_a_write_out_of_zone_in_the_worktree_is_denied(self) -> None:
        self.assertEqual(self.run_in("pre_tool_use.py", "write-worktree-other-zone", self.worktree), deny(self.CONTRACTS))

    def test_the_same_holds_in_bypass_permissions_mode(self) -> None:
        self.assertIn('"bypassPermissions"', self.event("write-worktree-other-zone"))
        out = self.run_in("pre_tool_use.py", "write-worktree-other-zone", self.worktree)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_write_in_zone_in_the_worktree_is_allowed(self) -> None:
        self.assertIsNone(self.run_in("pre_tool_use.py", "write-worktree-in-zone", self.worktree))

    def test_a_write_into_the_config_checkout_out_of_zone_is_denied_too(self) -> None:
        # the event path is rewritten to the primary checkout while cwd stays in the worktree
        self.worktree_path = self.project
        text = self.event("write-worktree-other-zone").replace(str(self.worktree) + "/packages", str(self.project) + "/packages")
        merged = {**self.env, "PAI_HARNESS_CONFIG": self.config}
        done = subprocess.run(["python3", str(self.hooks / "pre_tool_use.py")], input=text, text=True, capture_output=True, env=merged, cwd=self.worktree)
        self.assertEqual(json.loads(done.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_a_cwd_outside_the_config_dir_and_any_git_tree_fails_closed(self) -> None:
        elsewhere = Path(self._tmp.name).resolve() / "elsewhere"
        elsewhere.mkdir()
        self.worktree = elsewhere
        text = self.event("write-worktree-in-zone").replace(str(self.worktree) + "/apps", str(elsewhere) + "/apps")
        merged = {**self.env, "PAI_HARNESS_CONFIG": self.config}
        done = subprocess.run(["python3", str(self.hooks / "pre_tool_use.py")], input=text, text=True, capture_output=True, env=merged, cwd=elsewhere, timeout=60)
        out = json.loads(done.stdout)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn("is not a git work tree", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_the_state_dir_is_still_never_policed(self) -> None:
        self.assertIsNone(self.run_in("pre_tool_use.py", "write-delta-marker", self.worktree))


class WorktreeStopTest(WorktreeCase):
    def test_a_stop_with_an_out_of_zone_change_in_the_worktree_blocks(self) -> None:
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertEqual(out["decision"], "block")
        self.assertIn("packages/contracts/api.ts", out["reason"])
        self.assertIn("owned by acme-lead", out["reason"])

    def test_a_stop_with_only_in_zone_changes_passes(self) -> None:
        (self.worktree / "apps/acme-app/page.ts").write_text("two\n")
        self.assertIsNone(self.run_in("stop.py", "stop-worktree", self.worktree))

    def test_changes_in_the_config_checkout_are_diffed_too(self) -> None:
        # a shell write (sed -i, cp) from the worktree into the primary checkout leaves no trace for PreToolUse
        (self.project / "packages/contracts/api.ts").write_text("two\n")
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertEqual(out["decision"], "block")
        self.assertIn("packages/contracts/api.ts", out["reason"])

    def test_a_stop_outside_any_git_tree_fails_closed(self) -> None:
        elsewhere = Path(self._tmp.name).resolve() / "elsewhere"
        elsewhere.mkdir()
        self.worktree = elsewhere
        out = self.run_in("stop.py", "stop-worktree", elsewhere)
        self.assertEqual(out["decision"], "block")
        self.assertIn("not a git work tree", out["reason"])


class NestedWorktreeTest(WorktreeCase):
    NESTED = True

    def test_an_in_zone_write_is_allowed(self) -> None:
        self.assertIsNone(self.run_in("pre_tool_use.py", "write-worktree-in-zone", self.worktree))

    def test_an_out_of_zone_write_is_denied(self) -> None:
        self.assertEqual(self.run_in("pre_tool_use.py", "write-worktree-other-zone", self.worktree), deny(WorktreePreToolUseTest.CONTRACTS))

    def test_stop_diffs_the_worktree_not_the_primary_checkout(self) -> None:
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertEqual(out["decision"], "block")
        self.assertIn("packages/contracts/api.ts", out["reason"])
        self.assertNotIn(".claude/worktrees", out["reason"])  # the nested checkout is not itself reported as an untracked path

    def test_stop_with_only_in_zone_changes_passes(self) -> None:
        (self.worktree / "apps/acme-app/page.ts").write_text("two\n")
        self.assertIsNone(self.run_in("stop.py", "stop-worktree", self.worktree))


class NoRootTest(WorktreeCase):
    def setUp(self) -> None:
        super().setUp()
        self.elsewhere = Path(self._tmp.name).resolve() / "elsewhere"
        self.elsewhere.mkdir()

    def event_for(self, path: Path) -> str:
        return json.dumps({"session_id": "sess-1", "cwd": str(self.elsewhere), "hook_event_name": "PreToolUse", "tool_name": "Write",
                           "tool_input": {"file_path": str(path), "content": "x\n"}})

    def run_event(self, text: str) -> dict | None:
        merged = {**self.env, "PAI_HARNESS_CONFIG": self.config}
        done = subprocess.run(["python3", str(self.hooks / "pre_tool_use.py")], input=text, text=True, capture_output=True, env=merged, cwd=self.elsewhere, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    def test_the_delta_marker_can_still_be_written(self) -> None:
        self.assertIsNone(self.run_event(self.event_for(self.state / "deltas" / "acme-7.json")))

    def test_a_write_far_from_any_checkout_is_allowed(self) -> None:
        self.assertIsNone(self.run_event(self.event_for(Path(self._tmp.name).resolve() / "scratch" / "note.txt")))

    def test_a_write_under_cwd_or_the_config_checkout_is_refused(self) -> None:
        for path in (self.elsewhere / "apps/acme-app/page.ts", self.project / "packages/contracts/c.txt"):
            out = self.run_event(self.event_for(path))
            self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny", path)
            self.assertIn("not a git work tree", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_the_stop_block_names_the_real_cwd(self) -> None:
        text = self.event("stop-worktree").replace(str(self.worktree), str(self.elsewhere))
        merged = {**self.env, "PAI_HARNESS_CONFIG": self.config}
        done = subprocess.run(["python3", str(self.hooks / "stop.py")], input=text, text=True, capture_output=True, env=merged, cwd=self.elsewhere, timeout=60)
        self.assertNotIn("None", json.loads(done.stdout)["reason"])
