"""Health check, dispatcher, gate request, Linear status and the command files."""
from __future__ import annotations

import http.server
import json
import subprocess
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, ROOT, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_lib as lib  # noqa: E402

COMMANDS = ROOT / "plugins/pai-harness/commands"
SHA = "0123456789abcdef0123456789abcdef01234567"


class HealthTest(HarnessCase):
    def test_a_fresh_beat_is_healthy_and_a_16_minute_old_running_entry_is_stale(self) -> None:
        self.assertEqual(self.run_script("health.sh", "beat", "ACME-7", "--state", "running").returncode, 0)
        beat = lib.read_json(self.state / "registry/ACME-7.json")["heartbeat"]
        self.assertEqual(self.run_script("health.sh", "check").returncode, 0)
        at = lib.stamp(lib.parse_stamp(beat) + lib.timedelta(minutes=14))
        self.assertEqual(self.run_script("health.sh", "check", "--now", at).returncode, 0)
        late = lib.stamp(lib.parse_stamp(beat) + lib.timedelta(minutes=16))
        stale = self.run_script("health.sh", "check", "--now", late)
        self.assertEqual(stale.returncode, 1)
        self.assertTrue(json.loads(stale.stdout)["entries"][0]["stale"])

    def test_a_finished_entry_is_never_stale(self) -> None:
        self.run_script("health.sh", "beat", "ACME-7", "--state", "done")
        self.assertEqual(self.run_script("health.sh", "check", "--now", "2030-01-01T00:00:00Z").returncode, 0)

    def test_an_empty_registry_is_exit_2_and_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.run_script("health.sh", "check").returncode, 2)
        self.assertEqual(self.run_script("health.sh", "beat", "ACME-7", "--dry-run").returncode, 0)
        self.assertFalse((self.state / "registry").exists())


class DispatcherTest(HarnessCase):
    def ready(self, *issues: str) -> str:
        return "# ready\n" + "".join(f"{i} prompt-file={self.prompt}\n" for i in issues)

    def dispatch(self, text: str, *args: str, queue: str = "main") -> subprocess.CompletedProcess:
        return self.run_script("dispatcher.sh", "--queue", queue, *args, stdin=text, FAKE_CLAUDE_FIXTURE=str(self.fixture("success")))

    def test_launches_at_most_the_queue_limit(self) -> None:
        done = self.dispatch(self.ready("ACME-1", "ACME-2", "ACME-3"), "--dry-run")
        plan = json.loads(done.stdout)
        self.assertEqual([i["issue"] for i in plan["launch"]], ["ACME-1", "ACME-2"])
        self.assertEqual(plan["skipped"], [{"issue": "ACME-3", "why": "no capacity"}])
        self.assertFalse(self.state.exists())

    def test_running_entries_use_up_the_machine_limit(self) -> None:
        self.run_script("health.sh", "beat", "ACME-9", "--state", "running")
        lib.register(self.state, "ACME-9", state="running", queue="main", machine="acme-desktop")
        plan = json.loads(self.dispatch(self.ready("ACME-1", "ACME-2"), "--dry-run").stdout)
        self.assertEqual([i["issue"] for i in plan["launch"]], ["ACME-1"])

    def test_a_queue_without_a_machine_obeys_the_global_limit(self) -> None:
        for n in (7, 8):
            lib.register(self.state, f"ACME-{n}", state="running", queue="main", machine="acme-desktop")
        plan = json.loads(self.dispatch(self.ready("ACME-1", "ACME-2"), "--dry-run", queue="side").stdout)
        self.assertEqual(len(plan["launch"]), 1)  # global max 3, 2 running; side limit 1
        lib.register(self.state, "ACME-6", state="running", queue="side")
        plan = json.loads(self.dispatch(self.ready("ACME-1"), "--dry-run", queue="side").stdout)
        self.assertEqual(plan["capacity"], 0)

    def test_a_stale_running_entry_does_not_hold_a_slot(self) -> None:
        lib.write_json(self.state / "registry/ACME-9.json", {"name": "ACME-9", "state": "running", "queue": "main",
                                                             "machine": "acme-desktop", "heartbeat": "2020-01-01T00:00:00Z"})
        self.assertEqual(json.loads(self.dispatch(self.ready("ACME-1"), "--dry-run").stdout)["capacity"], 2)

    def test_skips_running_issues_and_lines_without_a_prompt(self) -> None:
        lib.register(self.state, "ACME-1", state="running", queue="main", machine="acme-desktop")
        plan = json.loads(self.dispatch(self.ready("ACME-1") + "ACME-2\n", "--dry-run").stdout)
        self.assertEqual([s["why"] for s in plan["skipped"]], ["already running", "no prompt-file"])

    def test_wait_launches_through_the_launcher(self) -> None:
        done = self.dispatch(self.ready("ACME-1", "ACME-2"), "--wait")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual([self.record(i)["state"] for i in ("ACME-1", "ACME-2")], ["done", "done"])
        self.assertIn("dispatch", [e["kind"] for e in self.journal()])

    def test_unknown_queue_is_refused(self) -> None:
        self.assertEqual(self.dispatch("", queue="nope").returncode, 2)


