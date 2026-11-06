"""The launcher: state comes only from the stream-json result frame and the exit code."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, PLUGIN_ROOT, SCRIPTS, HarnessCase as _HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_lib as lib  # noqa: E402


class HarnessCase(_HarnessCase):
    """The shared case, run outside any Herdr: a launch here must not open a tab in the developer's own session."""

    def setUp(self) -> None:
        super().setUp()
        for name in [k for k in self.env if k.startswith("HERDR_")]:
            self.env.pop(name)


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

    def test_the_run_exports_its_start_commit_as_the_zone_diff_base(self) -> None:
        repo = self.tmp / "repo"
        repo.mkdir()
        env = {**os.environ, "HOME": str(self.tmp)}
        for argv in (["init", "-q", "-b", "main"], ["-c", "user.name=Acme", "-c", "user.email=acme@example.com", "commit", "-q", "--allow-empty", "-m", "start"]):
            subprocess.run(["git", "-C", str(repo), *argv], check=True, capture_output=True, env=env)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True, env=env).stdout.strip()
        seen = self.run_with_env_probe("ACME-7", "--cwd", str(repo), PAI_HARNESS_BASE="stale")
        self.assertEqual(seen["PAI_HARNESS_BASE"], head)
        self.assertEqual(lib.read_json(self.state / "registry/ACME-7.json")["base"], head)

    def test_a_cwd_outside_git_drops_a_stale_base(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        seen = self.run_with_env_probe("ACME-7", "--role", "lead", "--cwd", str(plain), PAI_HARNESS_BASE="stale")
        self.assertNotIn("PAI_HARNESS_BASE", seen)

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
        self.assertEqual(sorted(plan["hook_env"]), ["PAI_HARNESS_AGENT", "PAI_HARNESS_BASE", "PAI_HARNESS_BRIEF", "PAI_HARNESS_PUSH_WRAPPER", "PAI_HARNESS_ROLE", "PAI_HARNESS_ZONES"])
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
        self.assertEqual([c[:2] for c in calls], [["pane", "get"], ["pane", "run"], ["pane", "wait-output"]])
        self.assertEqual(self.record("ACME-7")["state"], "done")
        self.assertNotIn("agent", [c[0] for c in calls])
        source = (SCRIPTS / "launch.py").read_text()
        self.assertNotIn('"agent"', source)

    def test_a_blocked_pane_run_returns_3(self) -> None:
        done = self.run_script("launch.sh", "ACME-8", "--prompt-file", str(self.prompt), "--pane", "pane-1",
                               PAI_HARNESS_HERDR=str(FIXTURES / "fake_herdr.py"), FAKE_HERDR_LOG=str(self.tmp / "h.log"),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("permission")))
        self.assertEqual(done.returncode, 3)


RENDER = Path(__file__).resolve().parent / "fixtures/harness-render"


