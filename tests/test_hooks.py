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
DEVELOP = "https://mcp-corp.paitesting.com/mcp"
DEVELOP_LEGACY = "https://mcp-edge-corp-develop.up.railway.app/mcp"
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
            json.dumps({"type": "user", "message": {"role": "user", "content": "hello"}}),
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

    def test_develop_writes_pass_without_confirmation(self) -> None:
        for url in (DEVELOP, DEVELOP_LEGACY):
            self.assertIsNone(self.guard(PLUGIN + "page_update", url), url)
            self.assertIsNone(self.guard(PLUGIN + "project_delete", url), url)

    def test_production_reads_pass(self) -> None:
        for tool in ("whoami", "page_read", "knowledge_search", "timeline_get", "page_validate"):
            self.assertIsNone(self.guard(PLUGIN + tool, PRODUCTION), tool)

    def test_production_write_asks(self) -> None:
        decision, reason = self.decision(self.guard(PLUGIN + "page_update", PRODUCTION, {"path": "architecture/payments"}))
        self.assertEqual(decision, "ask")
        self.assertIn("PRODUCTION", reason)
        self.assertIn("architecture/payments", reason)

    def test_production_irreversible_says_so_and_what_it_drags(self) -> None:
        decision, reason = self.decision(self.guard(PLUGIN + "project_delete", PRODUCTION, {"projectId": "p1"}))
        self.assertEqual(decision, "ask")
        self.assertTrue(reason.startswith("IRREVERSIBLE"))
        self.assertIn("payments and CFDI", reason)
        for tool in ("page_delete", "payment_void", "milestone_delete", "folder_delete", "asset_delete"):
            decision, reason = self.decision(self.guard(PLUGIN + tool, PRODUCTION))
            self.assertEqual(decision, "ask")
            self.assertTrue(reason.startswith("IRREVERSIBLE"), tool)

    def test_product_deploy_depends_on_target_environment(self) -> None:
        _, reason = self.decision(self.guard(PLUGIN + "product_deploy", PRODUCTION, {"environment": "production"}))
        self.assertTrue(reason.startswith("IRREVERSIBLE"))
        _, reason = self.decision(self.guard(PLUGIN + "product_deploy", PRODUCTION, {"environment": "staging"}))
        self.assertTrue(reason.startswith("ATTENTION"))

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

    def test_crm_lead_create_needs_duplicates_check(self) -> None:
        decision, _ = self.decision(self.guard(PLUGIN + "crm_lead_create", STAGING, transcript=self.transcript()))
        self.assertEqual(decision, "deny")
        searched = self.transcript(PLUGIN + "crm_lead_duplicates")
        self.assertIsNone(self.guard(PLUGIN + "crm_lead_create", STAGING, transcript=searched))

    def test_flow_create_needs_a_flows_search(self) -> None:
        decision, _ = self.decision(self.guard(PLUGIN + "flow_create", STAGING, transcript=self.transcript()))
        self.assertEqual(decision, "deny")
        searched = self.transcript(PLUGIN + "flow_list")
        self.assertIsNone(self.guard(PLUGIN + "flow_create", STAGING, transcript=searched))

    def test_note_create_needs_a_pages_search(self) -> None:
        decision, _ = self.decision(self.guard(PLUGIN + "note_create", STAGING, transcript=self.transcript()))
        self.assertEqual(decision, "deny")
        searched = self.transcript(PLUGIN + "page_list")
        self.assertIsNone(self.guard(PLUGIN + "note_create", STAGING, transcript=searched))

    def test_search_on_user_server_counts(self) -> None:
        searched = self.transcript(USER + "page_list")
        self.assertIsNone(self.guard(PLUGIN + "page_create", STAGING, transcript=searched))

    def test_missing_transcript_never_blocks(self) -> None:
        self.assertIsNone(self.guard(PLUGIN + "page_create", STAGING, transcript=str(Path(self.home.name, "missing.jsonl"))))

    def test_hostname_spoofs_are_production(self) -> None:
        for url in (
            STAGING.replace(".app/mcp", ".app.evil.test/mcp"),
            "https://evil.test/" + STAGING,
            "https://mcp-corp.paitesting.com@evil.test/mcp",
            "https://[broken/mcp",
        ):
            decision, _ = self.decision(self.guard(PLUGIN + "page_update", url))
            self.assertEqual(decision, "ask")
            output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, url)
            self.assertIn("PRODUCTION", output["systemMessage"])

    def test_malformed_events_do_not_crash(self) -> None:
        for event in (None, [], True, "text", {"tool_name": []}):
            self.assertIsNone(self.run_hook(GUARD, event, PRODUCTION))
        decision, _ = self.decision(self.run_hook(GUARD, {"tool_name": PLUGIN + "page_update", "tool_input": []}, PRODUCTION))
        self.assertEqual(decision, "ask")

    def test_malformed_transcript_entries_are_ignored(self) -> None:
        path = Path(self.home.name, "malformed.jsonl")
        path.write_text('[]\n{"message": []}\n{"message": {"content": "tool_use"}}\n')
        decision, _ = self.decision(self.guard(PLUGIN + "page_create", STAGING, transcript=str(path)))
        self.assertEqual(decision, "deny")