class GateRequestTest(HarnessCase):
    def test_asks_every_configured_gate_by_exact_sha(self) -> None:
        done = self.run_script("gate-request.sh", "--sha", SHA, "--issue", "ACME-7")
        self.assertEqual(done.returncode, 0, done.stderr)
        event = self.journal()[0]
        self.assertEqual((event["kind"], event["sha"], sorted(event["gates"])), ("gate.requested", SHA, ["lint", "unit"]))
        self.assertEqual(event["gates"]["lint"], ["true", "true"])

    def test_refuses_branches_and_abbreviations(self) -> None:
        for bad in ("main", SHA[:9], SHA.upper(), ""):
            self.assertEqual(self.run_script("gate-request.sh", "--sha", bad).returncode, 2, bad)

    def test_unknown_gate_is_refused_and_dry_run_writes_nothing(self) -> None:
        self.assertEqual(self.run_script("gate-request.sh", "--sha", SHA, "--gate", "e2e").returncode, 2)
        done = self.run_script("gate-request.sh", "--sha", SHA, "--gate", "unit", "--dry-run")
        self.assertEqual(json.loads(done.stdout)["gates"], {"unit": ["true"]})
        self.assertFalse(self.state.exists())

    def test_root_flag_reports_root_zone_and_root_path_hits(self) -> None:
        files = "apps/acme-app/page.tsx\npackages/contracts/api.ts\ndb/migrations/001.sql\n"
        done = self.run_script("gate-request.sh", "--sha", SHA, "--root", "--dry-run", stdin=files)
        self.assertEqual(json.loads(done.stdout)["root"], {"touches_root": True, "files": ["packages/contracts/api.ts", "db/migrations/001.sql"]})
        done = self.run_script("gate-request.sh", "--sha", SHA, "--root", "--dry-run", stdin="apps/acme-app/page.tsx\n")
        self.assertFalse(json.loads(done.stdout)["root"]["touches_root"])

    def test_run_needs_the_checkout_at_that_sha_and_records_the_verdict(self) -> None:
        repo = self.tmp / "repo"
        repo.mkdir()
        git = lambda *a: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True).stdout.strip()  # noqa: E731
        git("init", "-q")
        git("-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "x")
        head = git("rev-parse", "HEAD")
        wrong = self.run_script("gate-request.sh", "--sha", SHA, "--run", "--cwd", str(repo))
        self.assertEqual(wrong.returncode, 2)
        right = self.run_script("gate-request.sh", "--sha", head, "--run", "--cwd", str(repo), "--gate", "unit")
        self.assertEqual(right.returncode, 0, right.stderr)
        self.assertEqual(json.loads(right.stdout)["verdict"], "PASS")
        self.assertEqual(self.journal()[-1]["kind"], "gate.result")

    def test_a_failing_gate_command_gives_fail_and_exit_1(self) -> None:
        repo = self.tmp / "repo"
        repo.mkdir()
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.com", "commit", "-q", "--allow-empty", "-m", "x"], check=True)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        failing = self.tmp / "fail.toml"
        failing.write_text((FIXTURES / "acme.pai-harness.toml").read_text().replace('unit = "true"', 'unit = "false"'))
        done = self.run_script("gate-request.sh", "--sha", head, "--run", "--cwd", str(repo), "--config", str(failing))
        self.assertEqual(done.returncode, 1)
        self.assertEqual(json.loads(done.stdout)["verdict"], "FAIL")


class LinearStatusTest(HarnessCase):
    def test_three_lines_and_none_for_empty(self) -> None:
        done = self.run_script("linear-status.sh", "ACME-7", "--done", "built  the\nthing", "--next", "gate")
        self.assertEqual(done.stdout.splitlines(), ["Done: built the thing", "Next: gate", "Blocked: none"])

    def test_from_run_reads_the_recorded_state(self) -> None:
        self.launch("ACME-8", "permission", 0)
        lines = self.run_script("linear-status.sh", "ACME-8", "--from-run").stdout.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertEqual(lines[2], "Blocked: denied by policy or not pre-approved: Bash; report BLOCKER, do not work around it")

    def test_prints_only_without_a_token(self) -> None:
        done = self.run_script("linear-status.sh", "ACME-7", "--done", "x", LINEAR_API_URL="http://127.0.0.1:9/")
        self.assertEqual((done.returncode, done.stderr), (0, ""))

    def test_posts_when_the_token_and_endpoint_are_set(self) -> None:
        seen = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                seen.append((self.headers["Authorization"], json.loads(self.rfile.read(int(self.headers["Content-Length"])))))
                body = b'{"data":{"commentCreate":{"success":true}}}'
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args: object) -> None:
                pass

        server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        done = self.run_script("linear-status.sh", "ACME-7", "--done", "x", LINEAR_API_KEY="token-acme",
                               LINEAR_API_URL=f"http://127.0.0.1:{server.server_port}/")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(seen[0][0], "token-acme")
        self.assertEqual(seen[0][1]["variables"], {"issueId": "ACME-7", "body": "Done: x\nNext: none\nBlocked: none"})

    def test_a_post_failure_still_prints_and_exits_1(self) -> None:
        done = self.run_script("linear-status.sh", "ACME-7", "--done", "x", LINEAR_API_KEY="token-acme", LINEAR_API_URL="http://127.0.0.1:9/")
        self.assertEqual(done.returncode, 1)
        self.assertTrue(done.stdout.startswith("Done: x"))
        self.assertNotIn("token-acme", done.stderr)


