"""Every pane an agent runs in carries its pai wake tokens from the start: launcher, agent-start.sh and the health warning."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase as _HarnessCase  # noqa: E402


class PaneCase(_HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        self.herdr_state = self.tmp / "herdr-state.json"
        self.config_dir = self.tmp / "wake-config"
        self.env.update(PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr_agents.py"), HERDR_BIN_PATH=str(FIXTURES / "fake_herdr_agents.py"),
                        FAKE_HERDR_LOG=str(self.tmp / "herdr.log"), FAKE_HERDR_STATE=str(self.herdr_state), HERDR_PLUGIN_CONFIG_DIR=str(self.config_dir))

    def tokens(self, pane: str) -> dict:
        return json.loads(self.herdr_state.read_text())["tokens"].get(pane, {})

    def calls(self) -> list[list[str]]:
        return [json.loads(line) for line in (self.tmp / "herdr.log").read_text().splitlines()]


class LauncherTagTest(PaneCase):
    def test_the_launcher_tags_its_pane_before_the_run_starts(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", "--parent", "acme-lead", "--role", "implementer")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p1"), {"name": "ACME-7", "role": "implementer", "parent": "acme-lead", "issue": "ACME-7", "wake_on_done": "1"})
        order = [c[:2] for c in self.calls()]
        self.assertLess(order.index(["pane", "report-metadata"]), order.index(["pane", "run"]))
        self.assertTrue((self.config_dir / "agents/ACME-7.json").is_file())

    def test_a_missing_parent_is_said_aloud_not_silent(self) -> None:
        self.env.pop("PAI_HARNESS_PARENT")
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1")
        self.assertIn("no --parent", done.stderr)
        self.assertNotIn("parent", self.tokens("wAC:p1"))

    def test_the_parent_can_come_from_the_environment(self) -> None:
        self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", PAI_HARNESS_PARENT="acme-lead")
        self.assertEqual(self.tokens("wAC:p1")["parent"], "acme-lead")


class AgentStartTest(PaneCase):
    def start(self, *args: str, **env: str):
        return self.run_script("agent-start.sh", "acme-impl", "--role", "implementer", "--parent", "acme-lead", "--pane", "wAC:p2", *args, **env)

    def test_start_and_tag_in_one_step_with_args_passed_through(self) -> None:
        done = self.start("--issue", "ACME-7", "--kind", "claude", "--", "--permission-mode", "plan")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p2"), {"name": "acme-impl", "role": "implementer", "parent": "acme-lead", "wake_on_done": "1", "issue": "ACME-7"})
        start = next(c for c in self.calls() if c[:2] == ["agent", "start"])
        self.assertEqual(start, ["agent", "start", "acme-impl", "--pane", "wAC:p2", "--kind", "claude", "--", "--permission-mode", "plan"])

    def test_a_failed_start_is_reported_failed(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_START_FAIL="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED acme-impl", done.stderr)

    def test_a_tag_that_does_not_stick_fails_the_start(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_TAG_FAIL="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED acme-impl", done.stderr)

    def test_missing_pane_or_parent_is_a_usage_error_and_starts_nothing(self) -> None:
        done = self.run_script("agent-start.sh", "acme-impl", "--role", "implementer", "--pane", "wAC:p2")
        self.assertEqual(done.returncode, 2)
        self.assertFalse((self.tmp / "herdr.log").exists())


class HealthWarningTest(PaneCase):
    def test_an_agent_pane_without_tokens_is_a_named_warning(self) -> None:
        agents = [{"name": "acme-ghost", "pane_id": "wAC:p5"}, {"name": "acme-lead", "pane_id": "wAC:p1", "tokens": {"role": "lead", "name": "acme-lead"}}]
        done = self.run_script("health.sh", "check", FAKE_HERDR_AGENTS=json.dumps(agents))
        self.assertIn("WARNING untagged-agent-pane: acme-ghost (wAC:p5)", done.stderr)
        self.assertNotIn("acme-lead (wAC:p1)", done.stderr)
        self.assertEqual(json.loads(done.stdout)["untagged_agent_panes"], [{"name": "acme-ghost", "pane_id": "wAC:p5"}])

    def test_without_herdr_there_is_no_warning(self) -> None:
        done = self.run_script("health.sh", "check", PAI_HARNESS_HERDR="/nonexistent/herdr")
        self.assertNotIn("WARNING", done.stderr)
