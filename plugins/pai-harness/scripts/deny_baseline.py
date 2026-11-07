"""The deny-rule baseline that bypassPermissions needs, and the launcher preflight that checks it.

Bypass auto-approves everything a deny rule does not stop, including every MCP tool, so a run starts only when the
effective Claude Code settings carry these rules. The check reads the user, project, local and managed settings files;
it is presence only (the exact rule strings), never a proof that every spelling of a command is caught: the plugin hooks
are the second layer for git and zone rules, and nothing here covers a command that reads a secret through an interpreter.
Stdlib only. Run it standalone on every machine that runs bypass agents, before starting them (an interactive agent start never goes
through launch.py): `deny_baseline.py --check [--cwd DIR] [--role ROLE] [--strict]` exits 0 when the baseline is present and 1 when it is not.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

PAI_PREFIXES = ("mcp__pai__", "mcp__plugin_pai-console_pai__")  # the harness machine server, and the interactive plugin server
LINEAR_PREFIX = "mcp__plugin_linear_linear__"
RAILWAY_PREFIXES = ("mcp__railway__", "mcp__plugin_railway_railway__")
MERGE_ROLES = ("integrator", "orchestrator")  # the roles that merge by design; every other role also needs NON_MERGE_RULES

# MCP deny patterns by verb, not by hand-picked tool: a new Pai tool whose name carries one of these verbs is denied without a list update.
# Hooks never see MCP calls, so under bypass these rules are the only layer for MCP writes.
PAI_PATTERNS = tuple(f"*{verb}*" for verb in ("delete", "remove", "revoke", "deploy", "publish", "purge", "anonymize", "terminate", "void",
                                              "rotate", "renounce", "staff_grant", "enrollment_approve", "archive", "merge", "unlink")) + (
    "iam_*", "finance_*", "workforce_*", "*_ban", "*_unban", "*_win", "*slug_set", "*domain_set", "*production_access_set", "*member_role_set",
    "*_provision", "*_set", "*_save", "*_attach", "*_record", "*_invite*", "*_join*", "*_import", "connection_create", "user_create", "user_export", "organization_export", "organization_archive", "project_close",
)
LINEAR_PATTERNS = ("delete_*", "merge_diff")
RAILWAY_PATTERNS = ("delete-*", "*deploy*", "redeploy", "restart-service", "purge-cdn-cache", "reset-bucket-credentials", "set-variables",
                    "set-feature-flag", "update-function-source-code", "connect-service-source")

# Rules every role needs. `*` matches any characters (spaces included), so `git *push` also covers `git -C repo push`.
BASE_RULES = (
    "Bash(git *push *--force*)", "Bash(git *push -f*)", "Bash(git *push * -f*)", "Bash(git *push *--delete*)", "Bash(git *push -d *)",
    "Bash(git *push * -d *)", "Bash(git *push *--mirror*)", "Bash(git *push * +*)", "Bash(git *push * :**)", "Bash(git *push *--no-verify*)",
    "Bash(git *commit *--no-verify*)", "Bash(git *commit -n*)", "Bash(git *commit * -n)",
    "Bash(git *reset --hard*)", "Bash(git *clean *-*f*)", "Bash(git *branch -D *)", "Bash(git *branch *--delete *--force*)",
    "Bash(git *checkout .)", "Bash(git *checkout -- .)", "Bash(git *restore .)", "Bash(git *restore --staged --worktree .)",
    "Bash(sudo *)", "Bash(su *)", "Bash(ssh *)", "Bash(scp *)", "Bash(sftp *)",
)
# rm: only the whole-target spellings are denied (end-anchored), so scratch-directory cleanup (dist, ./build, node_modules, mktemp dirs) still runs.
# A backslash-star is a literal star: the glob spellings (rm -rf /*, ~/*, $HOME/*, ./*) are their own targets.
RM_TARGETS = ("/", "~", "~/", "$HOME", "$HOME/", '"$HOME"', "${HOME}", "..", "../", ".", "./", ".git", "./.git", "*/.git",
              "/\\*", "~/\\*", "$HOME/\\*", '"$HOME"/\\*', "${HOME}/\\*", "./\\*", "../\\*", ".git/\\*",
              "/etc", "/usr", "/var", "/bin", "/sbin", "/lib", "/boot", "/home", "/root", "/opt", "/sys", "/proc", "/dev")
RM_RULES = tuple(f"Bash(rm *{flag}* {target})" for target in RM_TARGETS for flag in ("r", "R"))
# Secrets: real env files only (.env.example and friends stay readable), through the common readers, and the credential directories.
ENV_FILES = (".env", ".env.l*",  # l* covers the local variant (spelled out, it reads as a hostname to the denylist test)
             ".env.p*", ".env.d*", ".env.staging", ".env.test")
READERS = ("cat", "head", "tail", "less", "grep", "rg", "source", "sed")  # cp is not a reader here: cp .env.example .env must run
# The env file must start a token (after a space or a slash), so code that mentions the name (process.env, import.meta.env) is never denied.
ENV_LEADS = ("{r} {e}", "{r} * {e}", "{r} */{e}")
ENV_RULES = tuple(rule for env in ENV_FILES for rule in (f"Read(./{env})", f"Read(**/{env})", f"Edit(./{env})", f"Write(./{env})"))
SECRET_RULES = tuple(f"Bash({lead.format(r=reader, e=env)}{tail})" for reader in READERS for env in ENV_FILES for lead in ENV_LEADS for tail in ("", " *")) + (
    "Bash(*~/.ssh/*)", "Bash(*~/.aws/*)", "Bash(*.config/gh/*)", "Bash(*pai-harness/token*)",
    "Read(~/.ssh/**)", "Read(~/.aws/**)", "Read(~/.config/gh/**)", "Read(~/.config/pai-harness/token)",
    "Edit(~/.ssh/**)", "Write(~/.ssh/**)", "Read(**/*.pem)", "Read(**/*.key)", "Read(**/secrets/**)",
)
MCP_RULES = (tuple(f"{prefix}{pattern}" for prefix in PAI_PREFIXES for pattern in PAI_PATTERNS)
             + tuple(f"{LINEAR_PREFIX}{pattern}" for pattern in LINEAR_PATTERNS)
             + tuple(f"{prefix}{pattern}" for prefix in RAILWAY_PREFIXES for pattern in RAILWAY_PATTERNS))
STRICT_MCP_RULES = tuple(f"{PAI_PREFIXES[0]}{pattern}" for pattern in PAI_PATTERNS)  # strict MCP: the machine config's one server is all there is

# Rules for every role except the integrator and the orchestrator, which merge by documented design (see examples/README.md).
def _protected(branch: str) -> tuple[str, ...]:
    """Destinations written bare, as src:dst, as refs/heads/..., or as a remote-qualified name, each as the last argument or followed by more."""
    return tuple(f"Bash(git *push *{sep}{branch}{tail})" for sep in (" ", ":", "/") for tail in ("", " *"))


NON_MERGE_RULES = (
    "Bash(gh *pr merge*)", *_protected("main"), *_protected("master"),
    "Bash(git *push * release/*)", "Bash(git *push *:release/*)", "Bash(git *push *refs/heads/release/*)",
)  # a bare `git push` on a protected branch has no destination to match: the push queue guard in the hooks is the layer for it
OTHER_RULES = (
    "Bash(gh repo delete *)", "Bash(gh repo archive *)", "Bash(gh release delete *)", "Bash(gh api -X DELETE *)", "Bash(gh api --method DELETE *)",
    "Bash(gh secret *)", "Bash(gh auth token*)",
    "Bash(terraform apply*)", "Bash(terraform destroy*)", "Bash(kubectl delete *)", "Bash(docker system prune*)", "Bash(docker volume rm *)",
    "Bash(railway delete*)", "Bash(railway down*)", "Bash(railway volume delete*)",
)


def baseline(strict: bool, role: str) -> tuple[str, ...]:
    """What a launch requires: git, rm, privilege and secret rules; the MCP verb rules (the machine server only under strict MCP,
    every known server otherwise); and the merge and protected-branch rules for every role that does not merge."""
    return (BASE_RULES + RM_RULES + SECRET_RULES + ENV_RULES + (STRICT_MCP_RULES if strict else MCP_RULES)
            + (() if role in MERGE_ROLES else NON_MERGE_RULES))


def example_rules() -> list[str]:
    """The rules of examples/settings.deny.json (every role); the merge rules ship in settings.deny.non-merge.json."""
    return list(dict.fromkeys(BASE_RULES + RM_RULES + SECRET_RULES + ENV_RULES + OTHER_RULES + MCP_RULES))


def glob_match(pattern: str, text: str) -> bool:
    """`*` matches any characters, a backslash-star is a literal star, everything else is literal."""
    regex = "".join(".*" if c == "*" else re.escape(c) for c in re.sub(r"\\\*", "\0", pattern))
    return re.fullmatch(regex.replace("\0", re.escape("*")), text, re.S) is not None


def covers(effective: str, wanted: str) -> bool:
    """Whether one effective deny rule satisfies one baseline rule: equal, a wildcard rule that matches it (`mcp__pai__iam_*` covers
    `mcp__pai__iam_policy_set`), or a whole-server rule (`mcp__pai`). Approximate by design: it never proves what Claude Code enforces."""
    if effective == wanted:
        return True
    if wanted.startswith("mcp__"):
        server = wanted.split("__")[1] if wanted.count("__") >= 2 else ""
        return effective == f"mcp__{server}" or (effective.startswith("mcp__") and glob_match(effective, wanted))
    kind = wanted.split("(", 1)[0]
    if effective.startswith(kind + "(") and effective.endswith(")") and wanted.endswith(")"):
        return glob_match(effective[len(kind) + 1:-1], wanted[len(kind) + 1:-1])
    return False


def settings_files(cwd: str | os.PathLike | None) -> list[Path]:
    """The settings files Claude Code merges for a run in `cwd`: managed (Linux, macOS, drop-ins), user, then the project and local
    settings of `cwd` itself (claude loads project settings from the directory it starts in, so a parent git root is not counted)."""
    user = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
    managed = [Path("/etc/claude-code/managed-settings.json"), Path("/Library/Application Support/ClaudeCode/managed-settings.json")]
    managed += sorted(Path("/etc/claude-code/managed-settings.d").glob("*.json"))
    root = Path(cwd or os.getcwd())
    return managed + [user / "settings.json", root / ".claude/settings.json", root / (".claude/settings" + ".local.json")]  # split: a bare dotted name reads as a hostname to the denylist test


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


def missing_baseline(cwd: str | os.PathLike | None, strict: bool, role: str) -> list[str]:
    """Baseline rules no effective deny rule covers (empty when the baseline is present)."""
    have = effective_deny(settings_files(cwd))
    return [rule for rule in baseline(strict, role) if not any(covers(rule_, rule) for rule_ in have)]


def preflight_reason(missing: list[str]) -> str | None:
    """The BLOCKER reason when the baseline is incomplete, else None."""
    if not missing:
        return None
    shown = ", ".join(missing[:3]) + (f" and {len(missing) - 3} more" if len(missing) > 3 else "")
    return (f"bypassPermissions needs the deny baseline and {len(missing)} rules are missing from the effective Claude Code settings ({shown}); "
            "copy examples/settings.deny.json (and settings.deny.non-merge.json for a role that does not merge) into .claude/settings.json, "
            "or set [run] bypass_permissions = false")


def report(cwd: str | os.PathLike | None, strict: bool, role: str) -> dict:
    """The check result: whether the baseline is present, the rules missing, and every settings file looked at (and whether it exists)."""
    files = settings_files(cwd)
    have = effective_deny(files)
    missing = [rule for rule in baseline(strict, role) if not any(covers(rule_, rule) for rule_ in have)]
    return {"ok": not missing, "role": role, "strict_mcp": strict, "cwd": str(Path(cwd or os.getcwd())), "missing": missing,
            "settings_files": [{"path": str(f), "exists": f.is_file()} for f in files]}


def loud_message(result: dict, limit: int = 15) -> str:
    """A named, multi-line FAIL text: the count, the settings files read, the first missing rules and the fix."""
    missing = result["missing"]
    lines = [f"FAIL deny-baseline: {len(missing)} deny rules are missing for role {result['role']} in {result['cwd']}; "
             "bypass agents must not start on this machine until they are installed."]
    lines += [f"  settings {'found' if f['exists'] else 'absent'}: {f['path']}" for f in result["settings_files"]]
    lines += [f"  missing {rule}" for rule in missing[:limit]]
    if len(missing) > limit:
        lines.append(f"  ... and {len(missing) - limit} more")
    lines.append("Fix: copy examples/settings.deny.json (and settings.deny.non-merge.json for a role that does not merge) into ~/.claude/settings.json "
                 "or the project's .claude/settings.json, then run this check again.")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="deny_baseline.py", description="Check that the effective Claude Code settings carry the deny baseline.")
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--cwd", help="the directory the agent will start in (default: the current directory)")
    parser.add_argument("--role", default="implementer", help="the agent's role (default implementer; integrator and orchestrator may merge)")
    parser.add_argument("--strict", action="store_true", help="strict MCP is in force (only the machine Pai server is loaded)")
    args = parser.parse_args(argv)
    result = report(args.cwd, args.strict, args.role)
    if result["ok"]:
        print(f"OK deny-baseline: present for role {args.role} in {result['cwd']}")
        return 0
    print(loud_message(result), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