class CommandFilesTest(unittest.TestCase):
    NAMES = ("task-start", "task-done", "gate", "root-review", "park", "resume")

    def test_every_command_has_frontmatter_and_calls_a_script_that_exists(self) -> None:
        for name in self.NAMES:
            text = (COMMANDS / f"{name}.md").read_text()
            self.assertTrue(text.startswith("---\ndescription: "), name)
            scripts = {s.split("/")[-1] for s in __import__("re").findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/scripts/[\w.-]+", text)}
            self.assertTrue(scripts, name)
            for script in scripts:
                self.assertTrue((SCRIPTS / script).is_file(), f"{name} calls missing {script}")

    def test_every_script_has_a_dry_run_and_is_executable(self) -> None:
        for sh in ("launch", "health", "dispatcher", "gate-request", "linear-status", "task-done"):
            path = SCRIPTS / f"{sh}.sh"
            self.assertTrue(path.stat().st_mode & 0o111, sh)
            self.assertIn("--dry-run", subprocess.run([str(path), "--help"], capture_output=True, text=True).stdout, sh)

    def test_scripts_never_use_a_temporary_directory(self) -> None:
        for path in SCRIPTS.glob("*.py"):
            self.assertNotIn("/tmp", path.read_text(), path.name)
            self.assertNotIn("tempfile", path.read_text(), path.name)


if __name__ == "__main__":
    unittest.main()
