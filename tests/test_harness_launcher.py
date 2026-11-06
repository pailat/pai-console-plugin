"""The launcher: state comes only from the stream-json result frame and the exit code."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_lib as lib  # noqa: E402


def summary_of(name: str) -> dict:
    return lib.parse_stream((FIXTURES / f"{name}.jsonl").read_text().splitlines())  # init placeholders are irrelevant to run_state


class RunStateTest(HarnessCase):
    def test_success_with_exit_zero_is_done(self) -> None:
        verdict = lib.run_state(summary_of("success"), 0)
        self.assertEqual((verdict["state"], verdict["turns"], verdict["cost_usd"]), ("done", 2, 0.0086))
        self.assertEqual(verdict["session_id"], "11111111-2222-3333-4444-555555555555")

    def test_a_non_zero_exit_beats_a_success_frame(self) -> None:
        self.assertEqual(lib.run_state(summary_of("success"), 1)["state"], "failed")

    def test_error_result_fails(self) -> None:
        verdict = lib.run_state(summary_of("failed"), 0)
        self.assertEqual((verdict["state"], verdict["reason"]), ("failed", "result error_max_turns"))

    def test_permission_denials_block_even_on_a_success_frame(self) -> None:
        verdict = lib.run_state(summary_of("permission"), 0)
        self.assertEqual((verdict["state"], verdict["reason"]), ("blocked", "permission needed: Bash"))

    def test_no_result_frame_fails_whatever_the_exit_code(self) -> None:
        for code in (0, 137):
            self.assertEqual(lib.run_state(summary_of("crashed"), code)["state"], "failed")

    def test_timeout_fails(self) -> None:
        self.assertEqual(lib.run_state(summary_of("crashed"), -15, timed_out=True)["reason"], "timeout")

    def test_bad_lines_are_counted_not_fatal(self) -> None:
        summary = lib.parse_stream(["not json", "[1]", '{"type":"result","subtype":"success"}'])
        self.assertEqual((summary["bad_lines"], summary["frames"]), (2, 1))


EXAMPLE = SCRIPTS.parent / "examples/acme/.pai-harness.toml"  # maps roles to zones and names a push wrapper


class LaunchTest(HarnessCase):
    def test_a_successful_run_records_stream_state_cost_turns_and_session(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--queue", "main")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((self.state / "runs/ACME-7.jsonl").read_text(), self.fixture("success").read_text())
        record = self.record("ACME-7")
        self.assertEqual((record["state"], record["turns"], record["cost_usd"], record["exit_code"]), ("done", 2, 0.0086, 0))
        self.assertEqual((record["session_id"], record["machine"]), ("11111111-2222-3333-4444-555555555555", "acme-desktop"))
        self.assertEqual([e["kind"] for e in self.journal()], ["run.started", "run.finished"])

    def test_the_command_is_headless_stream_json_with_the_prompt_on_stdin_and_no_permission_bypass(self) -> None:
        self.launch("ACME-7", "success", 0, "--role", "mechanical")
        sent = json.loads((self.tmp / "claude.json").read_text())
        self.assertEqual(sent["argv"][:5], ["-p", "--output-format", "stream-json", "--verbose", "--model"])
        self.assertEqual(sent["argv"][5], "haiku")
        self.assertIn("Implement ACME-7", sent["prompt"])
        self.assertFalse([a for a in sent["argv"] if "skip-permissions" in a or a == "bypassPermissions"])

    def run_with_env_probe(self, issue: str, *extra: str, **env: str) -> dict:
        probe = self.tmp / "probe_claude.py"
        probe.write_text("import json, os, sys\nsys.stdin.read()\n"
                         "json.dump({k: v for k, v in os.environ.items() if k.startswith('PAI_HARNESS_')}, open(os.environ['PROBE_LOG'], 'w'))\n"
                         "print(open(os.environ['FAKE_CLAUDE_FIXTURE']).read(), end='')\n")
        wrapper = self.tmp / "claude"
        wrapper.write_text(f"#!/bin/sh\nexec {sys.executable} {probe} \"$@\"\n")
        wrapper.chmod(0o755)
        done = self.run_script("launch.sh", issue, "--prompt-file", str(self.prompt), *extra, PAI_HARNESS_CLAUDE=str(wrapper),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("success")), PROBE_LOG=str(self.tmp / "env.json"), **{"PAI_HARNESS_CONFIG": str(EXAMPLE), **env})
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads((self.tmp / "env.json").read_text())

    def test_the_run_gets_the_hook_environment_from_the_config(self) -> None:
        seen = self.run_with_env_probe("ACME-7", "--role", "lead", PAI_HARNESS_ZONES="stale", PAI_HARNESS_KNOWLEDGE_CMD="knowledge.sh")
        self.assertEqual(seen["PAI_HARNESS_ROLE"], "lead")
        self.assertEqual(seen["PAI_HARNESS_AGENT"], "ACME-7")
        self.assertEqual(seen["PAI_HARNESS_ZONES"], "frontend,contracts")
        self.assertEqual(seen["PAI_HARNESS_BRIEF"], str(self.prompt))
        self.assertEqual(seen["PAI_HARNESS_PUSH_WRAPPER"], "scripts/queue-push.sh")
        self.assertEqual(seen["PAI_HARNESS_KNOWLEDGE_CMD"], "knowledge.sh")  # site tooling passes through
        self.assertEqual((seen["PAI_HARNESS_CONFIG"], seen["PAI_HARNESS_STATE_DIR"]), (str(EXAMPLE), str(self.state)))

    def test_the_role_defaults_to_implementer_and_an_unmapped_role_drops_a_stale_zone_list(self) -> None:
        seen = self.run_with_env_probe("ACME-7", PAI_HARNESS_ZONES="stale")
        self.assertEqual((seen["PAI_HARNESS_ROLE"], seen["PAI_HARNESS_ZONES"]), ("implementer", "frontend"))
        seen = self.run_with_env_probe("ACME-7", "--role", "mechanical", PAI_HARNESS_ZONES="stale")
        self.assertNotIn("PAI_HARNESS_ZONES", seen)

    def test_a_prompt_given_inline_becomes_the_brief_file(self) -> None:
        wrapper = self.tmp / "claude"
        wrapper.write_text("#!/bin/sh\ncat > /dev/null\ncat \"$FAKE_CLAUDE_FIXTURE\"\n")
        wrapper.chmod(0o755)
        done = self.run_script("launch.sh", "ACME-7", "--prompt", "Do ACME-7.", PAI_HARNESS_CLAUDE=str(wrapper), FAKE_CLAUDE_FIXTURE=str(self.fixture("success")),
                               PAI_HARNESS_CONFIG=str(EXAMPLE))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual((self.state / "briefs/ACME-7.md").read_text(), "Do ACME-7.")

    def test_the_dry_run_shows_the_hook_environment_and_writes_no_brief(self) -> None:
        plan = json.loads(self.run_script("launch.sh", "ACME-7", "--prompt", "x", "--role", "lead", "--dry-run", PAI_HARNESS_CONFIG=str(EXAMPLE)).stdout)
        self.assertEqual(plan["hook_env"]["PAI_HARNESS_ZONES"], "frontend,contracts")
        self.assertEqual(sorted(plan["hook_env"]), ["PAI_HARNESS_AGENT", "PAI_HARNESS_BRIEF", "PAI_HARNESS_PUSH_WRAPPER", "PAI_HARNESS_ROLE", "PAI_HARNESS_ZONES"])
        self.assertFalse(self.state.exists())

    def test_without_a_push_wrapper_in_the_config_a_stale_one_is_not_passed_on(self) -> None:
        seen = self.run_with_env_probe("ACME-7", PAI_HARNESS_CONFIG=self.env["PAI_HARNESS_CONFIG"], PAI_HARNESS_PUSH_WRAPPER="stale.sh")
        self.assertNotIn("PAI_HARNESS_PUSH_WRAPPER", seen)

    def test_a_permission_blocked_run_fails_fast_with_exit_3(self) -> None:
        done = self.launch("ACME-8", "permission", 0)
        self.assertEqual(done.returncode, 3)
        record = self.record("ACME-8")
        self.assertEqual((record["state"], record["reason"]), ("blocked", "permission needed: Bash"))
        self.assertEqual(lib.read_json(self.state / "registry/ACME-8.json")["state"], "blocked")

    def test_a_failed_run_exits_1(self) -> None:
        self.assertEqual(self.launch("ACME-9", "failed", 0).returncode, 1)
        self.assertEqual(self.record("ACME-9")["state"], "failed")

    def test_a_crash_without_a_result_frame_fails(self) -> None:
        self.assertEqual(self.launch("ACME-9", "crashed", 137).returncode, 1)
        self.assertIn("no result frame", self.record("ACME-9")["reason"])

    def test_a_missing_claude_binary_fails_with_a_state_file(self) -> None:
        done = self.run_script("launch.sh", "ACME-9", "--prompt", "x", PAI_HARNESS_CLAUDE=str(self.tmp / "absent"))
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.record("ACME-9")["state"], "failed")

    def test_dry_run_changes_nothing(self) -> None:
        done = self.launch("ACME-7", "success", 0, "--dry-run")
        self.assertEqual(done.returncode, 0)
        plan = json.loads(done.stdout)
        self.assertEqual(plan["command"][1:5], ["-p", "--output-format", "stream-json", "--verbose"])
        self.assertFalse(self.state.exists())

    def test_a_foreign_issue_id_is_refused(self) -> None:
        self.assertEqual(self.launch("OTHER-1", "success").returncode, 2)

    def test_park_and_resume_use_the_recorded_session(self) -> None:
        self.launch("ACME-8", "permission", 0)
        self.assertEqual(self.run_script("launch.sh", "ACME-8", "--park").returncode, 0)
        self.assertEqual(lib.read_json(self.state / "registry/ACME-8.json")["state"], "parked")
        done = self.run_script("launch.sh", "ACME-8", "--resume", FAKE_CLAUDE_FIXTURE=str(self.fixture("success")))
        self.assertEqual(done.returncode, 0, done.stderr)
        argv = json.loads((self.tmp / "claude.json").read_text())["argv"]
        self.assertEqual(argv[argv.index("--resume") + 1], "11111111-2222-3333-4444-555555555555")
        self.assertTrue(self.record("ACME-8")["resumed"])

    def test_resume_without_a_session_is_refused(self) -> None:
        self.assertEqual(self.run_script("launch.sh", "ACME-5", "--resume").returncode, 2)

    def test_the_mcp_bridge_gets_events_and_the_journal_is_the_fallback(self) -> None:
        sink = self.tmp / "bridge.jsonl"
        bridge = f"{sys.executable} -c \"import sys; open(r'{sink}','a').write(sys.stdin.read()+chr(10))\""
        self.env["PAI_HARNESS_MCP_CMD"] = bridge
        self.launch("ACME-7", "success")
        self.assertEqual(len(sink.read_text().splitlines()), 2)
        self.assertEqual(self.journal(), [])
        self.env["PAI_HARNESS_MCP_CMD"] = f"{sys.executable} -c \"raise SystemExit(1)\""
        self.launch("ACME-7", "success")
        self.assertEqual(len(self.journal()), 2)
        self.assertFalse(self.journal()[0]["delivered"])


class PaneLaunchTest(HarnessCase):
    def test_the_pane_run_ends_by_the_state_file_and_never_reads_agent_status(self) -> None:
        log = self.tmp / "herdr.log"
        done = self.run_script(
            "launch.sh", "ACME-7", "--prompt-file", str(self.prompt), "--pane", "pane-1",
            PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr.py"), FAKE_HERDR_LOG=str(log),
            FAKE_CLAUDE_FIXTURE=str(self.fixture("success")))
        self.assertEqual(done.returncode, 0, done.stderr)
        calls = [json.loads(line) for line in log.read_text().splitlines()]
        self.assertEqual([c[:2] for c in calls], [["pane", "run"], ["pane", "wait-output"]])
        self.assertEqual(self.record("ACME-7")["state"], "done")
        self.assertNotIn("agent", [c[0] for c in calls])
        source = (SCRIPTS / "launch.py").read_text()
        self.assertNotIn('"agent"', source)

    def test_a_blocked_pane_run_returns_3(self) -> None:
        done = self.run_script("launch.sh", "ACME-8", "--prompt-file", str(self.prompt), "--pane", "pane-1",
                               PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr.py"), FAKE_HERDR_LOG=str(self.tmp / "h.log"),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("permission")))
        self.assertEqual(done.returncode, 3)


class TaskLifecycleTest(HarnessCase):
    """/task-start through /task-done with the fake claude: only the stream and the exit code decide."""

    def test_start_to_done(self) -> None:
        self.assertEqual(self.launch("ACME-7", "success", 0, "--queue", "main").returncode, 0)
        done = self.run_script("task-done.sh", "ACME-7")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout.splitlines()[0], "Done: run done in 2 turns, cost $0.0086, session 11111111-2222-3333-4444-555555555555")
        self.assertEqual(lib.read_json(self.state / "registry/ACME-7.json")["state"], "done")
        self.assertEqual([e["kind"] for e in self.journal()][-1], "task.done")

    def test_a_failed_run_cannot_be_closed(self) -> None:
        self.launch("ACME-9", "failed", 0)
        done = self.run_script("task-done.sh", "ACME-9")
        self.assertEqual(done.returncode, 1)
        self.assertIn("not closed", done.stderr)
        self.assertEqual(lib.read_json(self.state / "registry/ACME-9.json")["state"], "failed")

    def test_a_permission_blocked_run_cannot_be_closed(self) -> None:
        self.launch("ACME-8", "permission", 0)
        done = self.run_script("task-done.sh", "ACME-8")
        self.assertEqual(done.returncode, 3)
        self.assertIn("Blocked: permission needed: Bash", done.stdout)

    def test_a_success_frame_with_a_failing_exit_cannot_be_closed(self) -> None:
        self.launch("ACME-7", "success", 2)
        self.assertEqual(self.run_script("task-done.sh", "ACME-7").returncode, 1)

    def test_no_run_means_usage_error(self) -> None:
        self.assertEqual(self.run_script("task-done.sh", "ACME-3").returncode, 2)


if __name__ == "__main__":
    unittest.main()
