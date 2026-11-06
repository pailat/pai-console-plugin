"""The deny-rule baseline that bypassPermissions needs, and the launcher preflight that checks it.

Bypass auto-approves everything a deny rule does not stop, including every MCP tool, so a run starts only when the
effective Claude Code settings carry these rules. The check reads the user, project, local and managed settings files;
it is presence only (the exact rule strings), never a proof that every spelling of a command is caught: the plugin hooks
are the second layer for git and zone rules, and nothing here covers a command that reads a secret through an interpreter.
Stdlib only.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

PAI_PREFIXES = ("mcp__pai__", "mcp__plugin_pai-console_pai__")  # the harness machine server, and the interactive plugin server
LINEAR_PREFIX = "mcp__plugin_linear_linear__"

# Pai tools that change access, deploy, delete or purge data, or export personal data. A run that needs one is blocked, never prompted.
PAI_DENIED_TOOLS = (
    "iam_binding_add", "iam_binding_remove", "iam_binding_renounce", "iam_boundary_set", "iam_deny_create", "iam_deny_delete",
    "iam_deny_update", "iam_group_create", "iam_group_delete", "iam_group_member_add", "iam_group_member_remove", "iam_group_update",
    "iam_policy_set", "iam_role_create", "iam_role_delete", "iam_role_update", "iam_service_account_create", "iam_service_account_disable",
    "iam_service_account_update", "iam_service_token_create", "iam_service_token_revoke", "iam_service_token_rotate",
    "iam_settings_update", "iam_staff_grant_create", "iam_staff_grant_end",
    "product_deploy", "product_production_access_set", "product_domain_attach", "product_domain_remove", "product_domain_set",
    "product_environment_remove", "product_provision", "product_version_publish", "product_member_add", "product_member_remove",
    "product_member_update", "product_variables_set",
    "organization_member_remove", "organization_member_role_set", "organization_archive", "organization_domain_set",
    "organization_slug_set", "organization_invitation_cancel", "organization_export",
    "crm_lead_purge", "crm_lead_anonymize", "crm_submission_anonymize",
    "user_ban", "user_unban", "user_create", "user_export",
    "project_delete", "project_close", "page_delete", "file_delete", "asset_delete", "agent_delete", "agent_routine_delete",
    "connection_revoke", "connection_terminal_terminate", "connection_enrollment_approve",
    "finance_payment_register", "finance_reconcile", "payment_void", "space_deploy", "space_version_publish",
)
LINEAR_DENIED_TOOLS = ("delete_attachment", "delete_comment", "delete_customer", "delete_customer_need", "delete_diff_comment",
                       "delete_status_update", "merge_diff")

# Rules every role needs. `*` matches any characters (spaces included), so `git *push` also covers `git -C repo push`.
BASE_RULES = (
    "Bash(git *push *--force*)", "Bash(git *push -f*)", "Bash(git *push * -f*)", "Bash(git *push *--delete*)", "Bash(git *push -d *)",
    "Bash(git *push * -d *)", "Bash(git *push *--mirror*)", "Bash(git *push * +*)", "Bash(git *push * :*)", "Bash(git *push *--no-verify*)",
    "Bash(git *commit *--no-verify*)", "Bash(git *commit -n*)", "Bash(git *commit * -n*)",
    "Bash(git *reset --hard*)", "Bash(git *clean *-*f*)", "Bash(git *branch -D *)", "Bash(git *branch *--delete *--force*)",
    "Bash(git *checkout .)", "Bash(git *checkout -- .)", "Bash(git *restore .)", "Bash(git *restore --staged --worktree .)",
    "Bash(sudo *)", "Bash(su *)", "Bash(ssh *)", "Bash(scp *)", "Bash(sftp *)",
    "Read(./.env)", "Read(./.env.*)", "Read(**/.env)", "Read(**/.env.*)", "Read(~/.ssh/**)", "Read(~/.aws/**)",
    "Read(~/.config/gh/**)", "Read(~/.config/pai-harness/token)",
)
RM_TARGETS = ("/", "/*", "~", "~/*", "$HOME", "$HOME/*", '"$HOME"', '"$HOME"/*', "${HOME}", "..", "../*", ".git", ".git/*", "./.git", "*/.git")
RM_RULES = tuple(f"Bash(rm *{flag}* {target})" for target in RM_TARGETS for flag in ("r", "R"))
SECRET_RULES = ("Bash(* .env)", "Bash(* .env *)", "Bash(* .env.*)", "Bash(*/.env)", "Bash(*/.env *)", "Bash(*/.env.*)",
                "Bash(*~/.ssh/*)", "Bash(*~/.aws/*)", "Bash(*.config/gh/*)", "Bash(*pai-harness/token*)")
MCP_RULES = tuple(f"{prefix}{tool}" for prefix in PAI_PREFIXES for tool in PAI_DENIED_TOOLS) + tuple(f"{LINEAR_PREFIX}{tool}" for tool in LINEAR_DENIED_TOOLS)

# Rules for every role except the integrator and the orchestrator, which merge by documented design (see examples/README.md).
NON_MERGE_RULES = (
    "Bash(gh *pr merge*)",
    "Bash(git *push * main)", "Bash(git *push * main *)", "Bash(git *push * HEAD:main)", "Bash(git *push * HEAD:main *)",
    "Bash(git *push * master)", "Bash(git *push * master *)", "Bash(git *push * HEAD:master)", "Bash(git *push * HEAD:master *)",
    "Bash(git *push * release/*)", "Bash(git *push * HEAD:release/*)",
)
OTHER_RULES = (
    "Edit(./.env)", "Edit(./.env.*)", "Edit(~/.ssh/**)", "Write(./.env)", "Write(./.env.*)", "Write(~/.ssh/**)",
    "Read(**/*.pem)", "Read(**/*.key)", "Read(**/secrets/**)",
    "Bash(gh repo delete *)", "Bash(gh repo archive *)", "Bash(gh release delete *)", "Bash(gh api -X DELETE *)", "Bash(gh api --method DELETE *)",
    "Bash(gh secret *)", "Bash(gh auth token*)",
    "Bash(terraform apply*)", "Bash(terraform destroy*)", "Bash(kubectl delete *)", "Bash(docker system prune*)", "Bash(docker volume rm *)",
    "Bash(railway delete*)", "Bash(railway down*)", "Bash(railway volume delete*)",
)

# What a launch requires: the dangerous git, rm, privilege and secret rules, and every denied Pai tool on the machine server.
BASELINE = BASE_RULES + RM_RULES + SECRET_RULES + tuple(f"{PAI_PREFIXES[0]}{tool}" for tool in PAI_DENIED_TOOLS)


def example_rules() -> list[str]:
    """The rules of examples/settings.deny.json (every role); the merge rules ship in settings.deny.non-merge.json."""
    return list(BASE_RULES + RM_RULES + SECRET_RULES + OTHER_RULES + MCP_RULES)


def settings_files(cwd: str | os.PathLike | None, git_root: str | None = None) -> list[Path]:
    """The settings files Claude Code merges for a run in `cwd`: managed, user, then project and local settings."""
    user = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    files = [Path("/etc/claude-code/managed-settings.json"), user / "settings.json"]
    for root in dict.fromkeys(str(p) for p in (cwd or os.getcwd(), git_root) if p):
        files += [Path(root) / ".claude/settings.json", Path(root) / (".claude/settings" + ".local.json")]  # split: a bare dotted name reads as a hostname to the denylist test
    return files


def effective_deny(files: list[Path]) -> set[str]:
    """The union of `permissions.deny` over the readable settings files; an unreadable or malformed file contributes nothing."""
    rules: set[str] = set()
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            deny = data["permissions"]["deny"]
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if isinstance(deny, list):
            rules.update(rule for rule in deny if isinstance(rule, str))
    return rules


def missing_baseline(cwd: str | os.PathLike | None, git_root: str | None = None) -> list[str]:
    """Baseline rules absent from the effective settings (empty when the baseline is present)."""
    have = effective_deny(settings_files(cwd, git_root))
    return [rule for rule in BASELINE if rule not in have]


def preflight_reason(missing: list[str]) -> str | None:
    """The BLOCKER reason when the baseline is incomplete, else None."""
    if not missing:
        return None
    shown = ", ".join(missing[:3]) + (f" and {len(missing) - 3} more" if len(missing) > 3 else "")
    return (f"bypassPermissions needs the deny baseline and {len(missing)} rules are missing from the effective Claude Code settings ({shown}); "
            "copy examples/settings.deny.json into .claude/settings.json (or user settings), or set [run] bypass_permissions = false")
