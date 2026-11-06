"""Fail-closed zone checks of the pai-harness hooks (ATE-1214 ROOT NO-GO): git failures at Stop, sibling worktrees, symlinks. Acme fixture only."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
from pathlib import Path

from tests.test_harness_hooks import HOOKS
from tests.test_harness_worktree_zone import WorktreeCase


class FailClosedCase(WorktreeCase):
    def fake_git(self, fail_when: str) -> str:
        """A PATH whose git fails (rc 1) when its arguments contain fail_when, else runs the real git. Returns the PATH."""
        real = shutil.which("git")
        bin_dir = Path(self._tmp.name) / "fakebin"
        bin_dir.mkdir(exist_ok=True)
        script = bin_dir / "git"
        script.write_text(f'#!/bin/sh\ncase " $* " in *" {fail_when}"*) echo "fatal: simulated failure" >&2; exit 1;; esac\nexec {real} "$@"\n')
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        return f"{bin_dir}:{os.environ['PATH']}"

    def second_worktree(self) -> Path:
        other = Path(self._tmp.name).resolve() / "worktree-b"
        self.git(self.project, "worktree", "add", "-q", "-b", "feature-b", str(other))
        return other

    def write_event(self, cwd: Path, target: Path) -> str:
        return json.dumps({"session_id": "sess-1", "cwd": str(cwd), "permission_mode": "bypassPermissions", "hook_event_name": "PreToolUse",
                           "tool_name": "Write", "tool_input": {"file_path": str(target), "content": "x\n"}})

    def pre(self, cwd: Path, target: Path, **env: str | None) -> dict | None:
        merged = {k: v for k, v in {**self.env, "PAI_HARNESS_CONFIG": self.config, **env}.items() if v is not None}
        done = subprocess.run(["python3", str(HOOKS / "pre_tool_use.py")], input=self.write_event(cwd, target), text=True, capture_output=True,
                              env=merged, cwd=cwd, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout) if done.stdout.strip() else None

    def decision(self, out: dict | None) -> str:
        return out["hookSpecificOutput"]["permissionDecision"] if out else "allow"


class StopGitFailureTest(FailClosedCase):
    def assertCannotCheck(self, out: dict | None, reason: str) -> None:
        self.assertIsNotNone(out)
        self.assertEqual(out["decision"], "block")
        self.assertIn("cannot be checked", out["reason"])
        self.assertIn(reason, out["reason"])

    def test_a_failing_git_status_blocks_stop(self) -> None:
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        out = self.run_in("stop.py", "stop-worktree", self.worktree, PATH=self.fake_git("status"))
        self.assertCannotCheck(out, "git status failed or timed out")

    def test_a_failing_git_diff_blocks_stop(self) -> None:
        out = self.run_in("stop.py", "stop-worktree", self.worktree, PATH=self.fake_git("diff"))
        self.assertCannotCheck(out, "git diff failed or timed out")

    def test_a_missing_base_blocks_stop_instead_of_falling_back_to_head(self) -> None:
        self.git(self.worktree, "-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "--allow-empty", "-m", "noop")
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        self.git(self.worktree, "add", "-A")
        self.git(self.worktree, "-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "-m", "committed out of zone")
        out = self.run_in("stop.py", "stop-worktree", self.worktree, PAI_HARNESS_BASE="no-such-ref")
        self.assertCannotCheck(out, "no base commit found")

    def test_a_committed_change_is_still_caught_with_a_valid_base(self) -> None:
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        self.git(self.worktree, "add", "-A")
        self.git(self.worktree, "-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "-m", "committed out of zone")
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertEqual(out["decision"], "block")
        self.assertIn("packages/contracts/api.ts", out["reason"])

    def test_a_symlink_resolving_outside_its_root_is_a_named_verdict(self) -> None:
        outside = Path(self._tmp.name).resolve() / "outside"
        outside.mkdir()
        (self.worktree / "apps/acme-app/link").symlink_to(outside)
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertCannotCheck(out, "resolves to")


class SiblingWorktreeTest(FailClosedCase):
    def test_a_write_from_worktree_a_into_out_of_zone_path_of_worktree_b_is_denied(self) -> None:
        other = self.second_worktree()
        out = self.pre(self.worktree, other / "packages/contracts/x.txt")
        self.assertEqual(self.decision(out), "deny")
        self.assertIn("belongs to zone 'contracts'", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_an_in_zone_path_of_worktree_b_is_allowed(self) -> None:
        other = self.second_worktree()
        self.assertEqual(self.decision(self.pre(self.worktree, other / "apps/acme-app/x.ts")), "allow")

    def test_the_primary_checkout_writing_into_a_non_nested_worktree_is_policed(self) -> None:
        other = self.second_worktree()
        self.assertEqual(self.decision(self.pre(self.project, other / "packages/contracts/x.txt")), "deny")
        self.assertEqual(self.decision(self.pre(self.project, other / "apps/acme-app/x.ts")), "allow")

    def test_a_lookup_failure_denies_for_a_writing_role(self) -> None:
        other = self.second_worktree()
        out = self.pre(self.worktree, other / "apps/acme-app/x.ts", PATH=self.fake_git("--git-common-dir"))
        self.assertEqual(self.decision(out), "deny")
        self.assertIn("cannot be checked", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_a_path_in_an_unrelated_repository_or_outside_any_is_left_alone(self) -> None:
        unrelated = Path(self._tmp.name).resolve() / "unrelated"
        unrelated.mkdir()
        self.git(unrelated, "init", "-q")
        self.assertEqual(self.decision(self.pre(self.worktree, unrelated / "packages/contracts/x.txt")), "allow")
        self.assertEqual(self.decision(self.pre(self.worktree, Path(self._tmp.name).resolve() / "scratch/x.txt")), "allow")


class ConfigSubdirectoryTest(FailClosedCase):
    def test_git_failing_only_for_the_config_dir_does_not_drop_the_subdirectory(self) -> None:
        sub = self.project / "svc"
        sub.mkdir()
        shutil.move(str(self.project / ".pai-harness.toml"), str(sub / ".pai-harness.toml"))
        (self.worktree / "svc").mkdir(exist_ok=True)
        bad = f"-C {sub}"
        out = self.pre(self.worktree, self.worktree / "svc/packages/contracts/x.txt", PAI_HARNESS_CONFIG=str(sub / ".pai-harness.toml"),
                       PATH=self.fake_git(bad))
        self.assertEqual(self.decision(out), "deny")
