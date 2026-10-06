"""Tests of the plugin hooks: python3 -m unittest discover -s tests"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUARD = ROOT / "hooks" / "guard.py"
SESSION_START = ROOT / "hooks" / "session_start.py"

STAGING = "https://mcp-edge-corp-staging.up.railway.app/mcp"
PRODUCTION = "https://mcp-corp.pai.lat/mcp"
PLUGIN = "mcp__plugin_pai-console_pai__"
USER = "mcp__pai-console__"


class HookCase(unittest.TestCase):
    def setUp(self) -> None:
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)

    def run_hook(self, script: Path, event: dict, url: str | None, user_url: str | None = None) -> dict | None:
        env = {"PATH": os.environ["PATH"], "HOME": self.home.name}
        if url is not None:
            env["CLAUDE_PLUGIN_OPTION_MCP_URL"] = url
        if user_url is not None:
            Path(self.home.name, ".claude.json").write_text(
                json.dumps({"mcpServers": {"pai-console": {"type": "http", "url": user_url}}})
            )
        result = subprocess.run(
            [sys.executable, str(script)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            env=env,
            check=True,
        )
        return json.loads(result.stdout) if result.stdout.strip() else None

    def transcript(self, *tool_names: str) -> str:
        path = Path(self.home.name, "transcript.jsonl")
        lines = [
            json.dumps({"type": "user", "message": {"role": "user", "content": "hola"}}),
            *(
                json.dumps(
                    {
                        "type": "assistant",
                        "message": {
                            "role": "assistant",
                            "content": [{"type": "tool_use", "id": f"t{i}", "name": name, "input": {}}],
                        },
                    }
                )
                for i, name in enumerate(tool_names)
            ),
        ]
        path.write_text("\n".join(lines) + "\n")
        return str(path)

    def guard(self, tool: str, url: str | None, tool_input: dict | None = None, transcript: str | None = None, user_url: str | None = None):
        event = {"tool_name": tool, "tool_input": tool_input or {}}
        if transcript is not None:
            event["transcript_path"] = transcript
        return self.run_hook(GUARD, event, url, user_url)

    def decision(self, output: dict | None) -> tuple[str, str] | None:
        if output is None:
            return None
        specific = output["hookSpecificOutput"]
        return specific["permissionDecision"], specific["permissionDecisionReason"]


class GuardTest(HookCase):
    def test_other_tools_pass(self) -> None:
        self.assertIsNone(self.guard("Bash", PRODUCTION))
        self.assertIsNone(self.guard("mcp__plugin_other_pai__page_delete", PRODUCTION))

    def test_staging_writes_pass_without_confirmation(self) -> None:
        self.assertIsNone(self.guard(PLUGIN + "page_update", STAGING))
        self.assertIsNone(self.guard(PLUGIN + "project_delete", STAGING))

    def test_production_reads_pass(self) -> None:
        for tool in ("whoami", "page_read", "knowledge_search", "timeline_get", "page_validate"):
            self.assertIsNone(self.guard(PLUGIN + tool, PRODUCTION), tool)

    def test_production_write_asks(self) -> None:
        decision, reason = self.decision(self.guard(PLUGIN + "page_update", PRODUCTION, {"path": "architecture/payments"}))
        self.assertEqual(decision, "ask")
        self.assertIn("PRODUCCIÓN", reason)
        self.assertIn("architecture/payments", reason)

    def test_production_irreversible_says_so_and_what_it_drags(self) -> None:
        decision, reason = self.decision(self.guard(PLUGIN + "project_delete", PRODUCTION, {"projectId": "p1"}))
        self.assertEqual(decision, "ask")
        self.assertTrue(reason.startswith("IRREVERSIBLE"))
        self.assertIn("pagos y CFDI", reason)
        for tool in ("page_delete", "payment_void", "milestone_delete"):
            decision, reason = self.decision(self.guard(PLUGIN + tool, PRODUCTION))
            self.assertEqual(decision, "ask")
            self.assertTrue(reason.startswith("IRREVERSIBLE"), tool)

    def test_product_deploy_depends_on_target_environment(self) -> None:
        _, reason = self.decision(self.guard(PLUGIN + "product_deploy", PRODUCTION, {"environment": "production"}))
        self.assertTrue(reason.startswith("IRREVERSIBLE"))
        _, reason = self.decision(self.guard(PLUGIN + "product_deploy", PRODUCTION, {"environment": "staging"}))
        self.assertTrue(reason.startswith("ATENCIÓN"))

    def test_unknown_tool_counts_as_write(self) -> None:
        decision, _ = self.decision(self.guard(PLUGIN + "brand_new_tool", PRODUCTION))
        self.assertEqual(decision, "ask")

    def test_unset_option_uses_the_manifest_default(self) -> None:
        # Claude Code exports the option only once it is set; the server then
        # runs on the manifest default (staging), and so must the guard.
        self.assertIsNone(self.guard(PLUGIN + "page_update", None))
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, None)
        self.assertIn("STAGING", output["systemMessage"])

    def test_unknown_url_counts_as_production(self) -> None:
        decision, _ = self.decision(self.guard(PLUGIN + "page_update", "https://example.com/mcp"))
        self.assertEqual(decision, "ask")

    def test_user_level_server_uses_its_own_url(self) -> None:
        decision, reason = self.decision(self.guard(USER + "page_update", STAGING, user_url=PRODUCTION))
        self.assertEqual(decision, "ask")
        self.assertIn("mcp-corp.pai.lat", reason)
        self.assertIsNone(self.guard(USER + "page_update", PRODUCTION, user_url=STAGING))

    def test_user_level_server_without_config_counts_as_production(self) -> None:
        decision, _ = self.decision(self.guard(USER + "knowledge_update", STAGING))
        self.assertEqual(decision, "ask")

    def test_create_without_search_is_denied_everywhere(self) -> None:
        empty = self.transcript()
        for url in (STAGING, PRODUCTION):
            decision, reason = self.decision(self.guard(PLUGIN + "knowledge_create", url, transcript=empty))
            self.assertEqual(decision, "deny")
            self.assertIn("knowledge_search", reason)

    def test_search_of_other_area_does_not_count(self) -> None:
        searched = self.transcript(PLUGIN + "page_search")
        decision, _ = self.decision(self.guard(PLUGIN + "knowledge_create", STAGING, transcript=searched))
        self.assertEqual(decision, "deny")

    def test_create_after_search_passes_in_staging_and_asks_in_production(self) -> None:
        searched = self.transcript(PLUGIN + "whoami", PLUGIN + "knowledge_search")
        self.assertIsNone(self.guard(PLUGIN + "knowledge_create", STAGING, transcript=searched))
        decision, _ = self.decision(self.guard(PLUGIN + "knowledge_create", PRODUCTION, transcript=searched))
        self.assertEqual(decision, "ask")

    def test_search_on_user_server_counts(self) -> None:
        searched = self.transcript(USER + "page_list")
        self.assertIsNone(self.guard(PLUGIN + "page_create", STAGING, transcript=searched))

    def test_missing_transcript_never_blocks(self) -> None:
        self.assertIsNone(self.guard(PLUGIN + "page_create", STAGING, transcript=str(Path(self.home.name, "missing.jsonl"))))


class SessionStartTest(HookCase):
    def test_announces_staging(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, STAGING)
        self.assertIn("STAGING", output["systemMessage"])
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mcp__plugin_pai-console_pai__", context)
        self.assertNotIn("pide confirmación", context)

    def test_announces_production_and_user_server(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, PRODUCTION, user_url=PRODUCTION)
        self.assertIn("PRODUCCIÓN", output["systemMessage"])
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("pide confirmación", context)
        self.assertIn("mcp__pai-console__", context)


if __name__ == "__main__":
    unittest.main()
