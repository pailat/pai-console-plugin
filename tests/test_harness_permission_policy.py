"""ATE-1223 owner policy: bypassPermissions by default, deny rules and hooks as the safety, no doc that forbids bypass."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_support import FIXTURES, PLUGIN_ROOT, ROOT, SCRIPTS, HarnessCase, write_deny_settings  # noqa: E402

sys.path.insert(0, str(SCRIPTS))
import deny_baseline  # noqa: E402
import harness_config  # noqa: E402

FORBIDS = re.compile(r"(never|do not|don't|must not|should not|shall not|forbid\w*|prohibit\w*|refuse\w*)\s+(to\s+)?(\w+\s+){0,4}?"
                     r"(bypass(ing)?[- ]?permissions?|permissions?[- ]bypass|dangerously-skip-permissions|skip-permissions)|"
                     r"permission-bypass flag|no[- ]permission[- ]bypass|(never|do not|don't)\s+run\s+with\s+bypass", re.I)
MINIMAL = '[project]\npai_org = "acme"\npai_project = "acme-web"\nlinear_team = "ACME"\n'


class NoDocForbidsBypassTest(unittest.TestCase):
    def test_no_agent_command_skill_doc_or_generated_package_forbids_bypass(self) -> None:
        roots = [PLUGIN_ROOT / d for d in ("agents", "commands", "skills", "docs", "scripts", "examples", "hooks")]
        roots += [PLUGIN_ROOT / "CHANGELOG.md", ROOT / "plugins/codex-harness", ROOT / "README.md", ROOT / "AGENTS.md", ROOT / ".claude", ROOT / "docs"]
        offenders = []
        for base in roots:
            for path in ([base] if base.is_file() else sorted(base.rglob("*"))):
                if path.is_file() and path.suffix in {".md", ".py", ".toml", ".json", ".sh"}:
                    if FORBIDS.search(path.read_text(errors="ignore")):
                        offenders.append(str(path.relative_to(ROOT)))
        self.assertEqual(offenders, [])

    def test_every_agent_states_the_policy(self) -> None:
        agents = sorted((PLUGIN_ROOT / "agents").glob("*.md"))
        for path in agents:
            if path.name == "README.md":
                continue
            text = path.read_text()
            self.assertIn("bypassPermissions", text, path.name)
            self.assertIn("BLOCKER", text, path.name)


class LauncherPolicyTest(HarnessCase):
    def argv(self) -> list[str]:
        return json.loads((self.tmp / "claude.json").read_text())["argv"]

    def test_default_passes_bypass_permissions(self) -> None:
        self.launch("ACME-7", "success", 0)
        argv = self.argv()
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")

    def test_resume_passes_bypass_permissions_too(self) -> None:
        self.launch("ACME-7", "success", 0)
        self.run_script("launch.sh", "ACME-7", "--resume", FAKE_CLAUDE_FIXTURE=str(self.fixture("success")))
        argv = self.argv()
        self.assertIn("--resume", argv)
        self.assertEqual(argv[argv.index("--permission-mode") + 1], "bypassPermissions")

    def test_project_opt_out_drops_the_flag(self) -> None:
        config = self.tmp / "optout.toml"
        config.write_text(MINIMAL + "\n[run]\nbypass_permissions = false\n")
        self.env["PAI_HARNESS_CONFIG"] = str(config)
        self.launch("ACME-7", "success", 0)
        self.assertNotIn("--permission-mode", self.argv())
        self.assertNotIn("bypassPermissions", self.argv())


class ConfigKeyTest(unittest.TestCase):
    def test_default_true_and_opt_out(self) -> None:
        self.assertIs(harness_config.validate({"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}})["run"]["bypass_permissions"], True)
        data = {"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}, "run": {"bypass_permissions": False}}
        self.assertIs(harness_config.validate(data)["run"]["bypass_permissions"], False)

    def test_rejects_a_non_boolean_and_unknown_keys(self) -> None:
        base = {"project": {"pai_org": "a", "pai_project": "b", "linear_team": "ACME"}}
        for run in ({"bypass_permissions": "no"}, {"mode": "x"}):
            with self.assertRaises(harness_config.ConfigError):
                harness_config.validate({**base, "run": run})

    def test_schema_documents_the_key(self) -> None:
        schema = json.loads((PLUGIN_ROOT / "schema/pai-harness.schema.json").read_text())
        self.assertEqual(sorted(schema["properties"]["run"]["properties"]), sorted(harness_config.DEFAULTS["run"]))


def matches(rule: str, command: str) -> bool:
    """A model of the Bash rule grammar used here (`*` matches any characters, whole command). It is NOT the Claude Code client:
    the rows below pin what the rules are meant to do, and a real client run is the only proof (see examples/README.md)."""
    return deny_baseline.glob_match(rule[len("Bash("):-1], command)


def denied(rules: list[str], command: str) -> bool:
    return any(matches(rule, command) for rule in rules if rule.startswith("Bash("))


def mcp_denied(rules: list[str], tool: str) -> bool:
    return any(deny_baseline.covers(rule, tool) or deny_baseline.glob_match(rule, tool) for rule in rules if rule.startswith("mcp__"))


class DenyExampleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.deny = json.loads((PLUGIN_ROOT / "examples/settings.deny.json").read_text())["permissions"]["deny"]
        self.non_merge = json.loads((PLUGIN_ROOT / "examples/settings.deny.non-merge.json").read_text())["permissions"]["deny"]

    def test_parses_with_claude_code_rule_syntax(self) -> None:
        self.assertTrue(self.deny and len(set(self.deny)) == len(self.deny))
        for rule in self.deny:
            self.assertRegex(rule, r"^((Bash|Read|Edit|Write)\(.+\)|mcp__[A-Za-z0-9_-]+__[A-Za-z0-9_*-]+)$")

    def test_real_command_spellings_are_denied(self) -> None:
        for command in ("git push --force origin x", "git -C repo push --force origin x", "git -c a=b push --force-with-lease", "git push -f",
                        "git push origin feature -f", "git push origin --delete feature", "git push origin :feature", "git push origin +feature",
                        "git push --mirror", "git push origin x --no-verify", "git -C r commit -m x --no-verify", "git commit -nm x", "git commit -m x -n",
                        "git reset --hard", "git -C repo reset --hard HEAD~1", "git -c core.x=1 reset --hard", "git clean -fd", "git clean -xfd",
                        "git -C r clean -f", "git branch -D x", "git -C r branch -D x", "git checkout .", "git restore .",
                        "rm -rf /", "rm -rf ~", "rm -r -f ~", "rm -fr ~", "rm -Rf /", 'rm -rf "$HOME"', "rm -rf $HOME", "rm -rf ${HOME}", "rm -rf ./.git",
                        "rm -rf .git", "rm -rf ..", "rm -rf .", "rm -rf ./", "rm -rf sub/.git", "rm --recursive --force /", "rm -rf /etc", "rm -rf /usr",
                        "rm -rf /home", "sudo ls", "ssh host", "cat .env", "cat ./.env.local", "head -3 .env", "grep KEY .env", "source .env",
                        "cat app/.env.production", "cat ~/.ssh/id_rsa", "cat ~/.config/pai-harness/token"):
            self.assertTrue(denied(self.deny, command), command)

    def test_ordinary_work_is_not_denied(self) -> None:
        for command in ("git push origin feature-fix", "git push -u origin feature", "git push origin HEAD:feature", "git status", "git commit -m x",
                        "git clean -n", "rm -rf build", "rm file.txt", "cat README.md", "grep env README.md", "git push origin main-fix",
                        "rm -rf /tmp/x", "rm -rf /tmp/*", "rm -rf /tmp/build-1234", 'rm -rf "$(mktemp -d)"', "rm -rf dist", "rm -rf ./build",
                        "rm -rf node_modules", "rm -rf ../sibling-tmp", "rm -rf ~/scratch/x", "rm -rf /var/tmp/x", "cat .env.example", "git add .env.example",
                        "cat .env.sample", 'git commit -m "explain .env loading"', 'git commit -m "list -n option"', 'git commit -m "x -n y"'):
            self.assertFalse(denied(self.deny + self.non_merge, command), command)
        for path in ("./.env.example", "./.env.sample"):
            self.assertNotIn(f"Read({path})", self.deny)

    def test_current_mcp_write_tools_are_denied_and_reads_are_not(self) -> None:
        """Every current Pai, Linear and Railway tool named here is a write that must not run unprompted under bypass."""
        pai = ("iam_policy_set", "iam_binding_add", "iam_binding_remove", "iam_role_create", "iam_service_token_create", "product_deploy",
               "product_version_publish", "space_deploy", "space_version_publish", "organization_member_remove", "organization_member_role_set",
               "organization_archive", "organization_theme_publish", "crm_lead_purge", "crm_lead_anonymize", "crm_opportunity_win", "user_ban",
               "user_unban", "user_create", "user_export", "page_delete", "file_delete", "folder_delete", "milestone_delete", "asset_delete",
               "project_delete", "project_slug_set", "connection_revoke", "connection_terminal_terminate", "payment_void", "finance_payment_register",
               "status_update_publish", "product_domain_remove", "product_production_access_set", "workforce_access_set")
        for prefix in deny_baseline.PAI_PREFIXES:
            for tool in pai:
                self.assertTrue(mcp_denied(self.deny, prefix + tool), prefix + tool)
        for tool in ("delete_attachment", "delete_comment", "delete_customer", "delete_customer_need", "delete_diff_comment", "delete_status_update", "merge_diff"):
            self.assertTrue(mcp_denied(self.deny, deny_baseline.LINEAR_PREFIX + tool), tool)
        railway = ("accept-deploy", "create-deployment", "deploy-template", "redeploy", "restart-service", "delete-bucket", "delete-domain",
                   "delete-feature-flag", "delete-service", "delete-tcp-proxy", "delete-volume", "delete-webhook", "purge-cdn-cache",
                   "reset-bucket-credentials", "set-variables", "set-feature-flag", "update-function-source-code", "connect-service-source")
        for prefix in deny_baseline.RAILWAY_PREFIXES:
            for tool in railway:
                self.assertTrue(mcp_denied(self.deny, prefix + tool), prefix + tool)
        for tool in ("knowledge_search", "knowledge_create", "knowledge_update", "page_read", "task_create", "comment_create", "project_list", "whoami"):
            self.assertFalse(mcp_denied(self.deny, "mcp__pai__" + tool), tool)  # the harness's own work stays allowed
        for tool in ("save_issue", "save_comment", "list_issues", "get_issue"):
            self.assertFalse(mcp_denied(self.deny, deny_baseline.LINEAR_PREFIX + tool), tool)
        for tool in ("list-services", "get-logs", "whoami"):
            self.assertFalse(mcp_denied(self.deny, "mcp__railway__" + tool), tool)

    def test_every_destructive_pai_tool_with_a_denied_verb_is_denied(self) -> None:
        """Drift guard on hooks/tools.json: a tool whose name carries a denied verb can never slip through the patterns."""
        tools = json.loads((ROOT / "hooks/tools.json").read_text())["tools"]
        verbs = ("delete", "remove", "revoke", "deploy", "publish", "purge", "anonymize", "terminate", "void", "rotate", "renounce")
        for name in tools:
            if any(verb in name for verb in verbs) or name.startswith(("iam_", "finance_")):
                self.assertTrue(mcp_denied(self.deny, "mcp__pai__" + name), name)

    def test_merge_roles_are_not_denied_the_merge_and_others_are(self) -> None:
        for command in ("gh pr merge 51 --squash", "gh -R o/r pr merge 51", "git push origin main", "git push origin HEAD:main", "git push origin release/1.2"):
            self.assertFalse(denied(self.deny, command), command)  # the integrator documented flow can run
            self.assertTrue(denied(self.non_merge, command), command)  # every other role's worktree adds this file
        self.assertFalse(denied(self.non_merge, "git push origin main-fix"))

    def test_baseline_is_part_of_the_example_and_the_files_are_generated(self) -> None:
        for role in ("implementer", "integrator"):
            for strict in (True, False):
                wanted = deny_baseline.baseline(strict, role)
                self.assertEqual([r for r in wanted if r not in self.deny and r not in self.non_merge], [])
        self.assertEqual(self.non_merge, list(deny_baseline.NON_MERGE_RULES))
        done = subprocess.run([sys.executable, str(ROOT / "tools/build_harness_deny.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)

    def test_the_settings_model_accepts_equivalent_wildcards(self) -> None:
        self.assertTrue(deny_baseline.covers("mcp__pai__*", "mcp__pai__iam_*"))
        self.assertTrue(deny_baseline.covers("mcp__pai", "mcp__pai__*delete*"))
        self.assertTrue(deny_baseline.covers("mcp__pai__iam_*", "mcp__pai__iam_*"))
        self.assertTrue(deny_baseline.covers("Bash(git *)", "Bash(git *reset --hard*)"))
        self.assertFalse(deny_baseline.covers("mcp__pai__iam_*", "mcp__pai__*delete*"))
        self.assertFalse(deny_baseline.covers("Read(./.env)", "Bash(sudo *)"))

    def test_is_generic(self) -> None:
        for name in ("settings.deny.json", "settings.deny.non-merge.json"):
            self.assertNotRegex((PLUGIN_ROOT / "examples" / name).read_text(), r"/home/|/Users/|pailat")


class PreflightTest(HarnessCase):
    def blocked(self, done: subprocess.CompletedProcess) -> None:
        self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
        self.assertIn("BLOCKER ACME-7:", done.stdout)
        self.assertIn("deny baseline", done.stdout)
        self.assertFalse((self.tmp / "claude.json").exists(), "no claude process may start")
        self.assertEqual(json.loads((self.state / "registry/ACME-7.json").read_text())["state"], "blocked")

    def test_missing_settings_end_the_run_blocked_with_a_named_reason(self) -> None:
        (self.claude_home / "settings.json").unlink()
        done = self.launch("ACME-7", "success", 0)
        self.blocked(done)
        self.assertIn("rules are missing", done.stdout)

    def test_one_missing_rule_blocks_and_is_named(self) -> None:
        rules = [r for r in deny_baseline.baseline(False, "implementer") if r != "mcp__pai__iam_*"]
        write_deny_settings(self.claude_home / "settings.json", rules)
        done = self.launch("ACME-7", "success", 0)
        self.blocked(done)
        self.assertIn("mcp__pai__iam_*", done.stdout)

    def test_an_equivalent_wildcard_satisfies_the_baseline(self) -> None:
        rules = [r for r in deny_baseline.baseline(False, "implementer") if not r.startswith("mcp__")] + ["mcp__pai", "mcp__plugin_pai-console_pai",
                 "mcp__plugin_linear_linear", "mcp__railway", "mcp__plugin_railway_railway"]
        write_deny_settings(self.claude_home / "settings.json", rules)
        self.assertEqual(self.launch("ACME-7", "success", 0).returncode, 0)

    def test_a_role_that_does_not_merge_needs_the_merge_denials_and_the_integrator_does_not(self) -> None:
        rules = [r for r in deny_baseline.baseline(False, "implementer") if r not in deny_baseline.NON_MERGE_RULES]
        write_deny_settings(self.claude_home / "settings.json", rules)
        self.assertIn("gh *pr merge", self.launch("ACME-7", "success", 0).stdout)
        (self.tmp / "claude.json").unlink(missing_ok=True)
        self.assertEqual(self.launch("ACME-9", "success", 0, "--role", "integrator").returncode, 0)

    def test_strict_mcp_needs_only_the_machine_server_and_open_mcp_needs_every_known_server(self) -> None:
        strict = set(deny_baseline.baseline(True, "implementer"))
        self.assertTrue(any(r.startswith("mcp__pai__") for r in strict))
        self.assertFalse(any(r.startswith(("mcp__railway", "mcp__plugin_")) for r in strict))
        open_ = set(deny_baseline.baseline(False, "implementer"))
        self.assertTrue(any(r.startswith("mcp__railway__") for r in open_))
        self.assertTrue(any(r.startswith("mcp__plugin_linear_linear__") for r in open_))
        self.assertTrue(any(r.startswith("mcp__plugin_pai-console_pai__") for r in open_))

    def test_a_preflight_block_replaces_the_recorded_state_and_keeps_the_session(self) -> None:
        self.launch("ACME-7", "success", 0)
        session = self.record("ACME-7")["session_id"]
        (self.claude_home / "settings.json").unlink()
        (self.tmp / "claude.json").unlink()
        self.blocked(self.launch("ACME-7", "success", 0))
        record = self.record("ACME-7")
        self.assertEqual((record["state"], record["session_id"]), ("blocked", session))
        self.assertIn("deny baseline", record["reason"])
        status = self.run_script("launch.sh", "--status", "ACME-7")
        self.assertEqual(status.returncode, 3, status.stdout + status.stderr)
        blockers = [e for e in self.journal() if e.get("kind") == "BLOCKER"]
        self.assertEqual(len(blockers), 1)

    def test_project_settings_of_a_parent_git_root_are_not_counted_for_a_subdirectory(self) -> None:
        (self.claude_home / "settings.json").unlink()
        work = self.tmp / "work"
        subprocess.run(["git", "init", "-q", str(work)], check=True)
        write_deny_settings(work / ".claude/settings.json", deny_baseline.baseline(False, "implementer"))
        (work / "sub").mkdir()
        self.blocked(self.launch("ACME-7", "success", 0, "--cwd", str(work / "sub")))

    def test_resume_is_checked_too(self) -> None:
        self.launch("ACME-7", "success", 0)
        (self.tmp / "claude.json").unlink()
        (self.claude_home / "settings.json").unlink()
        done = self.run_script("launch.sh", "ACME-7", "--resume", FAKE_CLAUDE_FIXTURE=str(self.fixture("success")))
        self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
        self.assertFalse((self.tmp / "claude.json").exists())

    def test_the_baseline_can_come_from_project_settings(self) -> None:
        (self.claude_home / "settings.json").unlink()
        work = self.tmp / "work"
        subprocess.run(["git", "init", "-q", str(work)], check=True)
        write_deny_settings(work / ".claude/settings.json", deny_baseline.baseline(False, "implementer"))
        done = self.launch("ACME-7", "success", 0, "--cwd", str(work))
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_waiver_and_opt_out_skip_the_check(self) -> None:
        (self.claude_home / "settings.json").unlink()
        for body in ("[run]\nrequire_deny_baseline = false\n", "[run]\nbypass_permissions = false\n"):
            config = self.tmp / "waive.toml"
            config.write_text(MINIMAL + "\n" + body)
            self.env["PAI_HARNESS_CONFIG"] = str(config)
            done = self.launch("ACME-7", "success", 0)
            self.assertEqual(done.returncode, 0, done.stdout + done.stderr)

    def test_dry_run_reports_the_missing_count_and_does_not_block(self) -> None:
        (self.claude_home / "settings.json").unlink()
        done = self.run_script("launch.sh", "ACME-7", "--prompt", "x", "--dry-run")
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertEqual(json.loads(done.stdout)["deny_baseline_missing"], len(deny_baseline.baseline(False, "implementer")))

    def test_malformed_settings_count_as_absent(self) -> None:
        (self.claude_home / "settings.json").write_text("{not json")
        self.blocked(self.launch("ACME-7", "success", 0))


class WordingTest(unittest.TestCase):
    def test_no_text_claims_prompts_exist_in_headless_runs(self) -> None:
        for path in [PLUGIN_ROOT / "schema/pai-harness.schema.json", SCRIPTS / "launch.py", PLUGIN_ROOT / "examples/README.md"]:
            self.assertNotIn("relies on prompts", path.read_text(), path.name)
            self.assertNotIn("safety then relies on prompts", path.read_text(), path.name)

    def test_a_denial_reads_as_policy_not_as_a_grant_to_ask_for(self) -> None:
        import harness_lib as lib
        summary = {"result": {"subtype": "success", "is_error": False, "permission_denials": [{"tool_name": "Bash"}]}}
        reason = lib.run_state(summary, 0)["reason"]
        self.assertIn("denied by policy", reason)
        self.assertIn("report BLOCKER", reason)
        self.assertNotIn("grant", reason)


class CodexPackageTest(unittest.TestCase):
    def test_the_codex_package_does_not_inherit_the_claude_only_policy_files(self) -> None:
        package = ROOT / "plugins/codex-harness/examples"
        self.assertEqual(sorted(p.name for p in package.glob("settings.deny*")), [])
        text = (package / "README.md").read_text()
        self.assertIn("Claude Code only", text)
        self.assertIn("native MCP approval policies", text)
        self.assertNotIn("Two layers", text)


if __name__ == "__main__":
    unittest.main()
