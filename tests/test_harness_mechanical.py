"""The mechanical lane: the launcher profile (closed brief, Haiku, empty strict MCP, four tools, json output) and the diff-scope verifier."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import launch as launcher  # noqa: E402
import mechanical_scope as scope  # noqa: E402
import verify_mechanical as vm  # noqa: E402

RESULT = FIXTURES / "mechanical_result.json"
FILES = ["src/cart.py", "src/totals.py"]
INSTRUCTION = "Rename the function calc_total to compute_total in the listed files."


def git(repo: Path, *argv: str) -> str:
    done = subprocess.run(["git", "-C", str(repo), "-c", "user.name=Acme Dev", "-c", "user.email=dev@acme.example.com", "-c", "commit.gpgsign=false", *argv],
                          capture_output=True, text=True, check=True)
    return done.stdout.strip()


class MechanicalCase(HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        self.env["PAI_HARNESS_LANE_ENV"] = "FAKE_CLAUDE_FIXTURE,FAKE_CLAUDE_EXIT,FAKE_CLAUDE_LOG"  # the lane env is an allowlist: let the fake claude see its own switches
        self.repo = self.tmp / "repo"
        (self.repo / "src").mkdir(parents=True)
        for name in (*FILES, "src/other.py", "README.md"):
            (self.repo / name).write_text(f"# {name}\ndef calc_total():\n    return 1\n")
        (self.repo / ".gitignore").write_text("*.env\nbuild/\nnode_modules/\n__pycache__/\n.pytest_cache/\n")
        (self.repo / "node_modules/pkg").mkdir(parents=True)
        (self.repo / "node_modules/pkg/index.js").write_text("module.exports = 1\n")
        (self.repo / "prod.env").write_text("SECRET=1\n")  # ignored and already there when the lane starts: not the run's change
        git(self.repo, "init", "-q")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")

    def lane(self, *extra: str, issue: str = "ACME-7", files: list[str] | None = None, exit_code: int = 0, **env: str) -> subprocess.CompletedProcess:
        return self.run_script("launch.sh", issue, "--profile", "mechanical", "--cwd", str(self.repo), "--instruction", INSTRUCTION,
                               "--files", *(files or FILES), *extra, FAKE_CLAUDE_FIXTURE=str(RESULT), FAKE_CLAUDE_EXIT=str(exit_code), **env)

    def argv(self) -> list[str]:
        return json.loads((self.tmp / "claude.json").read_text())["argv"]

    def verify(self, *extra: str, issue: str = "ACME-7") -> subprocess.CompletedProcess:
        return self.run_script("verify-mechanical.sh", issue, "--check", "true", *extra)


class ProfileTest(MechanicalCase):
    def test_the_command_is_the_guarded_lane(self) -> None:
        done = self.lane()
        self.assertEqual(done.returncode, 0, done.stderr)
        argv = self.argv()
        self.assertEqual(argv[:5], ["-p", "--output-format", "json", "--model", "haiku"])
        self.assertNotIn("--verbose", argv)
        self.assertIn("--strict-mcp-config", argv)
        self.assertEqual(json.loads(Path(argv[argv.index("--mcp-config") + 1]).read_text()), {"mcpServers": {}})
        self.assertEqual(argv[argv.index("--tools") + 1], "Read,Edit,Grep,Glob")
        root = str(self.repo.resolve())
        allowed = argv[argv.index("--allowed-tools") + 1:argv.index("--allowed-tools") + 5]
        self.assertEqual(allowed, [f"Read(/{root}/**)", f"Edit(/{root}/**)", "Grep", "Glob"])  # scoped to the run directory, not bare tool names
        denied = argv[argv.index("--disallowed-tools") + 1:]
        for rule in (f"Edit(/{root}/.git/**)", f"Edit(/{root}/.git)", f"Edit(/{self.state.resolve()}/**)", f"Read(/{self.state.resolve()}/**)",
                     f"Read(/{Path('~/.ssh').expanduser()}/**)", f"Read(/{Path('~/.config/pai-harness').expanduser()}/**)"):
            self.assertIn(rule, denied)
        self.assertFalse([r for r in denied if not r.startswith(("Edit(", "Read("))])
        self.assertEqual((argv[argv.index("--max-turns") + 1], argv[argv.index("--max-budget-usd") + 1]), ("12", "0.25"))
        self.assertFalse([a for a in argv if "skip-permissions" in a or a == "bypassPermissions" or a == "Bash"])

    def test_the_mcp_config_is_empty_even_when_a_pai_endpoint_is_configured(self) -> None:
        done = self.lane(PAI_HARNESS_CONFIG=str(FIXTURES / "acme-pai.pai-harness.toml"))
        self.assertEqual(done.returncode, 0, done.stderr)
        argv = self.argv()
        self.assertEqual(json.loads(Path(argv[argv.index("--mcp-config") + 1]).read_text()), {"mcpServers": {}})
        self.assertNotIn("headersHelper", Path(argv[argv.index("--mcp-config") + 1]).read_text())

    def test_the_brief_is_closed_and_the_record_carries_what_the_verifier_needs(self) -> None:
        self.lane()
        sent = json.loads((self.tmp / "claude.json").read_text())["prompt"]
        self.assertIn(INSTRUCTION, sent)
        self.assertIn("- src/cart.py\n- src/totals.py", sent)
        self.assertNotIn("Knowledge target", sent)
        record = self.record("ACME-7")
        self.assertEqual((record["state"], record["profile"], record["files"], record["role"], record["model"]),
                         ("done", "mechanical", FILES, "mechanical", "haiku"))
        self.assertEqual((record["cost_usd"], record["turns"], record["base"]), (0.004, 3, git(self.repo, "rev-parse", "HEAD")))
        self.assertEqual(record["cwd"], str(self.repo.resolve()))

    def test_sonnet_is_the_opt_in_and_other_models_are_refused(self) -> None:
        self.lane("--model", "sonnet")
        self.assertEqual(self.argv()[4], "sonnet")
        done = self.lane("--model", "opus", issue="ACME-8")
        self.assertEqual(done.returncode, 2)
        self.assertIn("runs haiku or sonnet, not opus", done.stderr)

    def test_a_json_array_output_is_read_like_the_single_object(self) -> None:
        frames = self.tmp / "array.json"
        frames.write_text(json.dumps([{"type": "system", "subtype": "init"}, json.loads(RESULT.read_text())]) + "\n")
        done = self.run_script("launch.sh", "ACME-7", "--profile", "mechanical", "--cwd", str(self.repo), "--instruction", INSTRUCTION, "--files", *FILES,
                               FAKE_CLAUDE_FIXTURE=str(frames))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.record("ACME-7")["state"], "done")

    def test_a_failed_run_is_recorded_failed(self) -> None:
        self.assertEqual(self.lane(exit_code=1).returncode, 1)
        self.assertEqual(self.record("ACME-7")["state"], "failed")

    def test_the_brief_must_be_closed(self) -> None:
        cases = [
            (["--instruction", "x"], "needs --files"),
            (["--files", "a.py"], "needs --files"),
            (["--instruction", "x", "--files", "src/*.py"], "literal relative path"),
            (["--instruction", "x", "--files", "/etc/passwd"], "literal relative path"),
            (["--instruction", "x", "--files", "../up.py"], "literal relative path"),
            (["--instruction", "x", "--files", ".git/config"], "points into .git"),
            (["--instruction", "x", "--files", "a.py", "--prompt", "also this"], "closed brief"),
            (["--instruction", "x", "--files", "a.py", "--allowed-tools", "Bash"], "closed brief"),
            (["--instruction", "x", "--files", "a.py", "--role", "lead"], "runs the mechanical role"),
        ]
        for extra, message in cases:
            done = self.run_script("launch.sh", "ACME-7", "--profile", "mechanical", "--cwd", str(self.repo), *extra)
            self.assertEqual(done.returncode, 2, extra)
            self.assertIn(message, done.stderr, extra)
        self.assertFalse((self.state / "runs" / "ACME-7.state.json").exists())

    def test_files_without_the_profile_are_refused(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt", "x", "--files", "a.py")
        self.assertEqual(done.returncode, 2)

    def test_a_dirty_worktree_is_refused(self) -> None:
        (self.repo / "scratch.txt").write_text("mine\n")
        done = self.lane()
        self.assertEqual(done.returncode, 1)
        self.assertIn("needs a clean worktree", done.stderr)
        self.assertFalse((self.tmp / "claude.json").exists())

    def test_outside_a_worktree_is_refused(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        done = self.run_script("launch.sh", "ACME-7", "--profile", "mechanical", "--cwd", str(plain), "--instruction", "x", "--files", "a.py")
        self.assertEqual(done.returncode, 1)
        self.assertIn("must run inside a git worktree", done.stderr)

    def test_the_dry_run_shows_the_plan_and_writes_nothing(self) -> None:
        done = self.lane("--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        command = json.loads(done.stdout)["command"]
        self.assertIn("--strict-mcp-config", command)
        self.assertEqual(command[command.index("--output-format") + 1], "json")
        self.assertFalse((self.state / "runs").exists())

    def test_the_mechanical_caps_can_be_raised_in_the_config(self) -> None:
        config = self.tmp / "caps.toml"
        config.write_text((FIXTURES / "acme.pai-harness.toml").read_text().rstrip("\n") + "\n\n[role_limits.mechanical]\nmax_turns = 20\nmax_budget_usd = 0.5\n")
        self.lane(PAI_HARNESS_CONFIG=str(config))
        argv = self.argv()
        self.assertEqual((argv[argv.index("--max-turns") + 1], argv[argv.index("--max-budget-usd") + 1]), ("20", "0.5"))


class VerifyTest(MechanicalCase):
    def started(self, **kwargs: object) -> None:
        done = self.lane(**kwargs)  # type: ignore[arg-type]
        self.assertEqual(done.returncode, 0, done.stderr)

    def edit(self, name: str, text: str = "def compute_total():\n    return 1\n") -> None:
        (self.repo / name).write_text(text)

    def test_listed_files_only_and_passing_checks_pass(self) -> None:
        self.started()
        self.edit("src/cart.py")
        self.edit("src/totals.py")
        done = self.verify()
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        result = json.loads(done.stdout)
        self.assertEqual((result["verdict"], result["changed"], result["outside"], result["discarded"]), ("pass", FILES, [], []))
        self.assertEqual(result["checks"][0]["exit_code"], 0)
        self.assertIn("RESULT ACME-7 done: check pass", done.stderr)
        self.assertEqual(self.record("ACME-7")["verify"]["verdict"], "pass")
        self.assertTrue((self.repo / "src/cart.py").read_text().startswith("def compute_total"))  # a pass keeps the work

    def test_a_change_outside_the_list_discards_the_whole_run(self) -> None:
        self.started()
        self.edit("src/cart.py")
        self.edit("src/other.py")
        (self.repo / "src/new.py").write_text("print('x')\n")
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertEqual(result["verdict"], "discard")
        self.assertEqual(result["outside"], ["src/new.py", "src/other.py"])
        self.assertIn("changed outside the listed files: src/new.py, src/other.py", result["reasons"][0])
        self.assertEqual(result["checks"], [])  # no check runs on a stray diff
        self.assertIn("BLOCKER ACME-7: mechanical run discarded", done.stderr)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")  # restored, the untracked file removed
        self.assertFalse((self.repo / "src/new.py").exists())

    def test_a_staged_change_and_a_deletion_outside_the_list_are_seen(self) -> None:
        self.started()
        self.edit("src/cart.py")
        (self.repo / "README.md").unlink()
        self.edit("src/other.py")
        git(self.repo, "add", "src/other.py")
        result = json.loads(self.verify().stdout)
        self.assertEqual(result["outside"], ["README.md", "src/other.py"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_a_failing_check_discards_the_run(self) -> None:
        self.started()
        self.edit("src/cart.py")
        done = self.run_script("verify-mechanical.sh", "ACME-7", "--check", "echo broken >&2; exit 3")
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertIn("check failed (exit 3)", result["reasons"][0])
        self.assertEqual(result["checks"][0]["output_tail"], "broken")
        self.assertEqual(result["discarded"], ["src/cart.py"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_gates_from_the_config_are_checks(self) -> None:
        self.started()
        self.edit("src/cart.py")
        config = self.tmp / "gates.toml"
        config.write_text((FIXTURES / "acme.pai-harness.toml").read_text().replace('lint = ["true", "true"]', 'lint = ["true", "exit 4"]'))
        done = self.run_script("verify-mechanical.sh", "ACME-7", "--gate", "lint", PAI_HARNESS_CONFIG=str(config))
        self.assertEqual(done.returncode, 1)
        self.assertEqual([c["exit_code"] for c in json.loads(done.stdout)["checks"]], [0, 4])

    def test_an_empty_diff_is_not_a_pass(self) -> None:
        self.started()
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["reasons"], ["no listed file changed"])

    def test_a_run_that_did_not_finish_done_is_discarded(self) -> None:
        self.assertEqual(self.lane(exit_code=1).returncode, 1)
        self.edit("src/cart.py")
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        self.assertIn("the run is failed", json.loads(done.stdout)["reasons"][0])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_keep_and_dry_run_leave_the_changes(self) -> None:
        self.started()
        self.edit("src/other.py")
        for flag in ("--keep", "--dry-run"):
            self.assertEqual(self.verify(flag).returncode, 1, flag)
            self.assertEqual(git(self.repo, "status", "--porcelain"), "M src/other.py", flag)
        self.assertEqual(self.record("ACME-7")["verify"]["verdict"], "discard")  # --keep records the verdict; the dry run after it changes nothing

    def test_a_moved_head_is_reported_and_never_undone(self) -> None:
        self.started()
        self.edit("src/cart.py")
        git(self.repo, "commit", "-q", "-am", "sneaky")
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertIn("HEAD moved", result["reasons"][0])
        self.assertEqual(result["discarded"], [])
        self.assertEqual(git(self.repo, "log", "--oneline").count("\n"), 1)

    def test_checks_are_required(self) -> None:
        self.started()
        done = self.run_script("verify-mechanical.sh", "ACME-7")
        self.assertEqual(done.returncode, 2)
        self.assertIn("never passed without them", done.stderr)

    def test_only_mechanical_runs_with_a_record_can_be_verified(self) -> None:
        self.assertEqual(self.verify().returncode, 2)  # no run recorded
        self.assertEqual(self.launch("ACME-7", "success", 0).returncode, 0)
        done = self.verify()
        self.assertEqual(done.returncode, 2)
        self.assertIn("not a mechanical-lane run", done.stderr)


class ScopeTest(MechanicalCase):
    """The review round: ignored files, subdirectories, git failure, checks that write, literal paths, dry run."""

    def started(self, **kwargs: object) -> None:
        done = self.lane(**kwargs)  # type: ignore[arg-type]
        self.assertEqual(done.returncode, 0, done.stderr)

    def edit(self, name: str, text: str = "changed\n") -> None:
        (self.repo / name).write_text(text)

    def test_an_ignored_file_new_or_changed_is_outside_and_a_preexisting_one_is_not(self) -> None:
        self.started()
        self.edit("src/cart.py")
        self.assertEqual(json.loads(self.verify().stdout)["verdict"], "pass")  # prod.env was there before the run and is untouched
        self.edit("prod.env", "SECRET=2\n")
        (self.repo / "build").mkdir()
        (self.repo / "build/out.js").write_text("x\n")
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertEqual(result["outside"], ["build/out.js", "prod.env"])
        self.assertFalse((self.repo / "build/out.js").exists())  # the new ignored file is removed
        self.assertIn("prod.env: an ignored file that existed before the run", " ".join(result["reasons"]))  # the old one cannot be restored from git: said, not hidden

    def test_a_subdirectory_cwd_uses_repo_root_paths_everywhere(self) -> None:
        sub = self.repo / "sub"
        sub.mkdir()
        (sub / "a.txt").write_text("a\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "sub")
        done = self.run_script("launch.sh", "ACME-7", "--profile", "mechanical", "--cwd", str(sub), "--instruction", INSTRUCTION, "--files", "a.txt",
                               FAKE_CLAUDE_FIXTURE=str(RESULT))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.record("ACME-7")["files"], ["sub/a.txt"])
        (sub / "a.txt").write_text("changed\n")
        self.assertEqual(json.loads(self.verify().stdout)["verdict"], "pass")
        self.edit("src/other.py")  # outside the subtree: still seen
        (self.repo / "untracked-elsewhere.txt").write_text("x\n")
        bad = self.verify()
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)["outside"], ["src/other.py", "untracked-elsewhere.txt"])
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")  # the whole run is undone, from the root-relative paths

    def test_a_literal_bracket_path_is_listed_checked_and_restored(self) -> None:
        page = "app/[slug]/page.tsx"
        (self.repo / "app/[slug]").mkdir(parents=True)
        (self.repo / page).write_text("x\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "next")
        self.started(files=[page, "src/cart.py"])
        self.edit(page)
        self.assertEqual(json.loads(self.verify().stdout)["verdict"], "pass")
        self.edit("src/other.py")
        self.assertEqual(self.verify().returncode, 1)
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")  # restored through a literal pathspec, not a glob

    def test_control_characters_in_a_path_are_refused(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--profile", "mechanical", "--cwd", str(self.repo), "--instruction", "x", "--files", "a\nb.py")
        self.assertEqual(done.returncode, 2)
        self.assertIn("control character", done.stderr)

    def test_a_check_that_writes_outside_the_list_discards_the_run(self) -> None:
        self.started()
        self.edit("src/cart.py")
        done = self.run_script("verify-mechanical.sh", "ACME-7", "--check", "echo snapshot > generated.txt; echo x > build-cache.env")
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertEqual(result["verdict"], "discard")
        self.assertEqual(result["outside"], ["build-cache.env", "generated.txt"])
        self.assertIn("after the checks", " ".join(result["reasons"]))
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")
        self.assertFalse((self.repo / "build-cache.env").exists())

    def test_a_git_failure_writes_a_discard_blocker_and_clears_an_earlier_pass(self) -> None:
        self.started()
        self.edit("src/cart.py")
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(self.record("ACME-7")["verify"]["verdict"], "pass")
        shutil.rmtree(self.repo / ".git")
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        self.assertIn("BLOCKER ACME-7", done.stderr)
        verify = self.record("ACME-7")["verify"]
        self.assertEqual(verify["verdict"], "discard")
        self.assertIn("fail closed", verify["reasons"][0])
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 1)  # the pass is gone, and so is the tree it described

    def test_a_missing_baseline_fails_closed(self) -> None:
        self.started()
        self.edit("src/cart.py")
        Path(self.record("ACME-7")["ignored_baseline"]).unlink()
        done = self.verify()
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.record("ACME-7")["verify"]["verdict"], "discard")
        self.assertIn("baseline", done.stdout)

    def test_discard_never_raises_when_git_restore_fails(self) -> None:
        self.started()
        self.edit("src/other.py")
        real = scope.git

        def broken(root: str, *argv: str) -> subprocess.CompletedProcess:
            if argv[0] == "restore":
                raise scope.ScopeError("git restore failed: timeout")
            return real(root, *argv)
        with mock.patch.object(scope, "git", broken):
            done, problems = vm.discard(str(self.repo), git(self.repo, "rev-parse", "HEAD"), ["src/other.py"], {})
        self.assertEqual((done, len(problems)), ([], 1))
        self.assertIn("timeout", problems[0])
        with mock.patch.object(scope, "git", side_effect=OSError("disk gone")):  # any other failure is reported too, never raised
            done, problems = vm.discard(str(self.repo), "0" * 40, ["src/other.py"], {})
        self.assertEqual((done, len(problems)), ([], 1))

    def test_the_dry_run_is_never_a_pass(self) -> None:
        self.started()
        self.edit("src/cart.py")
        done = self.verify("--dry-run")
        self.assertEqual(done.returncode, 1)
        result = json.loads(done.stdout)
        self.assertEqual((result["verdict"], result["dry_run"], result["checks"]), ("unverified", True, []))
        self.assertIn("not a verified pass", done.stderr)
        self.assertNotIn("verify", self.record("ACME-7"))
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 1)


class LaneEnvironmentTest(MechanicalCase):
    def test_the_child_gets_an_allowlist_not_the_whole_environment(self) -> None:
        done = self.lane(PAI_HARNESS_TOKEN_FILE="/x/token", PAI_HARNESS_TOKEN_SCOPE="write", AWS_SECRET_ACCESS_KEY="s", SSH_AUTH_SOCK="/s", GITHUB_TOKEN="g",
                         ANTHROPIC_API_KEY="k")
        self.assertEqual(done.returncode, 0, done.stderr)
        seen = set(json.loads((self.tmp / "claude.json").read_text())["env"])
        self.assertTrue({"PATH", "HOME", "ANTHROPIC_API_KEY"} <= seen)
        self.assertFalse({"PAI_HARNESS_TOKEN_FILE", "PAI_HARNESS_TOKEN_SCOPE", "AWS_SECRET_ACCESS_KEY", "SSH_AUTH_SOCK", "GITHUB_TOKEN", "PAI_HARNESS_ROLE",
                          "PAI_HARNESS_CONFIG", "PAI_HARNESS_STATE_DIR"} & seen)

    def test_the_real_hooks_are_inert_in_the_lane_environment(self) -> None:
        hooks = Path(launcher.__file__).resolve().parent.parent / "hooks"
        lane_env = {**launcher.lane_env(), "PAI_HARNESS_CONFIG": self.env["PAI_HARNESS_CONFIG"], "PAI_HARNESS_STATE_DIR": str(self.state)}
        events = {"stop.py": {"session_id": "s1", "cwd": str(self.repo)},
                  "pre_tool_use.py": {"tool_name": "Edit", "tool_input": {"file_path": str(self.repo / "src/other.py")}, "cwd": str(self.repo), "session_id": "s1"}}
        for hook, event in events.items():
            done = subprocess.run([sys.executable, str(hooks / hook)], input=json.dumps(event), text=True, capture_output=True, env=lane_env, timeout=30)
            self.assertEqual((done.returncode, done.stdout.strip()), (0, ""), (hook, done.stderr))
        # Control: with the role set the Stop hook would block this lane (no knowledge delta, no mechanical zone), which is why the lane runs without it.
        blocked = subprocess.run([sys.executable, str(hooks / "stop.py")], input=json.dumps(events["stop.py"]), text=True, capture_output=True,
                                 env={**lane_env, "PAI_HARNESS_ROLE": "mechanical", "PAI_HARNESS_AGENT": "ACME-7"}, timeout=30)
        self.assertIn("block", blocked.stdout)

    def test_the_brief_is_exactly_the_closed_text_and_tokens_are_accounted(self) -> None:
        self.assertEqual(self.lane().returncode, 0)
        self.assertEqual(json.loads((self.tmp / "claude.json").read_text())["prompt"], launcher.closed_brief(INSTRUCTION, FILES))
        record = self.record("ACME-7")
        self.assertEqual((record["input_tokens"], record["cache_write_tokens"], record["cache_read_tokens"], record["output_tokens"]), (120, 300, 4000, 55))
        self.assertEqual(record["cost_usd"], 0.004)

    def test_the_empty_strict_mcp_config_is_always_passed(self) -> None:
        for extra in ((), ("--model", "sonnet")):
            self.assertEqual(self.lane(*extra, PAI_HARNESS_CONFIG=str(FIXTURES / "acme-pai.pai-harness.toml")).returncode, 0)
            argv = self.argv()
            self.assertEqual(argv.count("--strict-mcp-config"), 1)
            self.assertEqual(json.loads(Path(argv[argv.index("--mcp-config") + 1]).read_text()), {"mcpServers": {}})
            git(self.repo, "checkout", "-q", "--", ".")


class DeltaTwoTest(MechanicalCase):
    """Review round two."""

    def started(self, **kwargs: object) -> None:
        done = self.lane(**kwargs)  # type: ignore[arg-type]
        self.assertEqual(done.returncode, 0, done.stderr)

    def edit(self, name: str = "src/cart.py", text: str = "changed\n") -> None:
        (self.repo / name).write_text(text)

    def test_checks_may_write_caches_but_not_a_sensitive_ignored_name(self) -> None:
        self.started()
        self.edit()
        done = self.run_script("verify-mechanical.sh", "ACME-7", "--check",
                               "mkdir -p __pycache__ .pytest_cache build && echo x > __pycache__/a.pyc && echo y > build/out.js && echo z > node_modules/pkg/cache.json")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(json.loads(done.stdout)["verdict"], "pass")
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 0)  # the same tolerant view at close
        git(self.repo, "checkout", "-q", "--", ".")
        self.started(issue="ACME-8")
        self.edit()
        bad = self.run_script("verify-mechanical.sh", "ACME-8", "--check", "echo K=1 > leaked.env")
        self.assertEqual(bad.returncode, 1)
        self.assertEqual(json.loads(bad.stdout)["outside"], ["leaked.env"])
        self.assertFalse((self.repo / "leaked.env").exists())

    def test_before_the_checks_a_dependency_directory_change_is_still_seen(self) -> None:
        self.started()
        self.edit()
        self.assertEqual(json.loads(self.verify().stdout)["verdict"], "pass")  # the pre-existing node_modules is untouched
        (self.repo / "node_modules/pkg/evil.js").write_text("x\n")
        result = json.loads(self.verify().stdout)
        self.assertEqual(result["outside"], ["node_modules/pkg/"])
        self.assertIn("cannot be restored", " ".join(result["reasons"]))

    def test_committing_the_verified_work_still_closes_but_other_commits_do_not(self) -> None:
        self.started()
        self.edit()
        self.assertEqual(self.verify().returncode, 0)
        git(self.repo, "commit", "-q", "-am", "the work")
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 0)
        self.edit("src/other.py")
        git(self.repo, "commit", "-q", "-am", "more")
        done = self.run_script("task-done.sh", "ACME-7")
        self.assertEqual(done.returncode, 1)
        self.assertIn("changed after the verdict", done.stderr)

    def test_the_sample_decision_does_not_depend_on_the_cli_and_a_new_run_gets_a_new_slot(self) -> None:
        for n in range(1, 6):
            git(self.repo, "checkout", "-q", "--", ".")
            self.started(issue=f"ACME-{n}")
            self.edit()
            result = json.loads(self.verify(issue=f"ACME-{n}").stdout)
        self.assertTrue(result["sample_review"])
        for value in ("2", "3", "4", "1"):
            self.assertTrue(json.loads(self.verify("--sample-every", value, issue="ACME-5").stdout)["sample_review"], value)  # slot 5 stays sampled
        git(self.repo, "checkout", "-q", "--", ".")  # the same issue relaunched is a new run with a new slot
        self.started(issue="ACME-5")
        self.edit()
        again = json.loads(self.verify(issue="ACME-5").stdout)
        self.assertEqual(again["sample_slot"], 6)
        self.assertFalse(again["sample_review"])

    def test_a_failed_post_check_measure_discards_from_a_fresh_listing(self) -> None:
        self.started()
        self.edit()
        calls = {"n": 0}
        real = scope.ignored_state

        def second_fails(root: str) -> dict:
            calls["n"] += 1
            if calls["n"] == 2:
                (self.repo / "stray.txt").write_text("written by the check\n")
                raise scope.ScopeError("timeout")
            return real(root)
        env = {k: self.env[k] for k in ("PAI_HARNESS_CONFIG", "PAI_HARNESS_STATE_DIR")}
        with mock.patch.dict(os.environ, env), mock.patch.object(scope, "ignored_state", second_fails), mock.patch("builtins.print"):
            code = vm.main(["ACME-7", "--check", "true"])
        self.assertEqual(code, 1)
        verify = self.record("ACME-7")["verify"]
        self.assertEqual(verify["verdict"], "discard")
        self.assertIn("scope after the checks", verify["reasons"][0])
        self.assertFalse((self.repo / "stray.txt").exists())  # removed although the second snapshot never completed
        self.assertEqual(git(self.repo, "status", "--porcelain"), "")

    def test_the_verifier_ignores_the_repo_config_that_would_run_code(self) -> None:
        self.started()
        self.edit()
        marker = self.tmp / "ran"
        git(self.repo, "config", "core.fsmonitor", f"touch {marker}; echo")
        git(self.repo, "config", "core.pager", f"touch {marker}")
        self.assertEqual(self.verify().returncode, 0)
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 0)
        self.assertFalse(marker.exists())

    def test_the_default_environment_reaches_the_api_and_credentials_are_not_opted_in_silently(self) -> None:
        env = {"HTTPS_PROXY": "http://p:3128", "NODE_EXTRA_CA_CERTS": "/ca.pem", "CLAUDE_CODE_USE_BEDROCK": "1", "AWS_REGION": "us-east-1",
               "AWS_ACCESS_KEY_ID": "id", "GOOGLE_APPLICATION_CREDENTIALS": "/g.json", "MY_TOKEN": "t", "PAI_HARNESS_TOKEN_FILE": "/t", "GITHUB_TOKEN": "g"}
        with mock.patch.dict(os.environ, {**env, "PAI_HARNESS_LANE_ENV": "MY_TOKEN,PAI_HARNESS_TOKEN_FILE,HARMLESS", "HARMLESS": "1"}), mock.patch("builtins.print") as printed:
            lane = launcher.lane_env()
        self.assertTrue({"HTTPS_PROXY", "NODE_EXTRA_CA_CERTS", "CLAUDE_CODE_USE_BEDROCK", "AWS_REGION", "AWS_ACCESS_KEY_ID", "HARMLESS"} <= set(lane))
        self.assertFalse({"GOOGLE_APPLICATION_CREDENTIALS", "MY_TOKEN", "PAI_HARNESS_TOKEN_FILE", "GITHUB_TOKEN"} & set(lane))  # Vertex not selected; secrets refused
        self.assertEqual(len(printed.call_args_list), 2)
        with mock.patch.dict(os.environ, {"PAI_HARNESS_LANE_ENV": "MY_TOKEN", "MY_TOKEN": "t", "PAI_HARNESS_LANE_ENV_ALLOW_SECRETS": "1"}):
            self.assertIn("MY_TOKEN", launcher.lane_env())

    @unittest.skipUnless(os.environ.get("PAI_HARNESS_LIVE_CLAUDE") == "1", "set PAI_HARNESS_LIVE_CLAUDE=1 to run the installed claude (a real, tiny Haiku call)")
    def test_live_an_absolute_edit_outside_the_run_directory_is_denied(self) -> None:
        outside = self.tmp / "outside.txt"
        outside.write_text("secret\n")
        args = launcher.argparse.Namespace(cwd=str(self.repo), role="mechanical", profile="mechanical", model="haiku", resume_run=False, allowed_tools=None)
        config, _ = launcher.lib.load_config(self.env["PAI_HARNESS_CONFIG"])
        allow, deny = launcher.lane_permissions(args, config)
        done = subprocess.run(["claude", "-p", "--model", "haiku", "--max-turns", "6", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}', "--tools", "Read,Edit,Grep,Glob",
                               "--allowed-tools", *allow, "--disallowed-tools", *deny], input=f"Edit {outside} replacing secret with leaked, then Edit {self.repo}/.git/config appending a line.",
                              text=True, capture_output=True, timeout=170, cwd=self.repo)
        self.assertEqual(outside.read_text(), "secret\n", done.stdout)
        self.assertNotIn("leaked", (self.repo / ".git/config").read_text())


class SamplerTest(MechanicalCase):
    def passing_run(self, issue: str) -> dict:
        git(self.repo, "checkout", "-q", "--", ".")
        self.assertEqual(self.lane(issue=issue).returncode, 0)
        (self.repo / "src/cart.py").write_text("changed\n")
        done = self.verify(issue=issue)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return json.loads(done.stdout)

    def test_exactly_every_fifth_pass_is_sampled_and_a_reverify_keeps_its_slot(self) -> None:
        picks = [self.passing_run(f"ACME-{n}")["sample_review"] for n in range(1, 11)]
        self.assertEqual(picks, [False] * 4 + [True] + [False] * 4 + [True])
        again = self.verify(issue="ACME-5")  # the same issue verified again is the same slot: it cannot be re-rolled
        self.assertTrue(json.loads(again.stdout)["sample_review"])

    def test_the_rate_can_be_made_stricter_never_looser(self) -> None:
        self.lane()
        (self.repo / "src/cart.py").write_text("changed\n")
        for value in ("1000000", "6", "0"):
            done = self.verify("--sample-every", value)
            self.assertEqual(done.returncode, 2, value)
            self.assertIn("never looser", done.stderr)
        self.assertTrue(json.loads(self.verify("--sample-every", "1").stdout)["sample_review"])


class CloseTest(MechanicalCase):
    def verify_run(self, issue: str = "ACME-7", check: str = "true") -> subprocess.CompletedProcess:
        return self.run_script("verify-mechanical.sh", issue, "--check", check)

    def edited(self, issue: str = "ACME-7") -> dict:
        self.assertEqual(self.lane(issue=issue).returncode, 0)
        (self.repo / "src/cart.py").write_text("changed\n")
        done = self.verify_run(issue)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        return json.loads(done.stdout)

    def test_an_unverified_run_cannot_be_closed(self) -> None:
        self.assertEqual(self.lane().returncode, 0)
        done = self.run_script("task-done.sh", "ACME-7")
        self.assertEqual(done.returncode, 1)
        self.assertIn("no passing verify-mechanical.sh verdict (not verified)", done.stderr)

    def test_a_discarded_run_cannot_be_closed(self) -> None:
        self.lane()
        (self.repo / "src/other.py").write_text("x\n")
        self.verify_run()
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 1)

    def test_a_verified_run_closes(self) -> None:
        self.edited()
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 0)

    def test_an_edit_after_the_pass_blocks_the_close(self) -> None:
        self.edited()
        (self.repo / "src/cart.py").write_text("changed again\n")
        done = self.run_script("task-done.sh", "ACME-7")
        self.assertEqual(done.returncode, 1)
        self.assertIn("worktree changed after the verdict", done.stderr)
        (self.repo / "src/cart.py").write_text("changed\n")
        (self.repo / "src/other.py").write_text("stray\n")
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 1)

    def test_a_sampled_run_needs_a_review_record_for_its_digest(self) -> None:
        for n in range(1, 5):
            self.edited(f"ACME-{n}")
            git(self.repo, "checkout", "-q", "--", ".")
        result = self.edited("ACME-5")
        self.assertTrue(result["sample_review"])
        held = self.run_script("task-done.sh", "ACME-5")
        self.assertEqual(held.returncode, 1)
        self.assertIn("no review record given", held.stderr)
        bare = self.run_script("task-done.sh", "ACME-5", "--sample-reviewed", str(self.tmp / "missing.json"))
        self.assertIn("review record unreadable", bare.stderr)
        review = self.tmp / "review.json"
        for body, message in (({"reviewer": "sonnet", "verdict": "clean", "diff_sha256": "0" * 64}, "different diff"),
                              ({"reviewer": "sonnet", "verdict": "issues", "diff_sha256": result["digest"]}, "not 'clean'"),
                              ({"verdict": "clean", "diff_sha256": result["digest"]}, "names no reviewer")):
            review.write_text(json.dumps(body))
            self.assertIn(message, self.run_script("task-done.sh", "ACME-5", "--sample-reviewed", str(review)).stderr)
        review.write_text(json.dumps({"reviewer": "sonnet", "verdict": "clean", "diff_sha256": result["digest"]}))
        self.assertEqual(self.run_script("task-done.sh", "ACME-5", "--sample-reviewed", str(review)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
