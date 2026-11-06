"""ATE-1204: headless runs reach the Pai MCP with a machine token; the helper refuses bad files and the launcher fails closed.

Every token here is FICTIONAL. The tests assert it never reaches the launcher's output, the journal, the stream log or any state file.
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, SCRIPTS, HarnessCase  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import harness_config as hc  # noqa: E402
import harness_lib as lib  # noqa: E402
import mcp_headers  # noqa: E402

FAKE_TOKEN = "pai_st_FAKE_ACME"
PAI_CONFIG = FIXTURES / "acme-pai.pai-harness.toml"


def header_line(token: str = FAKE_TOKEN) -> str:
    return json.dumps({"Authorization": f"Bearer {token}"}, separators=(",", ":")) + "\n"


class TokenCase(HarnessCase):
    def setUp(self) -> None:
        super().setUp()
        self.token = self.tmp / "token"
        self.write_token()
        self.env.pop("PAI_HARNESS_TOKEN_FILE", None)

    def write_token(self, text: str = FAKE_TOKEN + "\n", mode: int = 0o600) -> Path:
        self.token.unlink(missing_ok=True)
        self.token.write_text(text)
        os.chmod(self.token, mode)
        return self.token

    def helper(self, *args: str, **env: str) -> subprocess.CompletedProcess:
        return self.run_script("mcp_headers.sh", *args, PAI_HARNESS_TOKEN_FILE=str(self.token), **env)

    def assert_clean(self, done: subprocess.CompletedProcess | None = None) -> None:
        """The fictional token appears in no output, journal, stream log, state or MCP config of the run."""
        if done is not None:
            self.assertNotIn(FAKE_TOKEN, done.stdout)
            self.assertNotIn(FAKE_TOKEN, done.stderr)
        for path in self.state.rglob("*"):
            if path.is_file():
                self.assertNotIn(FAKE_TOKEN, path.read_text(errors="replace"), str(path))


class HelperTest(TokenCase):
    def test_prints_only_the_authorization_header(self) -> None:
        done = self.helper()
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(done.stdout, header_line())
        self.assertEqual(json.loads(done.stdout), {"Authorization": f"Bearer {FAKE_TOKEN}"})
        self.assertEqual(done.stderr, "")

    def test_a_trailing_newline_or_crlf_is_not_part_of_the_value(self) -> None:
        self.write_token(FAKE_TOKEN + "\r\n")
        self.assertEqual(self.helper().stdout, header_line())

    def test_wrong_mode_is_refused_and_the_value_is_never_echoed(self) -> None:
        for mode in (0o644, 0o640, 0o660, 0o400, 0o700, 0o666):
            self.write_token(mode=mode)
            done = self.helper()
            self.assertEqual((done.returncode, done.stdout), (1, ""), oct(mode))
            self.assertIn("must be 0600", done.stderr)
            self.assertNotIn(FAKE_TOKEN, done.stderr)

    def test_wrong_owner_is_refused(self) -> None:
        with mock.patch.object(mcp_headers.os, "geteuid", return_value=os.geteuid() + 1):
            with self.assertRaises(mcp_headers.Refused) as caught:
                mcp_headers.read_token(self.token)
        self.assertIn("not owned by the current user", str(caught.exception))
        self.assertNotIn(FAKE_TOKEN, str(caught.exception))

    def test_wrong_owner_through_main_prints_nothing_on_stdout(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, {"PAI_HARNESS_TOKEN_FILE": str(self.token)}), \
                mock.patch.object(mcp_headers.os, "geteuid", return_value=os.geteuid() + 1), redirect_stdout(out), redirect_stderr(err):
            code = mcp_headers.main([])
        self.assertEqual((code, out.getvalue()), (1, ""))
        self.assertNotIn(FAKE_TOKEN, err.getvalue())

    def test_a_missing_file_fails_closed_with_nothing_on_stdout(self) -> None:
        self.token.unlink()
        done = self.helper()
        self.assertEqual((done.returncode, done.stdout), (1, ""))
        self.assertIn("is missing", done.stderr)

    def test_a_symlink_a_directory_and_a_bad_value_are_refused(self) -> None:
        link = self.tmp / "link"
        link.symlink_to(self.token)
        self.assertEqual(self.run_script("mcp_headers.sh", PAI_HARNESS_TOKEN_FILE=str(link)).stdout, "")
        self.assertNotEqual(self.run_script("mcp_headers.sh", PAI_HARNESS_TOKEN_FILE=str(link)).returncode, 0)
        self.assertNotEqual(self.run_script("mcp_headers.sh", PAI_HARNESS_TOKEN_FILE=str(self.tmp)).returncode, 0)
        for bad in ("", "\n", "two words", "line1\nline2\n", "tok\x00en", "tök"):
            self.write_token(bad)
            done = self.helper()
            self.assertEqual((done.returncode, done.stdout), (1, ""), repr(bad))

    def test_the_config_names_the_file_and_the_environment_overrides_it(self) -> None:
        config = self.tmp / ".pai-harness.toml"
        config.write_text((FIXTURES / "acme.pai-harness.toml").read_text().rstrip("\n") + f'\n\n[pai]\ntoken_file = "{self.token}"\n')
        env = {k: v for k, v in self.env.items() if k != "PAI_HARNESS_TOKEN_FILE"}
        done = subprocess.run([str(SCRIPTS / "mcp_headers.sh"), "--config", str(config)], capture_output=True, text=True, env=env)
        self.assertEqual((done.returncode, done.stdout), (0, header_line()))
        other = self.tmp / "other"
        other.write_text("pai_st_FAKE_OTHER\n")
        os.chmod(other, 0o600)
        done = subprocess.run([str(SCRIPTS / "mcp_headers.sh"), "--config", str(config)], capture_output=True, text=True,
                              env={**env, "PAI_HARNESS_TOKEN_FILE": str(other)})
        self.assertEqual(done.stdout, header_line("pai_st_FAKE_OTHER"))

    def test_a_bad_config_fails_closed(self) -> None:
        bad = self.tmp / "bad.toml"
        bad.write_text("not toml [[")
        env = {k: v for k, v in self.env.items() if k != "PAI_HARNESS_TOKEN_FILE"}
        done = subprocess.run([str(SCRIPTS / "mcp_headers.sh"), "--config", str(bad)], capture_output=True, text=True, env=env)
        self.assertEqual((done.returncode, done.stdout), (1, ""))

    def test_unknown_arguments_are_a_usage_error_with_nothing_on_stdout(self) -> None:
        done = self.helper("--print-token")
        self.assertEqual((done.returncode, done.stdout), (2, ""))


class ConfigTest(unittest.TestCase):
    BASE = '[project]\npai_org = "acme"\npai_project = "acme-app"\nlinear_team = "ACME"\n'

    def test_defaults(self) -> None:
        pai = hc.validate(hc.tomllib.loads(self.BASE))["pai"]
        self.assertEqual(pai, {"token_file": "~/.config/pai-harness/token", "mcp_url": "", "token_scope": "write"})

    def test_values_and_refusals(self) -> None:
        ok = hc.validate(hc.tomllib.loads(self.BASE + '[pai]\ntoken_file = "/srv/acme/token"\nmcp_url = "https://mcp.acme.example.com/mcp"\n'))
        self.assertEqual(ok["pai"], {"token_file": "/srv/acme/token", "mcp_url": "https://mcp.acme.example.com/mcp", "token_scope": "write"})
        hc.validate(hc.tomllib.loads(self.BASE + '[pai]\nmcp_url = "http://localhost:3000/mcp"\n'))
        for text, fragment in (
            ('mcp_url = "http://mcp.acme.example.com/mcp"', "pai.mcp_url: must be an https URL"),
            ('mcp_url = "https://user:secret@mcp.acme.example.com/mcp"', "no credentials"),
            ('mcp_url = "ftp://x"', "pai.mcp_url"),
            ('mcp_url = 3', "pai.mcp_url: expected string"),
            ('token_file = ""', "pai.token_file: must not be empty"),
            ('token = "x"', "pai.token: unknown key"),
        ):
            with self.assertRaises(hc.ConfigError, msg=text) as caught:
                hc.validate(hc.tomllib.loads(self.BASE + f"[pai]\n{text}\n"))
            self.assertIn(fragment, str(caught.exception))

    def test_schema_matches(self) -> None:
        schema = json.loads((SCRIPTS.parent / "schema/pai-harness.schema.json").read_text())["properties"]["pai"]
        self.assertEqual(sorted(schema["properties"]), sorted(hc.DEFAULTS["pai"]))
        self.assertEqual(schema["properties"]["token_file"]["default"], hc.DEFAULTS["pai"]["token_file"])
        self.assertFalse(schema["additionalProperties"])

    def test_the_acme_example_validates_and_is_fictional(self) -> None:
        loaded = hc.load_file(SCRIPTS.parent / "examples/acme/.pai-harness.toml")
        self.assertEqual(loaded["pai"]["mcp_url"], "https://mcp.acme.example.com/mcp")


class InitCheckTest(unittest.TestCase):
    def frame(self, **change: object) -> dict:
        base = {"mcp_servers": [{"name": "pai", "status": "connected"}], "tools": ["Read", "mcp__pai__whoami"]}
        return {**base, **change}

    def test_connected_with_tools_passes(self) -> None:
        self.assertEqual(lib.mcp_problems(self.frame()), [])

    def test_every_other_state_fails(self) -> None:
        cases = (
            (self.frame(mcp_servers=[]), "server pai is not in init mcp_servers"),
            (self.frame(mcp_servers=None), "server pai is not in init mcp_servers"),
            (self.frame(mcp_servers=[{"name": "other", "status": "connected"}]), "server pai is not in init mcp_servers"),
            (self.frame(mcp_servers=[{"name": "pai", "status": "needs-auth"}]), "server pai status is needs-auth, not connected"),
            (self.frame(mcp_servers=[{"name": "pai", "status": "failed"}]), "not connected"),
            (self.frame(mcp_servers=[{"name": "pai"}]), "status is missing"),
            (self.frame(tools=["Read", "mcp__other__whoami"]), "no mcp__pai__* tools listed"),
            (self.frame(tools=[]), "no mcp__pai__* tools listed"),
        )
        for frame, fragment in cases:
            self.assertIn(fragment, "; ".join(lib.mcp_problems(frame)), frame)


class LauncherTest(TokenCase):
    def setUp(self) -> None:
        super().setUp()
        self.env["PAI_HARNESS_CONFIG"] = str(PAI_CONFIG)
        self.env["PAI_HARNESS_TOKEN_FILE"] = str(self.token)
        self.env["FAKE_CLAUDE_RUN_HELPER"] = "1"

    def argv(self) -> list[str]:
        return json.loads((self.tmp / "claude.json").read_text())["argv"]

    def helper_report(self) -> dict:
        return json.loads((self.tmp / "claude.json.helper").read_text())

    def test_connected_run_passes_a_strict_machine_only_mcp_config(self) -> None:
        done = self.launch("ACME-7", "pai_connected")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        argv = self.argv()
        self.assertIn("--strict-mcp-config", argv)
        path = Path(argv[argv.index("--mcp-config") + 1])
        self.assertEqual(path, self.state / "mcp/ACME-7.json")
        servers = json.loads(path.read_text())["mcpServers"]
        self.assertEqual(list(servers), ["pai"])
        self.assertEqual(servers["pai"]["type"], "http")
        self.assertEqual(servers["pai"]["url"], "https://mcp.acme.example.com/mcp")
        self.assertIn("mcp_headers.sh", servers["pai"]["headersHelper"])
        self.assertNotIn("headers", servers["pai"])  # never a static header
        self.assertEqual(self.record("ACME-7")["state"], "done")
        self.assertFalse([e for e in self.journal() if e["kind"] == "BLOCKER"])
        self.assertEqual(self.helper_report(), {"rc": 0, "keys": ["Authorization"], "stdout_empty": False})
        self.assert_clean(done)

    def test_the_stream_log_the_journal_and_the_output_never_hold_the_token(self) -> None:
        done = self.launch("ACME-7", "pai_connected")
        self.assertTrue((self.state / "runs/ACME-7.jsonl").is_file())
        self.assert_clean(done)

    def test_a_missing_token_file_stops_the_run_with_a_named_blocker(self) -> None:
        self.token.unlink()
        done = self.launch("ACME-7", "pai_not_connected")
        self.assertEqual(self.helper_report()["rc"], 1)
        self.assertTrue(self.helper_report()["stdout_empty"])
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("BLOCKER ACME-7: pai mcp not connected: server pai status is failed, not connected", done.stdout)
        self.assertEqual(self.record("ACME-7")["state"], "failed")
        self.assert_clean(done)

    def test_a_token_with_the_wrong_mode_stops_the_run(self) -> None:
        self.write_token(mode=0o644)
        done = self.launch("ACME-7", "pai_not_connected")
        self.assertEqual(self.helper_report()["rc"], 1)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("BLOCKER ACME-7: pai mcp not connected", done.stdout)
        self.assert_clean(done)

    def test_each_init_failure_fails_closed_with_one_journaled_blocker(self) -> None:
        frames = [json.loads(line) for line in self.fixture("pai_connected").read_text().splitlines()]
        cases = {
            "absent": ({"mcp_servers": []}, "server pai is not in init mcp_servers"),
            "needs-auth": ({"mcp_servers": [{"name": "pai", "status": "needs-auth"}]}, "status is needs-auth"),
            "no-tools": ({"tools": ["Read"]}, "no mcp__pai__* tools listed"),
        }
        for name, (change, fragment) in cases.items():
            with self.subTest(name):
                broken = self.tmp / f"{name}.jsonl"
                broken.write_text("\n".join(json.dumps({**frames[0], **change}) if i == 0 else json.dumps(f) for i, f in enumerate(frames)) + "\n")
                done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), FAKE_CLAUDE_FIXTURE=str(broken))
                self.assertNotEqual(done.returncode, 0)
                self.assertIn("BLOCKER ACME-7: pai mcp not connected", done.stdout)
                self.assertIn(fragment, done.stdout)
                self.assertEqual(self.record("ACME-7")["state"], "failed")
                self.assertEqual(len([e for e in self.journal() if e["kind"] == "BLOCKER"]), 1)
                (self.state / "journal.jsonl").unlink()
                self.assert_clean(done)

    def test_a_plugin_problem_and_an_mcp_problem_are_both_named(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt),
                               FAKE_CLAUDE_FIXTURE=str(self.fixture("success", drop_skill="pai-harness:lead")))
        self.assertIn("pai-harness self-check failed: skill pai-harness:lead not loaded", done.stdout)
        self.assertIn("pai mcp not connected: server pai is not in init mcp_servers", done.stdout)

    def test_without_mcp_url_no_mcp_flags_are_passed_and_no_check_runs(self) -> None:
        self.env["PAI_HARNESS_CONFIG"] = str(FIXTURES / "acme.pai-harness.toml")
        done = self.launch("ACME-7", "success")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertNotIn("--mcp-config", self.argv())
        self.assertNotIn("--strict-mcp-config", self.argv())
        self.assertFalse((self.state / "mcp").exists())

    def test_dry_run_shows_the_strict_flags_and_writes_nothing(self) -> None:
        done = self.run_script("launch.sh", "ACME-7", "--prompt-file", str(self.prompt), "--dry-run")
        plan = json.loads(done.stdout)
        self.assertIn("--strict-mcp-config", plan["command"])
        self.assertEqual(plan["command"][plan["command"].index("--mcp-config") + 1], str(self.state / "mcp/ACME-7.json"))
        self.assertFalse((self.state / "mcp").exists())
        self.assertNotIn(FAKE_TOKEN, done.stdout)

    def test_resume_keeps_the_strict_config(self) -> None:
        self.launch("ACME-7", "pai_connected")
        self.launch("ACME-7", "pai_connected", 0, "--resume")
        self.assertIn("--strict-mcp-config", self.argv())
        self.assertIn("--resume", self.argv())


if __name__ == "__main__":
    unittest.main()