class DisplayTest(HarnessCase):
    """Every run is visible from Herdr: live lines in the pane, workspace metadata with a TTL, the tab label. Herdr and claude are fakes."""

    def herdr(self, **env: str) -> dict[str, str]:
        return {"PAI_HARNESS_HERDR": str(RENDER / "fake_herdr.py"), "FAKE_HERDR_LOG": str(self.tmp / "herdr.log"), **env}

    def calls(self) -> list[list[str]]:
        log = self.tmp / "herdr.log"
        return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []

    def run_fixture(self, issue: str, fixture: Path, *extra: str, exit_code: int = 0, **env: str):
        return self.run_script("launch.sh", issue, "--prompt-file", str(self.prompt), *extra, FAKE_CLAUDE_FIXTURE=str(self.render_fixture(fixture.stem)),
                               FAKE_CLAUDE_EXIT=str(exit_code), **env)

    def render_fixture(self, name: str) -> Path:
        skills = sorted(f"pai-harness:{d.name}" for d in (PLUGIN_ROOT / "skills").glob("*") if (d / "SKILL.md").is_file())
        out = []
        for line in (RENDER / f"{name}.jsonl").read_text().splitlines():
            frame = json.loads(line)
            if frame.get("subtype") == "init":
                frame["plugins"][0]["path"] = str(PLUGIN_ROOT)
                frame["skills"] = skills
            out.append(json.dumps(frame))
        path = self.tmp / f"{name}.materialized.jsonl"
        path.write_text("\n".join(out) + "\n")
        return path

    def metadata(self) -> list[list[str]]:
        return [c for c in self.calls() if c[:2] == ["workspace", "report-metadata"]]

    def token(self, call: list[str], name: str) -> str:
        return next(call[i + 1].split("=", 1)[1] for i, a in enumerate(call) if a == "--token" and call[i + 1].startswith(name + "="))

    def test_a_pane_run_shows_its_live_lines_in_the_pane(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", **self.herdr())
        self.assertEqual(done.returncode, 0, done.stderr)
        lines = done.stderr.splitlines()  # the fake `pane run` runs the command here, so its terminal output is this stderr
        self.assertTrue(lines[0].startswith("▶ ACME-7 run "))
        self.assertTrue(any(l.startswith("▶ init model=claude-sonnet-5-5 skills=") and "hooks=PreToolUse,SessionStart,Stop" in l for l in lines), lines)
        self.assertIn("● tool Edit apps/acme-storefront/src/checkout/totals.ts", lines)
        self.assertIn("■ result done turns=4 duration=12.4s cost≈$0.0421", lines)
        self.assertTrue(lines[-1].startswith("■ record done exit=0"))

    def test_the_stream_is_teed_to_the_log_untouched(self) -> None:
        source = self.render_fixture("acme-run")
        self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), "--pane", "wAC:p1", FAKE_CLAUDE_FIXTURE=str(source), **self.herdr())
        self.assertEqual((self.state / "runs/ACME-7.jsonl").read_text(), source.read_text())

    def test_the_metadata_carries_state_task_run_step_turns_and_the_ttl(self) -> None:
        self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", **self.herdr())
        record = self.record("ACME-7")
        meta = self.metadata()
        self.assertEqual(len(meta), 12)  # 11 events and the clear
        for call in meta[:-1]:
            self.assertEqual(call[:7], ["workspace", "report-metadata", "wAC", "--source", "pai-harness", "--token", call[6]])
            self.assertEqual((self.token(call, "task"), self.token(call, "run")), ("ACME-7", record["run_id"]))
            self.assertEqual(call[call.index("--ttl-ms") + 1], "120000")
        self.assertEqual(self.token(meta[0], "state"), "working")
        edit = next(c for c in meta if self.token(c, "step").startswith("Edit "))
        self.assertEqual((self.token(edit, "step"), self.token(edit, "turns")), ("Edit apps/acme-storefront/src/checkout/totals.ts", "3"))
        self.assertEqual((self.token(meta[-2], "state"), self.token(meta[-2], "turns")), ("done", "4"))
        clear = meta[-1]
        self.assertEqual([clear[i + 1] for i, a in enumerate(clear) if a == "--clear-token"], ["state", "task", "run", "step", "turns"])
        self.assertNotIn("--token", clear)

    def test_a_fresh_pane_shell_is_handed_the_config_state_dir_and_settings(self) -> None:
        self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", PAI_HARNESS_INIT_TIMEOUT="30", **self.herdr())
        command = next(c for c in self.calls() if c[:2] == ["pane", "run"])[3]
        self.assertTrue(command.startswith("env "), command)
        for expected in (f"PAI_HARNESS_CONFIG={self.env['PAI_HARNESS_CONFIG']}", f"PAI_HARNESS_STATE_DIR={self.state}", "PAI_HARNESS_INIT_TIMEOUT=30",
                         "--herdr-workspace wAC", "--herdr-tab wAC:t2"):
            self.assertIn(expected, command)

    def test_the_tab_label_tracks_the_state(self) -> None:
        self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", **self.herdr())
        renames = [c for c in self.calls() if c[:2] == ["tab", "rename"]]
        self.assertEqual(renames, [["tab", "rename", "wAC:t2", "ACME-7 · working"], ["tab", "rename", "wAC:t2", "ACME-7 · done"]])

    def test_a_failed_run_ends_the_tab_failed_whatever_the_frame_said(self) -> None:
        done = self.run_fixture("ACME-9", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", exit_code=2, **self.herdr())
        self.assertEqual(done.returncode, 1)
        self.assertEqual(self.record("ACME-9")["state"], "failed")
        labels = [c[3] for c in self.calls() if c[:2] == ["tab", "rename"]]
        self.assertEqual(labels[-1], "ACME-9 · failed")
        self.assertEqual(self.calls()[-3][:2], ["tab", "rename"])  # then the tokens are cleared, then wait-output
        self.assertIn("--clear-token", self.metadata()[-1])

    def test_a_blocked_run_labels_the_tab_blocked(self) -> None:
        self.run_fixture("ACME-8", RENDER / "acme-blocked.jsonl", "--pane", "wAC:p1", **self.herdr())
        self.assertEqual(self.record("ACME-8")["state"], "blocked")
        self.assertEqual([c[3] for c in self.calls() if c[:2] == ["tab", "rename"]][-1], "ACME-8 · blocked")

    def test_inside_herdr_without_a_pane_the_launcher_opens_its_own_tab(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", HERDR_ENV="1", HERDR_WORKSPACE_ID="wAC", **self.herdr())
        self.assertEqual(done.returncode, 0, done.stderr)
        calls = self.calls()
        self.assertEqual(calls[0][:2], ["tab", "create"])
        self.assertEqual(calls[0][calls[0].index("--workspace") + 1], "wAC")
        self.assertEqual(calls[0][calls[0].index("--label") + 1], "ACME-7 · starting")
        self.assertNotIn("--focus", calls[0])
        self.assertEqual(calls[1][:3], ["pane", "run", "wAC:p9"])
        self.assertEqual([c[2] for c in self.metadata()][:1], ["wAC"])
        self.assertEqual([c[2] for c in calls if c[:2] == ["tab", "rename"]], ["wAC:t3", "wAC:t3"])
        self.assertIn("■ result done", done.stderr)

    def test_outside_herdr_the_run_is_in_the_foreground_with_the_same_lines_and_no_herdr_calls(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", **self.herdr())
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("■ result done turns=4", done.stderr)
        self.assertEqual(self.calls(), [])

    def test_a_tab_that_cannot_be_opened_falls_back_to_this_terminal(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", HERDR_ENV="1", **self.herdr(FAKE_HERDR_FAIL="1"))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("could not open a Herdr tab", done.stderr)
        self.assertIn("■ result done turns=4", done.stderr)
        self.assertEqual(self.record("ACME-7")["state"], "done")

    def test_a_herdr_that_fails_never_changes_the_record(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--pane", "wAC:p1", **self.herdr(FAKE_HERDR_FAIL="1"))
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(self.record("ACME-7")["state"], "done")

    def test_the_self_check_failure_is_shown_and_the_tab_ends_failed(self) -> None:
        broken = self.tmp / "broken.jsonl"
        broken.write_text(self.render_fixture("acme-run").read_text().replace("pai-harness:", "other:"))
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), "--pane", "wAC:p1", FAKE_CLAUDE_FIXTURE=str(broken), **self.herdr())
        self.assertIn("BLOCKER ACME-7: pai-harness self-check failed", done.stdout)
        self.assertIn("■ record failed self-check:", done.stderr)
        self.assertEqual([c[3] for c in self.calls() if c[:2] == ["tab", "rename"]][-1], "ACME-7 · failed")
        self.assertEqual(self.record("ACME-7")["state"], "failed")

    def test_a_writing_role_outside_a_worktree_is_refused_before_any_tab_opens(self) -> None:
        outside = self.tmp / "plain"
        outside.mkdir()
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--cwd", str(outside), HERDR_ENV="1", **self.herdr())
        self.assertEqual(done.returncode, 1)
        self.assertIn("BLOCKER ACME-7: writing role implementer must run inside a git worktree", done.stderr)
        self.assertEqual(self.calls(), [])

    def test_the_dry_run_opens_nothing(self) -> None:
        done = self.run_fixture("ACME-7", RENDER / "acme-run.jsonl", "--dry-run", HERDR_ENV="1", **self.herdr())
        self.assertEqual(done.returncode, 0)
        self.assertEqual(self.calls(), [])


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