class InventoryTest(HookCase):
    """hooks/tools.json is the corp server's tools/list (pai-portal 0.2.5+)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.tools = json.loads((ROOT / "hooks" / "tools.json").read_text())["tools"]
        source = (ROOT / "hooks" / "policy.py").read_text()
        cls.guard_names = set(
            name
            for block in ("IRREVERSIBLE = {", "ATTENTION = {", "SEARCH_BEFORE_CREATE = {")
            for name in __import__("re").findall(r'^    "([a-z_]+)":', source.split(block, 1)[1].split("\n}", 1)[0], __import__("re").M)
        )

    def test_inventory_has_the_025_tools(self) -> None:
        for tool in ("task_board", "knowledge_view", "knowledge_library", "knowledge_graph", "page_create"):
            self.assertIn(tool, self.tools)

    def test_every_read_passes_and_every_write_asks_in_production(self) -> None:
        for name, hints in self.tools.items():
            output = self.guard(PLUGIN + name, PRODUCTION, transcript=self.transcript(PLUGIN + "page_search", PLUGIN + "knowledge_search", PLUGIN + "timeline_get", PLUGIN + "project_list", PLUGIN + "organization_list", PLUGIN + "product_list", PLUGIN + "agent_list", PLUGIN + "crm_lead_duplicates", PLUGIN + "crm_organization_get"))
            if hints["readOnly"]:
                self.assertIsNone(output, name)
            else:
                self.assertEqual(self.decision(output)[0], "ask", name)

    def test_guard_names_exist_on_the_server(self) -> None:
        self.assertEqual(sorted(n for n in self.guard_names if n not in self.tools), [])

    def test_irreversible_tools_are_writes(self) -> None:
        self.assertEqual(sorted(n for n in self.guard_names if self.tools.get(n, {}).get("readOnly")), [])

    def test_skill_inventory_names_every_tool(self) -> None:
        inventory = (ROOT / "skills" / "pai-console" / "references" / "tools.md").read_text()
        self.assertEqual(sorted(n for n in self.tools if f"`{n}`" not in inventory), [])

    def test_explorer_agent_only_reads(self) -> None:
        header = (ROOT / "agents" / "pai-explorer.md").read_text().split("\n---", 1)[0]
        names = __import__("re").findall(r"mcp__plugin_pai-console_pai__(\w+)", header)
        self.assertIn("crm_task_list", names)
        self.assertEqual(sorted(n for n in names if not self.tools.get(n, {}).get("readOnly")), [])

    def test_flow_tools_are_known(self) -> None:
        for tool in ("flow_list", "flow_get", "flow_run_list", "flow_run_get"):
            self.assertTrue(self.tools[tool]["readOnly"], tool)
        for tool in ("flow_create", "flow_save", "flow_version_bump", "flow_run_start", "flow_run_step", "flow_run_finish"):
            self.assertFalse(self.tools[tool]["readOnly"], tool)
            self.assertFalse(self.tools[tool]["destructive"], tool)

    def test_asset_tools_are_known(self) -> None:
        for tool in ("asset_list", "asset_get"):
            self.assertTrue(self.tools[tool]["readOnly"], tool)
        for tool in ("asset_upload", "asset_confirm"):
            self.assertFalse(self.tools[tool]["readOnly"], tool)
            self.assertFalse(self.tools[tool]["destructive"], tool)
        self.assertTrue(self.tools["asset_delete"]["destructive"])

    def test_crm_task_tools_are_known(self) -> None:
        for tool in ("crm_task_list", "crm_task_get", "crm_task_tag_list"):
            self.assertTrue(self.tools[tool]["readOnly"], tool)
        for tool in ("crm_task_create", "crm_task_update", "crm_task_complete"):
            self.assertFalse(self.tools[tool]["readOnly"], tool)
            self.assertFalse(self.tools[tool]["destructive"], tool)


class SessionStartTest(HookCase):
    def test_announces_staging(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, STAGING)
        self.assertIn("STAGING", output["systemMessage"])
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("mcp__plugin_pai-console_pai__", context)
        self.assertNotIn("requests confirmation", context)

    def test_announces_develop(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, DEVELOP)
        self.assertIn("DEVELOP", output["systemMessage"])
        self.assertNotIn("confirmation", output["hookSpecificOutput"]["additionalContext"])
        self.assertIn(DEVELOP, output["systemMessage"])

    def test_announces_legacy_develop_url_as_develop(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, DEVELOP_LEGACY)
        self.assertIn("DEVELOP", output["systemMessage"])
        self.assertNotIn("PRODUCTION", output["systemMessage"])

    def test_announces_production_and_user_server(self) -> None:
        output = self.run_hook(SESSION_START, {"hook_event_name": "SessionStart"}, PRODUCTION, user_url=PRODUCTION)
        self.assertIn("PRODUCTION", output["systemMessage"])
        context = output["hookSpecificOutput"]["additionalContext"]
        self.assertIn("requests confirmation", context)
        self.assertIn("mcp__pai-console__", context)


if __name__ == "__main__":
    unittest.main()
