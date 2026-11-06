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


class ExistingFileTest(FailClosedCase):
    """PreToolUse on files that already exist (Edit/MultiEdit): `git -C <file>` fails, so the lookup must start from the directory."""

    def test_an_existing_out_of_zone_file_of_a_sibling_worktree_is_judged_by_zone(self) -> None:
        other = self.second_worktree()
        out = self.pre(self.worktree, other / "packages/contracts/api.ts")
        self.assertEqual(self.decision(out), "deny")
        self.assertIn("belongs to zone 'contracts'", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_an_existing_in_zone_file_of_a_sibling_worktree_is_allowed(self) -> None:
        other = self.second_worktree()
        self.assertEqual(self.decision(self.pre(self.worktree, other / "apps/acme-app/page.ts")), "allow")

    def test_an_existing_file_of_an_unrelated_repository_is_left_alone(self) -> None:
        unrelated = Path(self._tmp.name).resolve() / "unrelated"
        (unrelated / "packages/contracts").mkdir(parents=True)
        (unrelated / "packages/contracts/api.ts").write_text("one\n")
        self.git(unrelated, "init", "-q")
        self.assertEqual(self.decision(self.pre(self.worktree, unrelated / "packages/contracts/api.ts")), "allow")


class ConfigSubdirectoryTest(FailClosedCase):
    """Pinned behavior: when git fails only for the config's directory, the subdirectory is kept (the root is worktree/svc), so the
    write is judged by zone, not refused wholesale."""

    def setUp(self) -> None:
        super().setUp()
        self.sub = self.project / "svc"
        self.sub.mkdir()
        shutil.move(str(self.project / ".pai-harness.toml"), str(self.sub / ".pai-harness.toml"))
        (self.worktree / "svc").mkdir(exist_ok=True)

    def pre_sub(self, target: Path, fail: str) -> dict | None:
        return self.pre(self.worktree, target, PAI_HARNESS_CONFIG=str(self.sub / ".pai-harness.toml"), PATH=self.fake_git(fail))

    def test_an_in_zone_write_is_allowed(self) -> None:
        self.assertEqual(self.decision(self.pre_sub(self.worktree / "svc/apps/acme-app/x.ts", f"-C {self.sub}")), "allow")

    def test_an_out_of_zone_write_is_denied_by_zone(self) -> None:
        out = self.pre_sub(self.worktree / "svc/packages/contracts/x.txt", f"-C {self.sub}")
        self.assertEqual(self.decision(out), "deny")
        self.assertIn("belongs to zone 'contracts'", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_git_failing_for_the_config_dir_and_every_ancestor_denies_with_its_own_reason(self) -> None:
        out = self.pre_sub(self.worktree / "svc/apps/acme-app/x.ts", f"-C {self.sub}")  # baseline allow above
        self.assertEqual(self.decision(out), "allow")
        real = shutil.which("git")
        bin_dir = Path(self._tmp.name) / "failbin"
        bin_dir.mkdir()
        (bin_dir / "git").write_text(f'#!/bin/sh\ncase "$2" in {self.project}*) exit 1;; esac\nexec {real} "$@"\n')
        (bin_dir / "git").chmod(0o755)
        out = self.pre(self.worktree, self.worktree / "svc/apps/acme-app/x.ts", PAI_HARNESS_CONFIG=str(self.sub / ".pai-harness.toml"),
                       PATH=f"{bin_dir}:{os.environ['PATH']}")
        self.assertEqual(self.decision(out), "deny")
        self.assertIn("could not locate the harness config's directory", out["hookSpecificOutput"]["permissionDecisionReason"])


class SymlinkTest(FailClosedCase):
    def test_a_legitimate_in_zone_link_pointing_outside_the_root_passes_stop(self) -> None:
        outside = Path(self._tmp.name).resolve() / "shared"
        outside.mkdir()
        (self.worktree / "apps/acme-app/shared").symlink_to(outside)
        (self.worktree / "apps/acme-app/dangling").symlink_to("/nonexistent/target")
        self.assertIsNone(self.run_in("stop.py", "stop-worktree", self.worktree))

    def test_a_link_in_an_out_of_zone_directory_is_still_out_of_zone(self) -> None:
        outside = Path(self._tmp.name).resolve() / "shared"
        outside.mkdir()
        (self.worktree / "packages/contracts/link").symlink_to(outside)
        out = self.run_in("stop.py", "stop-worktree", self.worktree)
        self.assertEqual(out["decision"], "block")
        self.assertIn("packages/contracts/link", out["reason"])


class FourthStopTest(FailClosedCase):
    def test_a_cannot_check_reason_keeps_blocking_past_the_bound_but_an_out_of_zone_one_does_not(self) -> None:
        env = {"PATH": self.fake_git("status")}
        for _ in range(6):
            out = self.run_in("stop.py", "stop-worktree", self.worktree, **env)
            self.assertEqual(out["decision"], "block")
            self.assertIn("cannot be checked", out["reason"])
        (self.state / "deltas" / "acme-7.blocks").unlink(missing_ok=True)
        (self.worktree / "packages/contracts/api.ts").write_text("two\n")
        for _ in range(3):
            self.assertEqual(self.run_in("stop.py", "stop-worktree", self.worktree)["decision"], "block")
        self.assertIsNone(self.run_in("stop.py", "stop-worktree", self.worktree))  # 4th: the bound lets plain out-of-zone through
