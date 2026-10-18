"""Helper policy/transaction tests and native installation in an isolated Codex home."""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("codex_plugin", ROOT / "tools/codex_plugin.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)

CONFIG = '''# Keep the user's formatting and model.
model = "gpt-6.1-sol" # native model
favorite = { color = "blue", values = [1, 2] }
notes = """A string containing a table-like line:
[plugins."pai-console-production@pai-console-plugin"]
"""

[unrelated."with.dots"] # table comment
value = 'keep me' # retain this comment

[plugins."other@elsewhere"]
enabled = true # unrelated activation
'''
TOOLS = {"page_read": {"readOnly": True}, "page_create": {"readOnly": False}, "broken": {}}


class CodexHelperTest(unittest.TestCase):
    def test_symlinked_and_dangling_configs_are_preserved_before_native_commands(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "dotfiles.toml"
            target.write_text(CONFIG)
            for exists in (True, False):
                for dry_run in (True, False):
                    with self.subTest(target_exists=exists, dry_run=dry_run):
                        home = root / f"home-{exists}-{dry_run}"
                        home.mkdir()
                        link_target = target if exists else root / "absent.toml"
                        link = home / "config.toml"
                        link.symlink_to(link_target)
                        with patch.object(helper, "run_cli") as native:
                            with self.assertRaisesRegex(ValueError, "Symlinked"):
                                helper.configure(home, "staging", ROOT, dry_run=dry_run)
                            native.assert_not_called()
                        self.assertTrue(link.is_symlink())
                        self.assertEqual(link.readlink(), link_target)
                        self.assertEqual(target.read_text(), CONFIG)
                        self.assertEqual(list(home.iterdir()), [link])

    def test_atomic_write_does_not_replace_a_concurrently_created_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "external.toml"
            target.write_text(CONFIG)
            link = root / "config.toml"
            def external_writer(_fd):
                link.symlink_to(target)
            with patch.object(helper.os, "fsync", side_effect=external_writer):
                with self.assertRaisesRegex(ValueError, "symlinked"):
                    helper.atomic_write(link, b"changed")
            self.assertTrue(link.is_symlink())
            self.assertEqual(target.read_text(), CONFIG)

    def test_policy_matrix_unknown_and_stale_overrides(self):
        data = {"plugins": {"pai-console-production@pai-console-plugin": {"mcp_servers": {
            "pai_console_production": {"tools": {"future_tool": {"approval_mode": "approve"}}}}},
            "pai-console-staging@old-market": {"enabled": True}}}
        updates = helper.policy_updates(data, "develop", TOOLS)
        parsed = tomllib.loads(helper.update_toml(CONFIG, updates))
        self.assertFalse(parsed["plugins"]["pai-console-staging@old-market"]["enabled"])
        self.assertEqual(sum(v.get("enabled", False) for k, v in parsed["plugins"].items() if helper.PLUGIN.fullmatch(k)), 1)
        for env in helper.ENVIRONMENTS:
            server = parsed["plugins"][f"pai-console-{env}@{helper.MARKETPLACE}"]["mcp_servers"][f"pai_console_{env}"]
            self.assertEqual(server["default_tools_approval_mode"], "prompt")
            self.assertEqual(server["tools"]["page_read"]["approval_mode"], "approve")
            self.assertEqual(server["tools"]["page_create"]["approval_mode"], "prompt" if env == "production" else "approve")
            self.assertEqual(server["tools"]["broken"]["approval_mode"], "prompt")
        self.assertEqual(parsed["plugins"]["pai-console-production@pai-console-plugin"]["mcp_servers"]["pai_console_production"]["tools"]["future_tool"]["approval_mode"], "prompt")
        unknown = helper.policy_updates({}, "unrecognized", TOOLS)
        self.assertFalse(any(value is True for key, value in unknown.items() if key[-1] == "enabled" and len(key) == 3))

    def test_synced_iam_chats_and_tasks_use_native_production_prompts(self):
        tools = json.loads((ROOT / "hooks/tools.json").read_text())["tools"]
        parsed = tomllib.loads(helper.update_toml(CONFIG, helper.policy_updates({}, "production", tools)))
        for env in helper.ENVIRONMENTS:
            server = parsed["plugins"][f"pai-console-{env}@{helper.MARKETPLACE}"]["mcp_servers"][f"pai_console_{env}"]
            self.assertEqual(server["default_tools_approval_mode"], "prompt")
            for tool in ("iam_access_test", "iam_policy_get", "task_list_mine", "chat_get"):
                self.assertEqual(server["tools"][tool]["approval_mode"], "approve")
            for tool in ("iam_policy_set", "task_complete", "chat_send", "crm_lead_anonymize", "knowledge_merge"):
                self.assertEqual(server["tools"][tool]["approval_mode"], "prompt" if env == "production" else "approve")
            self.assertNotIn("crm_task_create", server["tools"])

    def test_unique_server_policy_leaves_existing_generic_pai_policy_unchanged(self):
        text = CONFIG + '\n[mcp_servers.pai] # unrelated generic server\ndefault_tools_approval_mode = "approve"\n\n[plugins."pai-console-production@pai-console-plugin".mcp_servers.pai] # unrelated generic policy\ndefault_tools_approval_mode = "writes"\n'
        data = tomllib.loads(text)
        updates = helper.policy_updates(data, "production", TOOLS)
        self.assertFalse(any("pai" in key for key in updates))
        output = helper.update_toml(text, updates)
        parsed = tomllib.loads(output)
        self.assertTrue(output.startswith(text))
        self.assertEqual(parsed["mcp_servers"]["pai"], data["mcp_servers"]["pai"])
        identity = "pai-console-production@pai-console-plugin"
        self.assertEqual(parsed["plugins"][identity]["mcp_servers"]["pai"], data["plugins"][identity]["mcp_servers"]["pai"])
        self.assertEqual(parsed["plugins"][identity]["mcp_servers"]["pai_console_production"]["default_tools_approval_mode"], "prompt")

    def test_preserves_comments_strings_unrelated_config_and_is_idempotent(self):
        updates = helper.policy_updates(tomllib.loads(CONFIG), "production", TOOLS)
        output = helper.update_toml(CONFIG, updates)
        self.assertTrue(output.startswith(CONFIG))
        second = helper.update_toml(output, updates)
        self.assertEqual(output, second)
        text = '[plugins."pai-console-staging@pai-console-plugin"] # retain\nenabled = true # inline\n'
        changed = helper.update_toml(text, {("plugins", "pai-console-staging@pai-console-plugin", "enabled"): False})
        self.assertEqual(changed, text.replace("= true", "= false"))

    def test_array_tables_and_dotted_owned_keys_preserve_unrelated_content(self):
        text = '\n'.join([
            '[plugins]',
            '"pai-console-staging@pai-console-plugin".enabled = true # keep',
            '[[unrelated]]',
            'enabled = true # unrelated array field',
            'description = """Text ends with a quote""""',
            '',
        ])
        path = ("plugins", "pai-console-staging@pai-console-plugin", "enabled")
        output = helper.update_toml(text, {path: False})
        self.assertEqual(output, text.replace('.enabled = true', '.enabled = false'))
        parsed = tomllib.loads(output)
        self.assertTrue(parsed["unrelated"][0]["enabled"])

    def test_owned_inline_layout_fails_safely(self):
        with self.assertRaises(ValueError):
            helper.update_toml('plugins = { "pai-console-staging@pai-console-plugin" = { enabled = true } }\n',
                               {("plugins", "pai-console-staging@pai-console-plugin", "enabled"): False})

    def test_status_and_dry_run_do_not_write_or_run_cli(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory) / "does-not-exist"
            self.assertFalse(helper.status(home)["exactly_one_environment"])
            with patch.object(helper, "run_cli", side_effect=AssertionError("dry run invoked CLI")):
                plan = helper.configure(home, "staging", ROOT, dry_run=True)
            self.assertTrue(plan["dry_run"])
            self.assertFalse(home.exists())
            self.assertEqual(plan["commands"][1][1:3], ["plugin", "add"])

    def test_mock_cli_failure_restores_config_and_keeps_atomic_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            path.write_text(CONFIG)
            def fake_cli(executable, arguments, selected_home, cwd):
                self.assertEqual(selected_home, home)
                if arguments[-1] == "--help":
                    return "Usage: <SOURCE> PLUGIN --json"
                raise ValueError("mock install failure")
            with patch.object(helper, "run_cli", side_effect=fake_cli):
                with self.assertRaisesRegex(ValueError, "mock install failure"):
                    helper.configure(home, "develop", ROOT)
            self.assertEqual(path.read_text(), CONFIG)
            backups = list(home.glob(".pai-backup-*.toml"))
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].read_text(), CONFIG)
            self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)

    def test_normal_failure_after_native_marketplace_edit_restores_original(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            path.write_text(CONFIG)
            def fake_cli(executable, arguments, selected_home, cwd):
                if arguments[-1] == "--help":
                    return "Usage: <SOURCE> PLUGIN --json"
                if arguments[:3] == ["plugin", "marketplace", "add"]:
                    path.write_text(path.read_text() + '\n[marketplaces.pai-console-plugin]\nsource_type = "local"\nsource = ' + json.dumps(str(ROOT)) + '\n')
                    return "{}"
                raise ValueError("ordinary native install failure")
            with patch.object(helper, "run_cli", side_effect=fake_cli):
                with self.assertRaisesRegex(ValueError, "ordinary native install failure"):
                    helper.configure(home, "staging", ROOT)
            self.assertEqual(path.read_text(), CONFIG)
            self.assertEqual(next(home.glob(".pai-backup-*.toml")).read_text(), CONFIG)

    def test_optimistic_conflict_preserves_concurrent_edits_and_reports_backup(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            path.write_text(CONFIG)
            original_update = helper.update_toml
            writes = []
            def racing_update(text, updates):
                output = original_update(text, updates)
                writes.append(output)
                if len(writes) == 3:
                    # Another writer changes unrelated config after our final read.
                    path.write_text(path.read_text() + '\n[concurrent] # keep this comment\nvalue = "external edit"\n')
                return output
            def fake_cli(executable, arguments, selected_home, cwd):
                return "Usage: <SOURCE> PLUGIN --json" if arguments[-1] == "--help" else "{}"
            with patch.object(helper, "run_cli", side_effect=fake_cli), patch.object(helper, "update_toml", side_effect=racing_update):
                with self.assertRaisesRegex(ValueError, "preserved current contents.*Original backup:") as caught:
                    helper.configure(home, "staging", ROOT)
            current = path.read_text()
            self.assertIn('[concurrent] # keep this comment\nvalue = "external edit"', current)
            self.assertTrue(current.startswith(CONFIG))
            backup = next(home.glob(".pai-backup-*.toml"))
            self.assertIn(str(backup), str(caught.exception))
            self.assertEqual(backup.read_text(), CONFIG)

    def test_failed_native_command_with_changed_config_does_not_overwrite_it(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            path.write_text(CONFIG)
            changed = []
            def fake_cli(executable, arguments, selected_home, cwd):
                if arguments[-1] == "--help":
                    return "Usage: <SOURCE> PLUGIN --json"
                changed.append(path.read_text() + '\n# Concurrent or native config edit must survive.\n')
                path.write_text(changed[0])
                raise ValueError("native install failed")
            with patch.object(helper, "run_cli", side_effect=fake_cli):
                with self.assertRaisesRegex(ValueError, "preserved current contents.*Original backup:"):
                    helper.configure(home, "staging", ROOT)
            self.assertEqual(path.read_text(), changed[0])
            self.assertEqual(next(home.glob(".pai-backup-*.toml")).read_text(), CONFIG)

    def test_git_snapshot_discovery_preserves_git_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            git_config = CONFIG + '\n[marketplaces.pai-console-plugin]\nsource_type = "git"\nsource = "https://github.com/pailat/pai-console-plugin.git"\nref = "main" # keep Git tracking\n'
            path.write_text(git_config)
            calls = []
            def fake_cli(executable, arguments, selected_home, cwd):
                calls.append(arguments)
                if arguments[-1] == "--help":
                    return "Usage: <SOURCE> PLUGIN --json"
                if arguments == ["plugin", "marketplace", "list", "--json"]:
                    return json.dumps({"marketplaces": [{"name": helper.MARKETPLACE, "root": str(ROOT),
                        "marketplaceSource": {"sourceType": "git", "source": "https://github.com/pailat/pai-console-plugin.git"}}]})
                return "{}"
            with patch.object(helper, "run_cli", side_effect=fake_cli):
                result = helper.configure(home, "develop")
            self.assertTrue(result["exactly_one_environment"])
            self.assertEqual(result["active"], ["pai-console-develop@pai-console-plugin"])
            self.assertEqual(tomllib.loads(path.read_text())["marketplaces"][helper.MARKETPLACE]["source_type"], "git")
            self.assertIn('ref = "main" # keep Git tracking', path.read_text())
            self.assertNotIn(["plugin", "marketplace", "add", str(ROOT), "--json"], calls)
            self.assertIn(["plugin", "marketplace", "list", "--json"], calls)
            with patch.object(helper, "run_cli", side_effect=AssertionError("explicit dry run invoked CLI")):
                self.assertTrue(helper.configure(home, "production", ROOT, dry_run=True)["dry_run"])
            def explicit_cli(executable, arguments, selected_home, cwd):
                if arguments[:3] == ["plugin", "marketplace", "list"]:
                    raise AssertionError("explicit snapshot root performed discovery")
                return "Usage: <SOURCE> PLUGIN --json" if arguments[-1] == "--help" else "{}"
            with patch.object(helper, "run_cli", side_effect=explicit_cli):
                self.assertEqual(helper.configure(home, "production", ROOT)["active"], ["pai-console-production@pai-console-plugin"])

    def test_unsupported_cli_does_not_mutate_config(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            (home / "config.toml").write_text(CONFIG)
            with patch.object(helper, "run_cli", return_value="Unsupported CLI"):
                with self.assertRaisesRegex(ValueError, "does not support"):
                    helper.configure(home, "staging", ROOT)
            self.assertEqual((home / "config.toml").read_text(), CONFIG)

    def test_mock_native_commands_single_activation_and_packaged_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            path = home / "config.toml"
            path.write_text(CONFIG)
            calls = []
            def fake_cli(executable, arguments, selected_home, cwd):
                calls.append(arguments)
                if arguments[-1] == "--help":
                    return "Usage: <SOURCE> PLUGIN --json"
                self.assertEqual(selected_home, home)
                return "{}"
            with patch.object(helper, "run_cli", side_effect=fake_cli):
                for environment in ("staging", "production", "develop"):
                    result = helper.configure(home, environment, ROOT)
                    self.assertEqual(result["active"], [f"pai-console-{environment}@{helper.MARKETPLACE}"])
                    self.assertTrue(path.read_text().startswith(CONFIG))
            self.assertEqual(sum(call[:2] == ["plugin", "add"] and call[-1] != "--help" for call in calls), 3)


@unittest.skipUnless(shutil.which("codex"), "Native Codex CLI is unavailable")
class NativeCodexInstallTest(unittest.TestCase):
    def test_real_portable_install_and_switch_in_temporary_home(self):
        # No model call, OAuth, credential copying, or real user's config access.
        with tempfile.TemporaryDirectory(prefix="pai native install ") as directory:
            isolated = Path(directory)
            home = isolated / "codex-home"
            home.mkdir()
            (home / "config.toml").write_text(CONFIG)
            env = {**os.environ, "CODEX_HOME": str(home)}
            version = subprocess.run(["codex", "--version"], env=env, cwd=isolated,
                                     capture_output=True, text=True, check=True).stdout.strip()
            self.assertIn("codex-cli", version)
            for environment in ("staging", "production", "develop"):
                result = helper.configure(home, environment, ROOT)
                self.assertTrue(result["exactly_one_environment"])
                self.assertEqual(result["active"], [f"pai-console-{environment}@{helper.MARKETPLACE}"])
            listing = subprocess.run(["codex", "plugin", "list", "--json"], env=env, cwd=isolated,
                                     capture_output=True, text=True, check=True)
            installed = json.loads(listing.stdout)["installed"]
            pai = [entry for entry in installed if entry["name"].startswith("pai-console-")]
            self.assertEqual(len(pai), 3)
            self.assertEqual([entry["name"] for entry in pai if entry["enabled"]], ["pai-console-develop"])
            self.assertTrue((home / "config.toml").read_text().startswith(CONFIG))
            for environment in helper.ENVIRONMENTS:
                cached = home / "plugins/cache" / helper.MARKETPLACE / f"pai-console-{environment}" / "0.0.9"
                self.assertTrue((cached / "plugin.json").is_file())
                self.assertFalse((cached / ".codex-plugin/plugin.json").exists())
                self.assertTrue((cached / "hooks/codex.py").is_file())
                self.assertTrue((cached / "hooks/policy.py").is_file())
                mcp = json.loads((cached / "mcp.json").read_text())
                self.assertEqual(mcp["mcpServers"][f"pai_console_{environment}"]["url"], helper.ENVIRONMENTS[environment])
                for skill_name in ("pai-env", "setup"):
                    loaded_skill_dir = cached / "skills" / skill_name
                    process = subprocess.run(["bash", "-c", 'pai_skill_dir="$1"\npython3 "$pai_skill_dir/../../tools/codex_plugin.py" status',
                                              "pai-skill-test", str(loaded_skill_dir)],
                                             env=env, cwd=isolated, capture_output=True, text=True, check=True)
                    self.assertEqual(json.loads(process.stdout)["active"], ["pai-console-develop@pai-console-plugin"])
            self.assertFalse((home / "auth.json").exists())



if __name__ == "__main__":
    unittest.main()
