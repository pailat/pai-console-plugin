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
    """Claude Code Bash rule semantics used here: `*` matches any characters (spaces included) and the rule covers the whole command."""
    body = rule[len("Bash("):-1]
    return re.fullmatch(".*".join(re.escape(part) for part in body.split("*")), command, re.S) is not None


def denied(rules: list[str], command: str) -> bool:
    return any(matches(rule, command) for rule in rules if rule.startswith("Bash("))


class DenyExampleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.deny = json.loads((PLUGIN_ROOT / "examples/settings.deny.json").read_text())["permissions"]["deny"]
        self.non_merge = json.loads((PLUGIN_ROOT / "examples/settings.deny.non-merge.json").read_text())["permissions"]["deny"]

    def test_parses_with_claude_code_rule_syntax(self) -> None:
        self.assertTrue(self.deny and len(set(self.deny)) == len(self.deny))
        for rule in self.deny:
            self.assertRegex(rule, r"^((Bash|Read|Edit|Write)\(.+\)|mcp__[A-Za-z0-9_-]+__[a-z_]+)$")

    def test_real_command_spellings_are_denied(self) -> None:
        for command in ("git push --force origin x", "git -C repo push --force origin x", "git -c a=b push --force-with-lease", "git push -f",
                        "git push origin feature -f", "git push origin --delete feature", "git push origin :feature", "git push origin +feature",
                        "git push --mirror", "git push origin x --no-verify", "git -C r commit -m x --no-verify", "git commit -nm x",
                        "git reset --hard", "git -C repo reset --hard HEAD~1", "git -c core.x=1 reset --hard", "git clean -fd", "git clean -xfd",
                        "git -C r clean -f", "git branch -D x", "git -C r branch -D x", "git checkout .", "git restore .",
                        "rm -rf /", "rm -rf ~", "rm -r -f ~", "rm -fr ~", "rm -Rf /", 'rm -rf "$HOME"', "rm -rf $HOME", "rm -rf ${HOME}", "rm -rf ./.git",
                        "rm -rf .git", "rm -rf ..", "rm -rf sub/.git", "rm --recursive --force /",
                        "sudo ls", "ssh host", "cat .env", "cat ./.env.local", "head -3 .env", "grep KEY .env", "source .env", "cat app/.env",
                        "cat ~/.ssh/id_rsa", "cat ~/.config/pai-harness/token"):
            self.assertTrue(denied(self.deny, command), command)

    def test_ordinary_commands_are_not_denied(self) -> None:
        for command in ("git push origin feature-fix", "git push -u origin feature", "git push origin HEAD:feature", "git status", "git commit -m x",
                        "git clean -n", "rm -rf build", "rm file.txt", "cat README.md", "grep env README.md", "git push origin main-fix"):
            self.assertFalse(denied(self.deny + self.non_merge, command), command)

    def test_mcp_writes_are_denied_on_both_pai_servers_and_linear(self) -> None:
        for tool in ("iam_policy_set", "iam_binding_add", "product_deploy", "organization_member_remove", "crm_lead_purge", "user_ban"):
            for prefix in deny_baseline.PAI_PREFIXES:
                self.assertIn(prefix + tool, self.deny)
        self.assertIn("mcp__plugin_linear_linear__delete_comment", self.deny)
        self.assertNotIn("mcp__pai__knowledge_create", self.deny)  # the distiller's own writes stay allowed

    def test_merge_roles_are_not_denied_the_merge_and_others_are(self) -> None:
        for command in ("gh pr merge 51 --squash", "gh -R o/r pr merge 51", "git push origin main", "git push origin HEAD:main", "git push origin release/1.2"):
            self.assertFalse(denied(self.deny, command), command)  # the integrator documented flow can run
            self.assertTrue(denied(self.non_merge, command), command)  # every other role's worktree adds this file
        self.assertFalse(denied(self.non_merge, "git push origin main-fix"))

    def test_baseline_is_part_of_the_example(self) -> None:
        self.assertEqual([rule for rule in deny_baseline.BASELINE if rule not in self.deny], [])
        self.assertEqual(self.deny, deny_baseline.example_rules())  # the shipped file is the generated one
        self.assertEqual(self.non_merge, list(deny_baseline.NON_MERGE_RULES))

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
        rules = [r for r in deny_baseline.BASELINE if r != "mcp__pai__user_ban"]
        write_deny_settings(self.claude_home / "settings.json", rules)
        done = self.launch("ACME-7", "success", 0)
        self.blocked(done)
        self.assertIn("mcp__pai__user_ban", done.stdout)

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
        write_deny_settings(work / ".claude/settings.json", deny_baseline.BASELINE)
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
        self.assertEqual(json.loads(done.stdout)["deny_baseline_missing"], len(deny_baseline.BASELINE))

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
