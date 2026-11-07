"""Every pane an agent runs in carries its pai wake tokens from the start: launcher, agent-start.sh and the health warning."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase as _HarnessCase  # noqa: E402
from test_harness_mechanical import MechanicalCase  # noqa: E402


class PaneCase(_HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        stub = self.tmp / "stubbin"  # a plain `herdr` on PATH is this stub, never the developer's real one (and its live fleet)
        stub.mkdir()
        (stub / "herdr").write_text('#!/bin/sh\necho \'{"result":{"agents":[]}}\'\n')
        (stub / "herdr").chmod(0o755)
        self.env["PATH"] = f"{stub}{os.pathsep}{self.env['PATH']}"
        self.herdr_state = self.tmp / "herdr-state.json"
        self.config_dir = self.tmp / "wake-config"
        self.env.update(PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr_agents.py"), HERDR_BIN_PATH=str(FIXTURES / "fake_herdr_agents.py"),
                        FAKE_HERDR_LOG=str(self.tmp / "herdr.log"), FAKE_HERDR_STATE=str(self.herdr_state), HERDR_PLUGIN_CONFIG_DIR=str(self.config_dir))

    def tokens(self, pane: str) -> dict:
        return json.loads(self.herdr_state.read_text())["tokens"].get(pane, {}) if self.herdr_state.exists() else {}

    def calls(self) -> list[list[str]]:
        log = self.tmp / "herdr.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


class LauncherTagTest(PaneCase):
    def test_the_launcher_tags_its_pane_before_the_run_starts(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", "--parent", "acme-lead", "--role", "implementer")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p1"), {"name": "acme-7", "role": "implementer", "parent": "acme-lead", "issue": "ACME-7", "wake_on_done": "1"})
        order = [c[:2] for c in self.calls()]
        self.assertEqual(order[:2], [["pane", "get"], ["pane", "report-metadata"]])
        self.assertLess(order.index(["pane", "report-metadata"]), order.index(["pane", "run"]))
        self.assertEqual(order.count(["pane", "report-metadata"]), 1)
        self.assertTrue((self.config_dir / "agents/acme-7.json").is_file())

    def test_a_missing_parent_refuses_and_starts_nothing(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1")
        self.assertEqual(done.returncode, 2)
        self.assertIn("no --parent", done.stderr)
        self.assertNotIn(["pane", "run"], [c[:2] for c in self.calls()])
        self.assertEqual(self.tokens("wAC:p1"), {})

    def test_no_parent_is_an_explicit_opt_out(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", "--no-parent")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("parent", self.tokens("wAC:p1"))

    def test_the_parent_can_come_from_the_environment(self) -> None:
        self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", PAI_HARNESS_PARENT="acme-lead")
        self.assertEqual(self.tokens("wAC:p1")["parent"], "acme-lead")

    def test_a_failed_tag_stops_the_run_loudly(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", "--parent", "acme-lead", FAKE_HERDR_TAG_FAIL="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED to tag pane wAC:p1", done.stderr)
        self.assertNotIn(["pane", "run"], [c[:2] for c in self.calls()])

    def test_an_invalid_name_role_or_parent_is_refused(self) -> None:
        for args in (("ACME 7",), ("ACME-7", "--role", "Bad Role"), ("ACME-7", "--parent", "a\nb")):
            done = self.launch(args[0], "success", 0, "--pane", "wAC:p1", "--parent", "acme-lead", *args[1:])
            self.assertEqual(done.returncode, 2, args)
        self.assertEqual(self.tokens("wAC:p1"), {})

    def test_a_pane_holding_another_agent_is_not_overwritten(self) -> None:
        agents = self.config_dir / "agents"
        agents.mkdir(parents=True)
        (agents / "acme-lead.json").write_text(json.dumps({"pane": "wAC:p1", "tokens": {"name": "acme-lead", "role": "lead"}}))
        done = self.launch("ACME-7", "success", 0, "--pane", "wAC:p1", "--parent", "acme-lead")
        self.assertEqual(done.returncode, 2)
        self.assertIn("already hosts 'acme-lead'", done.stderr)
        self.assertEqual(self.tokens("wAC:p1"), {})
        self.assertTrue((agents / "acme-lead.json").is_file())


class MechanicalTagTest(PaneCase, MechanicalCase):
    def test_the_mechanical_profile_in_a_pane_is_tagged_and_needs_a_parent(self) -> None:
        done = self.lane("--pane", "wAC:p1", "--parent", "acme-lead")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p1"), {"name": "acme-7", "role": "mechanical", "parent": "acme-lead", "issue": "ACME-7", "wake_on_done": "1"})
        order = [c[:2] for c in self.calls()]
        self.assertLess(order.index(["pane", "report-metadata"]), order.index(["pane", "run"]))

    def test_the_mechanical_profile_without_a_parent_is_refused_in_a_pane(self) -> None:
        done = self.lane("--pane", "wAC:p1")
        self.assertEqual(done.returncode, 2)
        self.assertIn("no --parent", done.stderr)
        self.assertNotIn(["pane", "run"], [c[:2] for c in self.calls()])


class AgentStartTest(PaneCase):
    def start(self, *args: str, name: str = "acme-impl", **env: str):
        return self.run_script("agent-start.sh", name, "--role", "implementer", "--parent", "acme-lead", "--pane", "wAC:p2", *args, **env)

    def test_start_and_tag_in_one_step_with_args_passed_through(self) -> None:
        done = self.start("--issue", "ACME-7", "--kind", "claude", "--", "--permission-mode", "plan")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p2"), {"name": "acme-impl", "role": "implementer", "parent": "acme-lead", "wake_on_done": "1", "issue": "ACME-7"})
        start = next(c for c in self.calls() if c[:2] == ["agent", "start"])
        self.assertEqual(start, ["agent", "start", "acme-impl", "--pane", "wAC:p2", "--kind", "claude", "--", "--permission-mode", "plan"])

    def test_a_lead_carries_no_wake_on_done_and_verifies_without_it(self) -> None:
        done = self.run_script("agent-start.sh", "acme-lead", "--role", "lead", "--parent", "acme-orch", "--pane", "wAC:p2")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p2"), {"name": "acme-lead", "role": "lead", "parent": "acme-orch"})

    def test_one_shot_roles_get_wake_on_done(self) -> None:
        for i, role in enumerate(("implementer", "reviewer", "answerer", "gate", "verifier", "mechanical")):
            done = self.run_script("agent-start.sh", f"acme-{role}", "--role", role, "--parent", "acme-lead", "--pane", f"wAC:p{i + 10}")
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertEqual(self.tokens(f"wAC:p{i + 10}")["wake_on_done"], "1", role)

    def test_wake_and_no_wake_override_the_role_default(self) -> None:
        self.assertEqual(self.start("--no-wake").returncode, 0)
        self.assertNotIn("wake_on_done", self.tokens("wAC:p2"))
        done = self.run_script("agent-start.sh", "acme-lead", "--role", "lead", "--parent", "acme-orch", "--pane", "wAC:p3", "--wake")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.tokens("wAC:p3")["wake_on_done"], "1")

    def test_a_start_that_fails_with_no_agent_is_reported_failed(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_START_FAIL="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED acme-impl", done.stderr)

    def test_a_running_agent_that_is_not_ready_is_tagged_and_reported_not_failed(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_START_NOT_READY="1")
        self.assertEqual(done.returncode, 3)
        self.assertIn("STARTED-NOT-READY acme-impl", done.stderr)
        self.assertNotIn("FAILED", done.stderr)
        self.assertEqual(self.tokens("wAC:p2")["parent"], "acme-lead")
        self.assertEqual(self.tokens("wAC:p2")["wake_on_done"], "1")

    def test_a_tag_that_cannot_be_set_fails_the_start_before_anything_runs(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_TAG_FAIL="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("FAILED acme-impl", done.stderr)
        self.assertNotIn(["agent", "start"], [c[:2] for c in self.calls()])

    def test_tags_that_do_not_show_on_the_pane_afterwards_fail_the_start(self) -> None:
        done = self.start("--", "x", FAKE_HERDR_DROP_TOKENS="1")
        self.assertEqual(done.returncode, 1)
        self.assertIn("missing tokens after tagging: name,role,parent,wake_on_done", done.stderr)

    def test_verification_is_by_pane_not_by_name(self) -> None:
        other = [{"name": "acme-impl", "pane_id": "wAC:p9", "tokens": {"name": "acme-impl", "role": "implementer", "parent": "acme-lead", "wake_on_done": "1"}}]
        done = self.start("--", "x", FAKE_HERDR_AGENTS=json.dumps(other), FAKE_HERDR_DROP_TOKENS="1")
        self.assertEqual(done.returncode, 1)  # the same name on another pane must not vouch for this one

    def test_bad_names_and_values_are_usage_errors_that_tag_nothing(self) -> None:
        for name in ("Acme Lead", "a;touch x", "1abc", "a" * 33):
            self.assertEqual(self.start(name=name).returncode, 2, name)
        bad = self.run_script("agent-start.sh", "acme-impl", "--role", "implementer", "--parent", "a\nb", "--pane", "wAC:p2")
        self.assertEqual(bad.returncode, 2)
        self.assertFalse((self.tmp / "herdr.log").exists())

    def test_missing_pane_or_parent_is_a_usage_error_and_starts_nothing(self) -> None:
        done = self.run_script("agent-start.sh", "acme-impl", "--role", "implementer", "--pane", "wAC:p2")
        self.assertEqual(done.returncode, 2)
        self.assertFalse((self.tmp / "herdr.log").exists())

    def test_it_works_through_a_symlink(self) -> None:
        link = self.tmp / "bin" / "agent-start"
        link.parent.mkdir()
        link.symlink_to(SCRIPTS / "agent-start.sh")
        done = subprocess.run([str(link), "acme-impl", "--role", "implementer", "--parent", "acme-lead", "--pane", "wAC:p2"],
                              text=True, capture_output=True, env=self.env, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)


class HealthWarningTest(PaneCase):
    def check(self, agents: list[dict], registered: tuple[str, ...] = ("acme-ghost",), **env: str):
        for name in registered:
            self.run_script("health.sh", "beat", name)
        return self.run_script("health.sh", "check", FAKE_HERDR_AGENTS=json.dumps(agents), **env)

    def test_a_registered_agent_pane_without_tokens_is_a_named_warning(self) -> None:
        agents = [{"name": "acme-ghost", "pane_id": "wAC:p5"}, {"name": "acme-lead", "pane_id": "wAC:p1", "tokens": {"role": "lead", "name": "acme-lead", "parent": "root", "wake_on_done": "1"}}]
        done = self.check(agents)
        self.assertIn("WARNING untagged-agent-pane: acme-ghost (wAC:p5)", done.stderr)
        self.assertNotIn("acme-lead (wAC:p1)", done.stderr)
        self.assertEqual(json.loads(done.stdout)["untagged_agent_panes"], [{"name": "acme-ghost", "pane_id": "wAC:p5", "missing": ["name", "role", "parent"]}])

    def test_a_half_tagged_pane_is_flagged(self) -> None:
        agents = [{"name": "acme-impl", "pane_id": "wAC:p3", "tokens": {"name": "acme-impl"}}]
        done = self.check(agents, registered=("acme-other",))
        self.assertIn("acme-impl (wAC:p3) is missing pai tokens role,parent", done.stderr)

    def test_an_agent_the_harness_did_not_start_is_not_flagged(self) -> None:
        done = self.check([{"name": "my-own-agent", "pane_id": "wAC:p8"}])
        self.assertNotIn("WARNING", done.stderr)
        self.assertEqual(json.loads(done.stdout)["untagged_agent_panes"], [])

    def test_herdr_bin_path_is_honoured_and_pai_harness_herdr_is_the_fallback(self) -> None:
        agents = [{"name": "acme-ghost", "pane_id": "wAC:p5"}]
        self.env.pop("PAI_HARNESS_HERDR")
        self.assertIn("WARNING", self.check(agents).stderr)  # HERDR_BIN_PATH only
        self.env.pop("HERDR_BIN_PATH")
        self.assertNotIn("WARNING", self.check(agents).stderr)  # neither: plain `herdr` on PATH, which is the empty stub
        self.assertIn("WARNING", self.check(agents, PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr_agents.py")).stderr)

    def test_wake_on_done_is_required_for_one_shot_roles_only(self) -> None:
        base = {"name": "x", "role": "lead", "parent": "root"}
        agents = [{"name": "acme-lead", "pane_id": "wAC:p1", "tokens": {**base, "name": "acme-lead"}},
                  {"name": "acme-impl", "pane_id": "wAC:p2", "tokens": {**base, "name": "acme-impl", "role": "implementer"}}]
        done = self.check(agents, registered=("acme-lead",))
        self.assertNotIn("acme-lead (wAC:p1)", done.stderr)
        self.assertIn("acme-impl (wAC:p2) is missing pai tokens wake_on_done", done.stderr)

    def test_without_herdr_there_is_no_warning(self) -> None:
        done = self.check([], HERDR_BIN_PATH="/nonexistent/herdr", PAI_HARNESS_HERDR="/nonexistent/herdr")
        self.assertNotIn("WARNING", done.stderr)

    def test_an_empty_registry_is_a_usage_error_without_probing_herdr(self) -> None:
        done = self.check([{"name": "x", "pane_id": "wAC:p1"}], registered=())
        self.assertEqual(done.returncode, 2)
        self.assertFalse((self.tmp / "herdr.log").exists())
