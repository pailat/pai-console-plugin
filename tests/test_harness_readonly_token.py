"""Read-only machine token (ATE-1206): scope config, the report command with its named BLOCKER, and the Stop marker reason."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_harness_zone_diff import ZoneDiffCase

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / "plugins/pai-harness"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
SCRIPT = str(HARNESS / "scripts/delta_marker.py")
CANDIDATES = str(FIXTURES / "harness-distiller/candidates.json")
CONFIG = str(FIXTURES / "harness/knowledge.pai-harness.toml")
BLOCKER = "knowledge write needs a project-scope write token"
sys.path.insert(0, str(HARNESS / "scripts"))
import harness_config as hc  # noqa: E402


class ScopeConfigTest(unittest.TestCase):
    BASE = '[project]\npai_org = "acme"\npai_project = "acme-app"\nlinear_team = "ACME"\n'

    def test_default_is_write_and_values_validate(self) -> None:
        self.assertEqual(hc.validate(hc.tomllib.loads(self.BASE))["pai"]["token_scope"], "write")
        read = hc.validate(hc.tomllib.loads(self.BASE + '[pai]\ntoken_scope = "read"\n'))
        self.assertEqual(hc.token_scope(read, {}), "read")
        with self.assertRaisesRegex(hc.ConfigError, "pai.token_scope: must be one of read, write"):
            hc.validate(hc.tomllib.loads(self.BASE + '[pai]\ntoken_scope = "admin"\n'))

    def test_environment_overrides_and_fails_closed(self) -> None:
        write = hc.validate(hc.tomllib.loads(self.BASE))
        self.assertEqual(hc.token_scope(write, {"PAI_HARNESS_TOKEN_SCOPE": "read"}), "read")
        self.assertEqual(hc.token_scope(write, {"PAI_HARNESS_TOKEN_SCOPE": "typo"}), "read")
        read = hc.validate(hc.tomllib.loads(self.BASE + '[pai]\ntoken_scope = "read"\n'))
        self.assertEqual(hc.token_scope(read, {"PAI_HARNESS_TOKEN_SCOPE": "write"}), "write")

    def test_schema_and_example_carry_it(self) -> None:
        schema = json.loads((HARNESS / "schema/pai-harness.schema.json").read_text())["properties"]["pai"]["properties"]["token_scope"]
        self.assertEqual((schema["enum"], schema["default"]), (["read", "write"], "write"))
        example = hc.load_file(HARNESS / "examples/acme/.pai-harness.toml")
        self.assertEqual(example["pai"]["token_scope"], "write")


class ReportTest(unittest.TestCase):
    def run_marker(self, tmp: str, *args: str, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([sys.executable, SCRIPT, "--config", CONFIG, *args], capture_output=True, text=True,
                              env={"PAI_HARNESS_STATE_DIR": tmp, "PATH": "/usr/bin:/bin", **env})

    def test_scope_read_saves_the_report_and_prints_the_blocker(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(tmp, "report", "acme-42", CANDIDATES, PAI_HARNESS_TOKEN_SCOPE="read")
            self.assertEqual(done.returncode, 3, done.stderr)
            self.assertIn(f"BLOCKER acme-42: {BLOCKER}", done.stdout)
            report = json.loads((Path(tmp) / "deltas/acme-42.report.json").read_text())
            self.assertEqual((report["blocker"], report["reason"], report["turn"]), (BLOCKER, "token scope read", "turn-acme-0142"))
            self.assertEqual([n["ref"] for n in report["nodes"]], ["$retry", "$swallow", "$clock"])
            self.assertFalse((Path(tmp) / "deltas/acme-42.json").exists())
            self.assertIn(BLOCKER, (Path(tmp) / "journal.jsonl").read_text())

    def test_denied_write_maps_to_the_same_blocker_and_keeps_the_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(tmp, "report", "acme-42", CANDIDATES, "--denied")
            self.assertEqual(done.returncode, 3)
            self.assertIn(BLOCKER, done.stdout)
            self.assertEqual(json.loads((Path(tmp) / "deltas/acme-42.report.json").read_text())["reason"], "permission denied")

    def test_scope_read_refuses_a_marker_for_unwritten_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            done = self.run_marker(tmp, "write", "acme-42", "kn-acme-0031", PAI_HARNESS_TOKEN_SCOPE="read")
            self.assertEqual(done.returncode, 3)
            self.assertIn(BLOCKER, done.stdout)
            self.assertFalse((Path(tmp) / "deltas/acme-42.json").exists())

    def test_scope_write_keeps_the_normal_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {"PAI_HARNESS_KNOWLEDGE_ORG": "acme", "PAI_HARNESS_KNOWLEDGE_PROJECT": "acme-app"}
            ok = self.run_marker(tmp, "write", "acme-42", "kn-acme-0031", PAI_HARNESS_TOKEN_SCOPE="write", **env)
            self.assertEqual(ok.returncode, 0, ok.stdout + ok.stderr)
            self.assertEqual(json.loads((Path(tmp) / "deltas/acme-42.json").read_text()), {"nodes": ["kn-acme-0031"]})
            self.assertFalse((Path(tmp) / "deltas/acme-42.report.json").exists())

    def test_a_bad_candidate_file_is_not_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({"turn": "turn-acme-0142", "nodes": [{"ref": "$x", "kind": "lesson", "title": "t", "summary": "s", "sources": []}]}))
            done = self.run_marker(tmp, "report", "acme-42", str(bad))
            self.assertEqual(done.returncode, 1)
            self.assertFalse((Path(tmp) / "deltas/acme-42.report.json").exists())

    def test_text_names_the_blocker(self) -> None:
        for relative in ("skills/distiller/SKILL.md", "agents/distiller.md"):
            text = (HARNESS / relative).read_text()
            for needle in ("PAI_HARNESS_TOKEN_SCOPE", "delta_marker.py report", "--denied", BLOCKER) if "skills" in relative else ("report", "--denied", BLOCKER):
                self.assertIn(needle, text, relative)


class StopReadOnlyTest(ZoneDiffCase):
    def setUp(self) -> None:
        super().setUp()
        self.delta.unlink()
        (self.state / "deltas/acme-7.report.json").write_text(json.dumps({"blocker": BLOCKER, "nodes": []}))

    def test_a_report_is_not_a_delta_and_the_marker_names_the_reason(self) -> None:
        for _ in range(3):
            result = self.stop()
            self.assertEqual(result["decision"], "block")
            self.assertIn("knowledge write blocked: read-only token", result["reason"])
            self.assertIn(BLOCKER, result["reason"])
        self.assertIsNone(self.stop())  # the 3-block bound is unchanged
        missing = json.loads((self.state / "deltas/acme-7.missing").read_text())
        self.assertEqual(missing["problem"], "knowledge write blocked: read-only token")
        self.assertEqual(missing["blocks"], 3)

    def test_without_a_report_the_reason_stays_generic(self) -> None:
        (self.state / "deltas/acme-7.report.json").unlink()
        for _ in range(3):
            self.stop()
        self.assertIsNone(self.stop())
        self.assertEqual(json.loads((self.state / "deltas/acme-7.missing").read_text())["problem"], "the marker file does not exist")

    def test_a_valid_delta_still_wins(self) -> None:
        self.delta.write_text(json.dumps({"nodes": ["decision/acme-uses-cas"]}))
        self.assertIsNone(self.stop())


if __name__ == "__main__":
    unittest.main()
