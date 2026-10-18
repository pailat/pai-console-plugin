"""Codex adapter contract tests; all MCP results and endpoints are fixtures."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"
sys.path.insert(0, str(HOOKS))
import policy

spec = importlib.util.spec_from_file_location("pai_codex_hooks", HOOKS / "codex.py")
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)

STAGING = "https://mcp-edge-corp-staging.up.railway.app/mcp"
PRODUCTION = "https://mcp-corp.pai.lat/mcp"
DEVELOP = "https://mcp-corp.paitesting.com/mcp"


def response(data=None):
    return {"isError": False, "content": [{"type": "text", "text": json.dumps({"success": True, "data": {} if data is None else data})}]}


class CodexHookTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.config = {"environment": "staging", "url": STAGING, "plugin_name": "pai-console-staging", "server_name": "pai_console_staging"}
        self.configure()
        self.env = patch.dict(os.environ, {"PLUGIN_ROOT": str(self.root), "PLUGIN_DATA": str(self.root / "data")})
        self.env.start()
        self.addCleanup(self.env.stop)

    def configure(self, **changes):
        self.config.update(changes)
        if "environment" in changes and "server_name" not in changes:
            self.config["server_name"] = "pai_console_" + runtime.ENVIRONMENTS[changes["environment"]]
        if "environment" in changes and "plugin_name" not in changes:
            self.config["plugin_name"] = "pai-console-" + runtime.ENVIRONMENTS[changes["environment"]]
        (self.root / "environment.json").write_text(json.dumps(self.config))

    def event(self, kind="PreToolUse", tool="page_update", session="s1", prefix=None, **fields):
        if prefix is None:
            prefix = f"mcp__{self.config['server_name']}__"
        return {"hook_event_name": kind, "session_id": session, "tool_name": prefix + tool, "tool_input": {}, **fields}

    def pre(self, tool="page_update", **fields):
        return runtime.handle(self.event(tool=tool, **fields))

    def post(self, tool="page_search", data=None, **fields):
        return runtime.handle(self.event("PostToolUse", tool, tool_response=response(data), **fields))

    def identify(self, environment="staging", **fields):
        return self.post("whoami", {"environment": environment}, **fields)

    def denied(self, result, text=None):
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        if text:
            self.assertIn(text, result["hookSpecificOutput"]["permissionDecisionReason"])

    def passed(self, result):
        if result is not None:
            self.assertNotIn("permissionDecision", result["hookSpecificOutput"])
            self.assertNotIn('"ask"', json.dumps(result))

    def states(self):
        return list((self.root / "data/pai-hook-state").glob("*.json"))

    def test_session_start_fixed_endpoint_and_native_approval_context(self):
        result = runtime.handle(self.event("SessionStart"))
        self.assertIn(STAGING, result["systemMessage"])
        self.assertIn("fixed endpoint", json.dumps(result))
        self.assertIn("Native MCP approval", json.dumps(result))
        self.assertFalse((self.root / "data").exists())

    def test_exact_known_server_names(self):
        prefixes = runtime.known_prefixes(runtime.package())
        self.assertEqual(prefixes, ("mcp__pai_console_staging__",))
        for prefix in prefixes:
            with self.subTest(prefix=prefix):
                self.assertEqual(runtime.resolve(prefix + "page_search", runtime.package()), (prefix, "page_search"))
                self.identify(prefix=prefix)
                self.post(prefix=prefix)
                self.passed(self.pre("page_create", prefix=prefix))
        for name in ("mcp__other__page_search", "mcp__plugin_other_pai__page_search", "mcp__pai-evil__page_search", "mcp__pai__page_search__suffix", "mcp__plugin_pai-console-production_pai__page_search", "mcp__plugin_pai-console-staging__pai__page_search"):
            self.assertIsNone(runtime.resolve(name, runtime.package()), name)

    def test_unrecognized_pai_names_are_denied(self):
        for prefix in ("mcp__pai__", "mcp__pai-console__", "mcp__pai-evil__", "mcp__pai_console_production__", "mcp__pai_console_develop__", "mcp__pai_console_staging_evil__", "mcp__plugin_pai-console-production_pai__", "mcp__plugin-pai-console-staging_pai__", "mcp__plugin__pai-console-staging__pai__", "mcp__PAI_console_staging__"):
            self.denied(self.pre(prefix=prefix), "namespace")

    def test_unique_server_name_matches_canonical_environment_exactly(self):
        for environment, url in (("staging", STAGING), ("develop", DEVELOP), ("development", DEVELOP), ("production", PRODUCTION)):
            canonical = runtime.ENVIRONMENTS[environment]
            expected = f"pai_console_{canonical}"
            self.configure(environment=environment, url=url)
            self.assertEqual(runtime.package()["server_name"], expected)
            self.assertEqual(runtime.known_prefixes(runtime.package()), (f"mcp__{expected}__",))
            for invalid in ("pai", "pai-console", "pai_console_development", expected + "_evil", *[f"pai_console_{other}" for other in ("staging", "develop", "production") if other != canonical]):
                self.configure(server_name=invalid)
                with self.assertRaises(runtime.PolicyError):
                    runtime.package()
            self.configure(server_name=expected)

    def test_plugin_name_matches_canonical_environment_exactly(self):
        for environment, url in (("staging", STAGING), ("develop", DEVELOP), ("development", DEVELOP), ("production", PRODUCTION)):
            canonical = runtime.ENVIRONMENTS[environment]
            self.configure(environment=environment, url=url)
            expected = f"pai-console-{canonical}"
            self.assertEqual(runtime.package()["plugin_name"], expected)
            for invalid in ("pai-console", "pai-console-development", expected + "-evil", *[f"pai-console-{other}" for other in ("staging", "develop", "production") if other != canonical]):
                with self.subTest(environment=environment, plugin_name=invalid):
                    self.configure(plugin_name=invalid)
                    with self.assertRaises(runtime.PolicyError):
                        runtime.package()
                    self.denied(self.pre("task_update"), "environment.json")
            self.configure(plugin_name=expected)

    def test_wrong_server_search_cannot_authorize_create(self):
        self.identify()
        for prefix in ("mcp__pai__", "mcp__pai-console__", "mcp__pai_console_production__", "mcp__plugin_pai-console-staging_pai__"):
            self.assertEqual(self.post(prefix=prefix)["decision"], "block")
            self.denied(self.pre("page_create"), "Search before creating")
        self.post()
        self.passed(self.pre("page_create"))

    def test_native_and_other_mcp_tools_pass_without_parsing_code(self):
        (self.root / "environment.json").unlink()
        for name in ("Bash", "apply_patch", "exec_command", "write_stdin", "exec", "functions.exec", "update_plan", "mcp__other__page_delete"):
            for kind in ("PreToolUse", "PostToolUse"):
                self.assertIsNone(runtime.handle(self.event(kind, name, prefix="", tool_input={"code": 'await tools.mcp__pai__page_delete({})'})), name)

    def test_all_inventory_read_write_policies_every_environment(self):
        inventory = json.loads((HOOKS / "tools.json").read_text())["tools"]
        for env, url in (("staging", STAGING), ("production", PRODUCTION), ("development", DEVELOP)):
            self.configure(environment=env, url=url)
            self.identify(env)
            for search in runtime.SEARCHES:
                self.post(search)
            for tool, hints in inventory.items():
                with self.subTest(environment=env, tool=tool):
                    result = self.pre(tool)
                    if hints["readOnly"]:
                        self.assertIsNone(result)
                    else:
                        self.passed(result)
                        context = result["hookSpecificOutput"]["additionalContext"]
                        self.assertIn(runtime.ENVIRONMENTS[env].upper(), context)
                        if env == "production":
                            self.assertIn("does not grant approval", context)

    def test_each_create_requires_matching_successful_search(self):
        self.identify()
        for create, searches in policy.SEARCH_BEFORE_CREATE.items():
            with self.subTest(create=create):
                session = create
                self.identify(session=session)
                self.denied(self.pre(create, session=session), "Search before creating")
                self.post("whoami", {"environment": "staging"}, session=session)
                self.denied(self.pre(create, session=session), searches[0])
                self.post(searches[0], session=session)
                self.passed(self.pre(create, session=session))

    def test_search_invocation_alone_does_not_count(self):
        self.identify()
        self.assertIsNone(self.pre("page_search"))
        self.denied(self.pre("page_create"), "Search before creating")

    def test_failed_and_malformed_results_never_authorize_create(self):
        self.identify()
        failures = [None, False, True, [], "success", {}, {"success": False}, {"success": 1}, {"isError": True, "success": True}, {"isError": "false", "success": True}, {"success": True, "error": "FORBIDDEN"}, {"content": []}, {"content": "ok"}, {"content": [{"type": "text", "text": "not JSON"}]}, {"isError": False, "structuredContent": {"success": False}}, {"isError": False, "content": [{"type": "text", "text": '{"success": false}'}]}, {"success": True, "data": {"success": False}}, {"success": True, "structuredContent": {"success": True}, "content": [{"type": "text", "text": '{"isError": true}'}]}]
        for result in failures:
            with self.subTest(result=result):
                runtime.handle(self.event("PostToolUse", "page_search", tool_response=result))
                self.denied(self.pre("page_create"), "Search before creating")

    def test_failed_refresh_revokes_earlier_search(self):
        self.identify()
        self.post()
        self.passed(self.pre("page_create"))
        runtime.handle(self.event("PostToolUse", "page_search", tool_response={"isError": True}))
        self.denied(self.pre("page_create"), "Search before creating")

    def test_structured_and_text_success_carriers(self):
        self.identify()
        for result in (response([]), {"isError": False, "structuredContent": {"success": True, "data": []}}, {"content": [{"type": "text", "text": '{"results": []}'}]}):
            runtime.handle(self.event("PostToolUse", "page_search", tool_response=result))
            self.passed(self.pre("page_create"))

    def test_sessions_and_servers_are_isolated(self):
        self.identify()
        self.post()
        self.identify(session="other")
        self.denied(self.pre("page_create", session="other"), "Search before creating")
        for prefix in ("mcp__pai__", "mcp__pai-console__", "mcp__pai_console_production__"):
            self.assertEqual(self.post(prefix=prefix)["decision"], "block")
            self.denied(self.pre("page_create", prefix=prefix), "namespace")
        self.passed(self.pre("page_create"))

    def test_environment_server_and_full_endpoint_changes_isolate_state(self):
        self.identify()
        self.post()
        self.configure(environment="production", url=PRODUCTION)
        self.assertEqual(self.config["server_name"], "pai_console_production")
        self.denied(self.pre("page_create"), "whoami")
        self.identify("production")
        self.denied(self.pre("page_create"), "Search before creating")
        self.configure(environment="staging", url=STAGING)
        self.passed(self.pre("page_create"))
        # The full validated URL remains part of the state key even when both
        # spellings refer to the same host and canonical environment.
        self.configure(url=STAGING.removesuffix("/mcp") + ":443/mcp")
        self.denied(self.pre("page_create"), "whoami")
        self.identify()
        self.denied(self.pre("page_create"), "Search before creating")
        self.configure(url=STAGING)
        self.passed(self.pre("page_create"))

    def test_whoami_mismatch_blocks_all_writes_and_persists(self):
        self.assertEqual(self.config["server_name"], "pai_console_staging")
        self.post()
        self.post("crm_lead_duplicates")
        result = self.identify("production")
        self.assertEqual(result["decision"], "block")
        self.assertEqual(json.loads(self.states()[0].read_text())["identity"], "production")
        for tool in ("page_update", "page_create", "task_update", "crm_lead_create"):
            self.denied(self.pre(tool), "environment")
        self.assertIsNone(self.pre("whoami"))
        self.identify()
        self.passed(self.pre())

    def test_missing_unknown_failed_identity_blocks_non_crm_writes(self):
        self.denied(self.pre(), "whoami")
        for data in ({}, {"environment": "unknown"}, {"environment": []}, {"environment": "production"}):
            self.post("whoami", data)
            self.denied(self.pre(), "environment")
        runtime.handle(self.event("PostToolUse", "whoami", tool_response={"isError": True}))
        self.denied(self.pre(), "environment")

    def test_restricted_access_uses_fixed_endpoint_without_whoami(self):
        self.passed(self.pre("task_update"))
        self.passed(self.pre("iam_policy_set"))
        self.denied(self.pre("crm_lead_create"), "Search before creating")
        self.post("crm_lead_duplicates")
        self.passed(self.pre("crm_lead_create"))

    def test_unknown_tools_are_denied_in_all_environments(self):
        for environment, url in (("staging", STAGING), ("production", PRODUCTION), ("develop", DEVELOP)):
            self.configure(environment=environment, url=url)
            self.denied(self.pre("unknown_tool"), "Unknown Pai tool")
            self.assertIsNone(self.post("unknown_tool"))

    def test_missing_corrupt_and_unavailable_state_fail_conservative(self):
        self.denied(self.pre("page_create"))
        self.identify()
        self.post()
        state = self.states()[0]
        for corrupt in ("{", "[]", '{"version":1}', '{"version":1,"searches":["page_search"],"identity":"staging","ended":0}'):
            state.write_text(corrupt)
            self.denied(self.pre("page_create"), "Corrupt")
        state.unlink()
        self.denied(self.pre("page_create"), "whoami")
        (self.root / "file").write_text("not a directory")
        with patch.dict(os.environ, {"PLUGIN_DATA": str(self.root / "file")}):
            self.denied(self.pre("task_update"), "unavailable")

    def test_missing_data_and_session_are_not_shared(self):
        for value in ("", "relative"):
            with patch.dict(os.environ, {"PLUGIN_DATA": value}):
                self.denied(self.pre("task_update"), "PLUGIN_DATA")
                self.assertIsNone(self.pre("page_search"))
        for session in (None, "", [], {}):
            self.denied(self.pre("task_update", session=session), "session_id")

    def test_transcript_is_never_read(self):
        self.identify()
        transcript = self.root / "transcript.jsonl"
        transcript.write_text(json.dumps({"tool_name": "mcp__pai_console_staging__page_search", "success": True}))
        self.denied(self.pre("page_create", transcript_path=str(transcript)), "Search before creating")

    def test_session_end_tombstone_blocks_late_results(self):
        self.identify()
        self.post()
        runtime.handle(self.event("SessionEnd"))
        self.denied(self.pre("page_create"), "ended")
        self.assertEqual(self.post()["decision"], "block")
        self.assertTrue(all(json.loads(path.read_text())["ended"] for path in self.states()))
        runtime.handle(self.event("SessionStart", source="resume"))
        self.denied(self.pre("page_create"), "ended")
        self.identify(session="new")
        self.denied(self.pre("page_create", session="new"), "Search before creating")

    def test_resume_preserves_searches_and_identity(self):
        self.identify()
        self.post()
        runtime.handle(self.event("SessionStart", source="resume"))
        self.passed(self.pre("page_create"))

    def test_url_host_matching_rejects_spoofs_and_mismatches(self):
        urls = [STAGING.replace(".app/mcp", ".app.evil.test/mcp"), "https://evil.test/" + STAGING, "https://mcp-edge-corp-staging.up.railway.app@evil.test/mcp", "http://mcp-edge-corp-staging.up.railway.app/mcp", STAGING + "?url=" + PRODUCTION, STAGING.replace("/mcp", ":9443/mcp"), PRODUCTION, "https://[broken/mcp"]
        for url in urls:
            self.configure(url=url)
            self.denied(self.pre("task_update"), "environment.json")

    def test_bad_packaged_configuration_never_falls_back_to_claude(self):
        for config in (None, [], {}, {**self.config, "environment": []}, {**self.config, "server_name": "other"}, {**self.config, "plugin_name": "other"}):
            (self.root / "environment.json").write_text(json.dumps(config))
            with patch.dict(os.environ, {"CLAUDE_PLUGIN_OPTION_MCP_URL": STAGING}):
                self.denied(self.pre("task_update"), "environment.json")
        (self.root / "environment.json").unlink()
        self.denied(self.pre("page_search"), "environment.json")

    def test_irreversible_attention_and_deploy_target(self):
        self.identify()
        for tool, consequence in {**policy.IRREVERSIBLE, **policy.ATTENTION}.items():
            if tool in policy.SEARCH_BEFORE_CREATE:
                self.post(policy.SEARCH_BEFORE_CREATE[tool][0])
            result = self.pre(tool)
            self.passed(result)
            self.assertIn(consequence, json.dumps(result))
        for environment, expected in (("production", "IRREVERSIBLE"), ("staging", "ATTENTION")):
            result = self.pre("product_deploy", tool_input={"environment": environment})
            self.assertIn(expected, result["hookSpecificOutput"]["additionalContext"])

    def test_malformed_tool_inputs_and_event_shapes(self):
        for value in (None, "", [], True):
            self.denied(self.pre(tool_input=value), "tool_input")
        self.denied(runtime.handle(self.event(tool_name=[])), "tool_name")
        self.denied(runtime.handle({}), "Malformed")

    def test_concurrent_processes_preserve_all_successful_searches(self):
        searches = sorted(runtime.SEARCHES)
        env = dict(os.environ)
        def call(tool):
            result = subprocess.run([sys.executable, str(HOOKS / "codex.py")], input=json.dumps(self.event("PostToolUse", tool, tool_response=response())), env=env, text=True, capture_output=True, check=True)
            self.assertEqual(result.stdout, "", result.stderr)
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(call, searches * 2))
        state = json.loads(self.states()[0].read_text())
        self.assertEqual(state["searches"], searches)
        self.assertFalse(list(self.states()[0].parent.glob(".*.tmp")))

    def test_cli_malformed_json_never_crashes_or_emits_ask(self):
        for value in ("{", "null", "[]", '"text"', "true"):
            result = subprocess.run([sys.executable, str(HOOKS / "codex.py")], input=value, text=True, capture_output=True, check=True)
            self.assertEqual(result.stderr, "")
            self.denied(json.loads(result.stdout), "Malformed")

    def test_codex_manifest_and_claude_manifest_remain_separate(self):
        manifest = json.loads((HOOKS / "codex_hooks.json").read_text())["hooks"]
        self.assertEqual(set(manifest), {"SessionStart", "PreToolUse", "PostToolUse", "SessionEnd"})
        for groups in manifest.values():
            self.assertNotIn("matcher", groups[0])  # Native nested tools reach the adapter too.
            handler = groups[0]["hooks"][0]
            self.assertEqual(handler["command"], 'python3 "${PLUGIN_ROOT}/hooks/codex.py"')
        claude = (HOOKS / "hooks.json").read_text()
        self.assertIn("CLAUDE_PLUGIN_ROOT", claude)
        self.assertNotIn("codex.py", claude)


if __name__ == "__main__":
    unittest.main()
