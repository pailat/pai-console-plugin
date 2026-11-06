"""The mechanical lane: the launcher profile (closed brief, Haiku, empty strict MCP, four tools, json output) and the diff-scope verifier."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
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
        self.repo = self.tmp / "repo"
        (self.repo / "src").mkdir(parents=True)
        for name in (*FILES, "src/other.py", "README.md"):
            (self.repo / name).write_text(f"# {name}\ndef calc_total():\n    return 1\n")
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
        allowed = argv[argv.index("--allowed-tools") + 1:argv.index("--allowed-tools") + 5]
        self.assertEqual(allowed, ["Read", "Edit", "Grep", "Glob"])
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
        self.assertEqual(self.lane(**kwargs).returncode, 0)  # type: ignore[arg-type]

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


class SamplerTest(unittest.TestCase):
    def test_the_picker_is_deterministic_and_about_one_in_five(self) -> None:
        picks = [vm.sampled(f"ACME-{n}", "a" * 40, 5) for n in range(1, 501)]
        self.assertEqual(picks, [vm.sampled(f"ACME-{n}", "a" * 40, 5) for n in range(1, 501)])
        self.assertTrue(70 <= sum(picks) <= 130, sum(picks))

    def test_every_one_samples_everything(self) -> None:
        self.assertTrue(all(vm.sampled(f"ACME-{n}", "b" * 40, 1) for n in range(1, 20)))


class CloseTest(MechanicalCase):
    def sampled_issue(self, want: bool) -> str:
        base = git(self.repo, "rev-parse", "HEAD")
        return next(f"ACME-{n}" for n in range(1, 500) if vm.sampled(f"ACME-{n}", base, 5) is want)

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

    def verify_run(self, issue: str = "ACME-7") -> subprocess.CompletedProcess:
        return self.run_script("verify-mechanical.sh", issue, "--check", "true")

    def test_a_verified_run_closes_and_a_sampled_one_waits_for_its_review(self) -> None:
        plain = self.sampled_issue(False)
        self.lane(issue=plain)
        (self.repo / "src/cart.py").write_text("changed\n")
        self.assertFalse(json.loads(self.verify_run(plain).stdout)["sample_review"])
        self.assertEqual(self.run_script("task-done.sh", plain).returncode, 0)
        git(self.repo, "checkout", "-q", "--", ".")
        picked = self.sampled_issue(True)
        self.lane(issue=picked)
        (self.repo / "src/cart.py").write_text("changed\n")
        done = self.verify_run(picked)
        self.assertTrue(json.loads(done.stdout)["sample_review"])
        self.assertIn("SONNET REVIEW REQUIRED", done.stderr)
        held = self.run_script("task-done.sh", picked)
        self.assertEqual(held.returncode, 1)
        self.assertIn("Sonnet sample review", held.stderr)
        self.assertEqual(self.run_script("task-done.sh", picked, "--sample-reviewed").returncode, 0)


if __name__ == "__main__":
    unittest.main()
