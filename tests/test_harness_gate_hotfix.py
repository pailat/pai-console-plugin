"""The [gates.hotfix] profile: one fixture test for each condition of the red-release hotfix lane."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import gate_request as gr  # noqa: E402
import harness_config as hc  # noqa: E402

SHA = "0123456789abcdef0123456789abcdef01234567"
PROFILE = hc.load_file(FIXTURES / "hotfix.pai-harness.toml")["gates"]["hotfix"]
TITLE = "hotfix: repair the broken typecheck"


class FakeRunner:
    """Fakes command results by name; every command not listed passes. Records the calls in order."""

    def __init__(self, failing: tuple[str, ...] = ()) -> None:
        self.failing, self.calls = failing, []

    def __call__(self, command: str, cwd: str) -> int:
        self.calls.append(command)
        return 1 if command in self.failing else 0


class HotfixConditionsTest(unittest.TestCase):
    def decide(self, runner: FakeRunner, title: str = TITLE, labels: list[str] | None = None, **kwargs) -> dict:
        return gr.hotfix_decide(PROFILE, SHA, title, labels or [], runner=runner, **kwargs)

    def test_tip_green_profile_inactive(self) -> None:
        runner = FakeRunner()  # active_when passes: the release tip is green
        result = self.decide(runner)
        self.assertEqual((result["decision"], result["merge"], result["revert"], result["blocker"]), ("inactive", False, False, None))
        self.assertEqual(runner.calls, ["tip-check"])

    def test_pr_not_matching_is_refused(self) -> None:
        runner = FakeRunner(failing=("tip-check",))
        result = self.decide(runner, title="feat: add a button", labels=["ui"])
        self.assertEqual((result["decision"], result["merge"]), ("refused", False))
        self.assertEqual(runner.calls, ["tip-check"])  # no pre_merge command ran

    def test_a_label_match_is_enough(self) -> None:
        result = self.decide(FakeRunner(failing=("tip-check",)), title="feat: add a button", labels=["Release-Red"])
        self.assertEqual(result["decision"], "merge")

    def test_pre_merge_fails_no_merge(self) -> None:
        merged = []
        runner = FakeRunner(failing=("tip-check", "test-touched"))
        result = self.decide(runner, merge=lambda: merged.append(1))
        self.assertEqual((result["decision"], result["merge"], result["blocker"]), ("pre_merge_failed", False, None))
        self.assertEqual((merged, runner.calls), ([], ["tip-check", "typecheck-all", "test-touched"]))

    def test_post_merge_fails_revert_and_blocker(self) -> None:
        runner = FakeRunner(failing=("tip-check", "gate-full"))
        result = self.decide(runner, merge=lambda: runner.calls.append("MERGE"))
        self.assertEqual((result["decision"], result["revert"]), ("revert", True))
        self.assertTrue(result["blocker"].startswith("BLOCKER hotfix " + SHA))
        self.assertEqual(runner.calls[-2:], ["MERGE", "gate-full"])

    def test_all_green_merge_then_full_gate(self) -> None:
        runner = FakeRunner(failing=("tip-check",))
        result = self.decide(runner, merge=lambda: runner.calls.append("MERGE"))
        self.assertEqual((result["decision"], result["revert"], result["blocker"]), ("post_merge_passed", False, None))
        self.assertEqual(runner.calls, ["tip-check", "typecheck-all", "test-touched", "MERGE", "gate-full"])

    def test_green_pre_merge_says_merge_now_without_running_the_full_gate(self) -> None:
        runner = FakeRunner(failing=("tip-check",))
        result = self.decide(runner)
        self.assertEqual((result["decision"], result["merge"]), ("merge", True))
        self.assertNotIn("gate-full", runner.calls)

    def test_post_phase_skips_active_when(self) -> None:
        runner = FakeRunner()
        self.assertEqual(self.decide(runner, phase="post-merge")["decision"], "post_merge_passed")
        self.assertEqual(runner.calls, ["gate-full"])

    def test_revert_is_not_emitted_when_revert_on_failure_is_off(self) -> None:
        result = gr.hotfix_decide({**PROFILE, "revert_on_failure": False}, SHA, TITLE, [], runner=FakeRunner(failing=("gate-full",)), phase="post-merge")
        self.assertEqual((result["decision"], result["revert"]), ("post_merge_failed", False))
        self.assertIn("BLOCKER", result["blocker"])


class HotfixCliTest(HarnessCase):
    def hotfix(self, config: str, *args: str):
        return self.run_script("gate-request.sh", "--hotfix", "--sha", SHA, "--cwd", str(self.tmp), "--config", str(config), *args)

    def write(self, **commands: str) -> Path:
        text = (FIXTURES / "hotfix.pai-harness.toml").read_text()
        path = self.tmp / "hotfix.toml"
        path.write_text(text.replace('"tip-check"', commands.get("tip", '"false"')).replace('["typecheck-all", "test-touched"]', commands.get("pre", '["true"]')).replace('"gate-full"', commands.get("post", '"true"')))
        return path

    def test_cli_prints_the_decision_as_json(self) -> None:
        done = self.hotfix(self.write(), "--pr-title", TITLE)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["decision"], "merge")
        self.assertEqual(self.hotfix(self.write(tip='"true"'), "--pr-title", TITLE).returncode, 0)
        refused = self.hotfix(self.write(), "--pr-title", "feat: a button")
        self.assertEqual((refused.returncode, json.loads(refused.stdout)["decision"]), (1, "refused"))

    def test_cli_post_merge_failure_prints_the_blocker_line(self) -> None:
        done = self.hotfix(self.write(post='"false"'), "--phase", "post-merge")
        self.assertEqual(done.returncode, 1)
        self.assertIn("BLOCKER hotfix " + SHA, done.stdout.splitlines()[-1])
        self.assertEqual(json.loads(done.stdout.rsplit("}", 1)[0] + "}")["decision"], "revert")

    def test_plain_gates_skip_the_hotfix_profile(self) -> None:
        done = self.run_script("gate-request.sh", "--sha", SHA, "--config", str(FIXTURES / "hotfix.pai-harness.toml"), "--dry-run")
        self.assertEqual(sorted(json.loads(done.stdout)["gates"]), ["unit"])
        self.assertEqual(self.run_script("gate-request.sh", "--sha", SHA, "--gate", "hotfix", "--config", str(FIXTURES / "hotfix.pai-harness.toml")).returncode, 2)


if __name__ == "__main__":
    unittest.main()
