#!/usr/bin/env python3
"""Run `claude -p` for one issue, inside a Herdr pane, and record its stream, state, cost and session id.

The run is never hidden: with --pane it runs in that pane; inside Herdr (HERDR_ENV=1) without --pane the launcher opens
its own tab; outside Herdr it runs in the foreground of your terminal. In every case the stream is teed to the JSONL log
and to render_stream.py, which prints one readable line per event, and (in Herdr) mirrors the run into workspace
metadata (state, task, run, step, turns, 2-minute TTL) and the tab label. That display never decides anything.

State comes only from the stream-json `result` frame and the exit code (see harness_lib.run_state); the Herdr agent
status is never read. A run that needs a permission is not given one: it ends `blocked` (exit 3).

Usage: launch.sh ISSUE (--prompt TEXT | --prompt-file FILE) [--pane PANE] [--model M] [--role R] [--cwd DIR]
                 [--queue Q] [--stream S] [--allowed-tools T ...] [--config FILE] [--dry-run]
       launch.sh ISSUE --profile mechanical --files F [F ...] --instruction TEXT [--model haiku|sonnet] [--cwd DIR]
                 the mechanical lane: a closed brief, Haiku, an empty strict MCP config, Read/Edit/Grep/Glob only, `--output-format json`;
                 check the result with verify-mechanical.sh before closing it (--files are relative to --cwd, which may be a repo subdirectory)
       launch.sh --resume ISSUE   continue a parked or blocked run by its recorded session id
       launch.sh --park ISSUE     mark a run parked (no process is touched)
       launch.sh --status ISSUE   print the recorded state
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_config  # noqa: E402
import harness_lib as lib  # noqa: E402
import mechanical_scope as scope  # noqa: E402
import render_stream  # noqa: E402


MECHANICAL_TOOLS = ("Read", "Edit", "Grep", "Glob")  # the whole tool set of the mechanical lane: no Bash, no MCP, no web
MECHANICAL_MODELS = ("haiku", "sonnet")  # Haiku by default; `--model sonnet` is the opt-in
GLOB_CHARS = set("*?")  # [ ] { } are valid filename characters (app/[slug]/page.tsx); paths are compared and passed to git as literals
LANE_ENV_KEYS = ("PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TERM", "TMPDIR", "TZ", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
                 "XDG_CACHE_HOME", "XDG_STATE_HOME", "XDG_RUNTIME_DIR", "CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN", "ANTHROPIC_API_KEY",
                 "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY", "http_proxy", "https_proxy",
                 "no_proxy", "all_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR", "NODE_EXTRA_CA_CERTS", "REQUESTS_CA_BUNDLE", "CLAUDE_CODE_USE_BEDROCK",
                 "CLAUDE_CODE_USE_VERTEX")  # what `claude` needs to run, sign in and reach the API; nothing of Pai, SSH or other credentials
BEDROCK_ENV = ("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN",
               "AWS_BEARER_TOKEN_BEDROCK", "ANTHROPIC_BEDROCK_BASE_URL")  # passed only when CLAUDE_CODE_USE_BEDROCK is set
VERTEX_ENV = ("GOOGLE_APPLICATION_CREDENTIALS", "ANTHROPIC_VERTEX_PROJECT_ID", "CLOUD_ML_REGION", "ANTHROPIC_VERTEX_BASE_URL")  # only with CLAUDE_CODE_USE_VERTEX
LANE_ENV_EXTRA = "PAI_HARNESS_LANE_ENV"  # the operator may name more variables (comma separated) to pass to the lane
LANE_ENV_SECRETS = "PAI_HARNESS_LANE_ENV_ALLOW_SECRETS"  # =1 lets LANE_ENV_EXTRA name credential-looking variables (printed when used)
SECRET_NAME = re.compile(r"TOKEN|SECRET|KEY|PASSWORD|CREDENTIAL|^PAI_HARNESS_", re.IGNORECASE)
HOOK_KEYS = ("PAI_HARNESS_ROLE", "PAI_HARNESS_AGENT", "PAI_HARNESS_ZONES", "PAI_HARNESS_BRIEF", "PAI_HARNESS_PUSH_WRAPPER", "PAI_HARNESS_BASE",
             "PAI_HARNESS_STREAM", "PAI_HARNESS_KNOWLEDGE_ORG", "PAI_HARNESS_KNOWLEDGE_PROJECT", "PAI_HARNESS_KNOWLEDGE_PRODUCT")
KNOWLEDGE_ENV = ("PAI_HARNESS_STREAM", "PAI_HARNESS_KNOWLEDGE_ORG", "PAI_HARNESS_KNOWLEDGE_PROJECT", "PAI_HARNESS_KNOWLEDGE_PRODUCT")


def stream_of(args: argparse.Namespace, state: Path | None = None) -> str | None:
    """The stream that picks the Knowledge target: --stream, else the queue name (a queue without an override uses the default)."""
    if args.stream:
        return args.stream
    queue = args.queue
    if not queue and state is not None:
        queue = (lib.read_json(run_paths(state, args.issue)[1]) or {}).get("queue")
    return queue


def knowledge_target(args: argparse.Namespace, config: dict, state: Path | None = None) -> dict | None:
    return harness_config.resolve_knowledge(config, stream_of(args, state))


def knowledge_header(args: argparse.Namespace, config: dict, state: Path | None = None) -> str:
    """The one-line brief header naming the Knowledge target; for the distiller with no target it says so (it then fails closed)."""
    target = knowledge_target(args, config, state)
    if target:
        scope = f"project={target['project']}" if "project" in target else f"product={target['product']}"
        label = f" stream={target['stream']}" if target["stream"] else ""
        return f"Knowledge target: organization={target['organization']} {scope}{label}\n\n"
    if (args.role or "implementer") == "distiller":
        return f"Knowledge target: none resolved for distiller/{stream_of(args, state) or 'default'}\n\n"
    return ""


def run_paths(state: Path, issue: str) -> tuple[Path, Path, Path]:
    runs = state / "runs"
    return runs / f"{issue}.jsonl", runs / f"{issue}.state.json", runs / f"{issue}.stderr.log"


def mcp_config_path(state: Path, issue: str) -> Path:
    return state / "mcp" / f"{issue}.json"


def write_empty_mcp_config(state: Path, issue: str) -> Path:
    """The mechanical lane's MCP config: no servers at all. With --strict-mcp-config no user or plugin server (Pai, OAuth) can load."""
    path = mcp_config_path(state, issue)
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_json(path, {"mcpServers": {}})
    return path


def closed_brief(instruction: str, files: list[str]) -> str:
    """The only input of a mechanical run: the exact instruction and the explicit list of files it may touch."""
    listing = "\n".join(f"- {f}" for f in files)
    return (f"Instruction (do exactly this, nothing else):\n{instruction.strip()}\n\n"
            f"Files you may change (the only ones; do not create, delete or rename files):\n{listing}\n\n"
            "Use only Read, Edit, Grep and Glob. If the instruction cannot be done inside these files, change nothing and say why in one line.\n")


def clean_files(files: list[str]) -> list[str]:
    """Validate the brief's file list: relative literal paths inside the worktree, no globs, no duplicates. Raises ValueError."""
    out: list[str] = []
    for raw in files:
        path = os.path.normpath(raw)
        if any(ord(c) < 32 or ord(c) == 127 for c in raw):
            raise ValueError(f"--files entry {raw!r} contains a control character or newline")
        if not raw.strip() or os.path.isabs(path) or path == ".." or path.startswith("../") or path == "." or GLOB_CHARS & set(raw):
            raise ValueError(f"--files entry {raw!r} must be a literal relative path inside the worktree (no glob, no ..)")
        if path.startswith(".git/") or path == ".git":
            raise ValueError(f"--files entry {raw!r} points into .git")
        if path not in out:
            out.append(path)
    return out


def worktree_dirty(cwd: str | None) -> bool:
    """True when the worktree has uncommitted or untracked changes (the verifier discards by path, so the lane starts from a clean tree)."""
    try:
        done = run_process(["git", "-C", str(cwd or os.getcwd()), "status", "--porcelain"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return True  # fail closed: a tree that cannot be inspected is not clean
    return done.returncode != 0 or bool(done.stdout.strip())


def pai_mcp_config(config: dict, config_path: Path) -> dict:
    """The machine-only MCP config: one `pai` server whose headers come from mcp_headers.sh (headersHelper), never a static header.

    headersHelper keeps working when the server also advertises OAuth (Claude Code issue 59467 ignores a static header there).
    The file holds a path and a URL, never the token: the helper reads the token file itself at connect time.
    """
    helper = shlex.join([str(Path(__file__).resolve().parent / "mcp_headers.sh"), "--config", str(config_path)])
    return {"mcpServers": {lib.PAI_SERVER: {"type": "http", "url": config["pai"]["mcp_url"], "headersHelper": helper}}}


def write_mcp_config(config: dict, state: Path, issue: str, config_path: Path) -> Path:
    path = mcp_config_path(state, issue)
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_json(path, pai_mcp_config(config, config_path))
    return path


SPENT_KEYS = ("input_tokens", "cache_write_tokens", "cache_read_tokens", "output_tokens")


def remaining_caps(args: argparse.Namespace, config: dict, previous: dict | None) -> tuple[int, float, str | None]:
    """The turn and dollar caps this invocation may spend: the role's caps minus what earlier invocations of the same issue already used.

    The caps bound the total per issue, not each invocation: a resume gets what is left, and when nothing is left the third value
    names why (the launcher then stops with a BLOCKER instead of retrying into the same cap).
    """
    caps = harness_config.role_limits(config, args.role or "implementer")
    spent = previous if (args.resume_run and previous) else {}
    turns = caps["max_turns"] - (spent.get("turns") or 0)
    budget = round(caps["max_budget_usd"] - (spent.get("cost_usd") or 0), 4)
    if turns < 1:
        return 0, budget, f"turn cap reached: {spent.get('turns')} of {caps['max_turns']} turns used (raise [role_limits.{args.role or 'implementer'}] max_turns)"
    if budget < harness_config.MIN_BUDGET_USD:
        return turns, budget, f"budget cap reached: ${spent.get('cost_usd')} of ${caps['max_budget_usd']} used (raise [role_limits.{args.role or 'implementer'}] max_budget_usd)"
    return turns, budget, None


def abs_rule(tool: str, path: str, tail: str = "/**") -> str:
    return f"{tool}(/{path}{tail})"  # a leading // is an absolute path in a Claude Code permission rule


def lane_permissions(args: argparse.Namespace, config: dict) -> tuple[list[str], list[str]]:
    """Scoped permission rules for the lane: Edit only under the run directory, never .git (the repo's and the common one), the harness state
    dir or a dependency directory; Read denied for credential and state locations (deny rules win over allows, so Read elsewhere is not
    confined: a deny of everything would also deny the worktree). Checked against the installed claude: an absolute Edit outside is denied."""
    cwd = str(Path(args.cwd or os.getcwd()).resolve())
    state = str(lib.state_dir(config).resolve())
    guarded = [state, str(Path("~/.config/pai-harness").expanduser()), *[str(Path(f"~/{d}").expanduser()) for d in (".ssh", ".aws", ".gnupg", ".config/gcloud", ".claude")]]
    git_dirs = []
    try:
        root, _ = scope.toplevel(cwd)
        git_dirs = [os.path.join(root, ".git"), scope.common_git_dir(root)]
    except scope.ScopeError:
        git_dirs = [os.path.join(cwd, ".git")]
    bulk = [os.path.join(cwd, d) for d in sorted(scope.BULK_DIRS) if os.path.isdir(os.path.join(cwd, d))]
    allow = [abs_rule("Read", cwd), abs_rule("Edit", cwd), "Grep", "Glob"]
    deny = [abs_rule("Edit", p) for p in (*guarded, *git_dirs, *bulk)] + [abs_rule("Edit", p, "") for p in git_dirs]
    deny += [abs_rule("Read", p) for p in (*guarded, *git_dirs)]
    return allow, list(dict.fromkeys(deny))


def claude_command(args: argparse.Namespace, config: dict, resume: str | None, mcp_config: Path | None = None, previous: dict | None = None) -> list[str]:
    model = args.model or config["models"].get(args.role or "implementer", "sonnet")
    output = ["--output-format", "json"] if args.profile else ["--output-format", "stream-json", "--verbose"]
    command = [os.environ.get("PAI_HARNESS_CLAUDE", "claude"), "-p", *output, "--model", model]
    if not lib.installed_plugin():
        command += ["--plugin-dir", str(lib.plugin_root())]  # every run loads the plugin, from the launcher's own location
    if mcp_config:  # only the machine config (the mechanical lane: an empty one): a user or plugin OAuth server must not stand in for it
        command += ["--mcp-config", str(mcp_config), "--strict-mcp-config"]
    # Budgets fail closed: every run carries a turn cap and a dollar cap (the role's, from [limits] / [role_limits]); claude stops the run when either is hit.
    turns, budget, _ = remaining_caps(args, config, previous)
    command += ["--max-turns", str(max(turns, 1)), "--max-budget-usd", format(budget, ".4f").rstrip("0").rstrip(".")]
    if resume:
        command += ["--resume", resume]
    if args.profile:  # the tool set is fixed: --tools removes every other built-in tool; the allow rules are scoped, and -p denies what no rule allows
        allow, deny = lane_permissions(args, config)
        command += ["--tools", ",".join(MECHANICAL_TOOLS), "--allowed-tools", *allow, "--disallowed-tools", *deny]
    elif args.allowed_tools:
        command += ["--allowed-tools", *args.allowed_tools]
    return command


def launch_base(args: argparse.Namespace, previous: dict) -> str | None:
    """The commit the Stop zone diff compares against: the one recorded when the run first started (a resume keeps it), else HEAD in the run cwd."""
    if args.resume_run and previous.get("base"):
        return previous["base"]
    try:
        done = run_process(["git", "-C", str(args.cwd or os.getcwd()), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 and done.stdout.strip() else None


def hook_env(args: argparse.Namespace, config: dict, state: Path, config_path: Path, write: bool = True, base: str | None = None) -> dict[str, str]:
    """The environment that activates the hooks for this run: role, agent, zones, brief, push wrapper, start commit and Knowledge command."""
    role = args.role or "implementer"
    if args.profile:
        return lane_env()
    env = {**os.environ, "PAI_HARNESS_ROLE": role, "PAI_HARNESS_AGENT": args.issue, "PAI_HARNESS_CONFIG": str(config_path),
           "PAI_HARNESS_STATE_DIR": str(state)}
    zones = config["role_zones"].get(role)
    if zones is not None:
        env["PAI_HARNESS_ZONES"] = ",".join(zones)
    else:
        env.pop("PAI_HARNESS_ZONES", None)  # a stale value must not leak in; the hooks fall back to zone owners
    if config["rules"]["push_wrapper"]:
        env["PAI_HARNESS_PUSH_WRAPPER"] = config["rules"]["push_wrapper"]
    else:
        env.pop("PAI_HARNESS_PUSH_WRAPPER", None)
    if base:
        env["PAI_HARNESS_BASE"] = base
    else:
        env.pop("PAI_HARNESS_BASE", None)  # a stale value must not leak in; zone_diff falls back to [project] base_branch
    if args.prompt_file:
        env["PAI_HARNESS_BRIEF"] = str(Path(args.prompt_file).resolve())
    elif args.prompt:
        brief = state / "briefs" / f"{args.issue}.md"
        if write:
            brief.parent.mkdir(parents=True, exist_ok=True)
            brief.write_text(args.prompt, encoding="utf-8")
        env["PAI_HARNESS_BRIEF"] = str(brief)
    env[harness_config.TOKEN_SCOPE_ENV] = harness_config.token_scope(config, os.environ)  # the distiller reads it: scope read means report only
    for key in KNOWLEDGE_ENV:
        env.pop(key, None)  # a stale target must not leak in; only the resolved one is exported
    target = knowledge_target(args, config, state)
    if target:
        env["PAI_HARNESS_KNOWLEDGE_ORG"] = target["organization"]
        env["PAI_HARNESS_KNOWLEDGE_PROJECT" if "project" in target else "PAI_HARNESS_KNOWLEDGE_PRODUCT"] = target.get("project") or target["product"]
    stream = stream_of(args, state)
    if stream:
        env["PAI_HARNESS_STREAM"] = stream
    # PAI_HARNESS_KNOWLEDGE_CMD has no config key (it is site tooling); an operator's value passes through the inherited environment.
    return env


def lane_env() -> dict[str, str]:
    """The environment of the mechanical lane: an allowlist, not os.environ, and no PAI_HARNESS_ROLE.

    No Pai/machine token variable, SSH or unrelated cloud credential reaches the child; the Bedrock or Vertex variables are passed only when that
    provider is selected. PAI_HARNESS_LANE_ENV adds names, but a credential-looking one (TOKEN, SECRET, KEY, PASSWORD, CREDENTIAL, PAI_HARNESS_*) is
    refused unless PAI_HARNESS_LANE_ENV_ALLOW_SECRETS=1, and the refusal is printed. Without PAI_HARNESS_ROLE the plugin hooks (Stop delta marker,
    zone checks) do nothing: the lane has no Write or MCP to satisfy them and its guard is the permission rules plus verify-mechanical.sh.
    """
    allowed = set(LANE_ENV_KEYS)
    if os.environ.get("CLAUDE_CODE_USE_BEDROCK"):
        allowed.update(BEDROCK_ENV)
    if os.environ.get("CLAUDE_CODE_USE_VERTEX"):
        allowed.update(VERTEX_ENV)
    for name in (n.strip() for n in os.environ.get(LANE_ENV_EXTRA, "").split(",") if n.strip()):
        if SECRET_NAME.search(name) and os.environ.get(LANE_ENV_SECRETS) != "1":
            print(f"mechanical lane: {LANE_ENV_EXTRA} name {name!r} looks like a credential and is NOT passed (set {LANE_ENV_SECRETS}=1 to allow it)", file=sys.stderr)
            continue
        allowed.add(name)
    return {k: v for k, v in os.environ.items() if k in allowed or k.startswith("LC_")}


class InitCheck:
    """Watches the stream for the first `system/init` event and proves the pai-harness plugin from it (fail closed)."""

    def __init__(self, skills: list[str], pai_server: str | None = None) -> None:
        self.skills, self.pai_server, self.problems, self.mcp, self.done = skills, pai_server, [], [], threading.Event()
        self.model: str | None = None  # the model id the init frame reports

    def feed(self, line: str) -> None:
        if self.done.is_set():
            return
        try:
            frame = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(frame, dict):
            return
        if frame.get("type") == "system" and frame.get("subtype") == "init":
            self.model = frame.get("model") if isinstance(frame.get("model"), str) else None
            self.problems = lib.init_problems(frame, self.skills)
            self.mcp = lib.mcp_problems(frame, self.pai_server) if self.pai_server else []
            self.done.set()
        elif frame.get("type") in ("assistant", "user", "result"):
            self.problems = ["init event came after the first model frame"]
            self.done.set()


def init_reason(problems: list[str], mcp: list[str]) -> str:
    """The BLOCKER reason: the plugin self-check first, then the named `pai mcp not connected`. Built from init field names only."""
    parts = (["pai-harness self-check failed: " + "; ".join(problems)] if problems else []) + (["pai mcp not connected: " + "; ".join(mcp)] if mcp else [])
    return "; ".join(parts)


def accumulate(previous: dict, resumed: bool, this: dict) -> dict:
    """The record fields after this invocation: totals over every invocation of the issue (a resume adds, never overwrites) plus the runs list.

    `this` holds the invocation's own cost_usd (None when no result frame), turns, token counts and peak context. A fresh launch starts a new
    accumulation; a resume continues the previous record's. An unpriced invocation adds no cost and is counted in `unpriced_runs`.
    """
    base = previous if resumed else {}
    runs = list(base.get("runs") or [])
    if base and not runs:  # a record written before `runs` existed counts as one earlier invocation
        runs.append({k: base.get(k) for k in ("run_id", "started", "finished", "state", "cost_usd", "turns", "reason", *SPENT_KEYS, "peak_context_tokens")})
    runs.append({k: this.get(k) for k in ("run_id", "started", "finished", "state", "cost_usd", "turns", "reason", *SPENT_KEYS, "peak_context_tokens")})
    priced = [r["cost_usd"] for r in runs if r.get("cost_usd") is not None]
    return {**{k: sum(r.get(k) or 0 for r in runs) for k in (*SPENT_KEYS, "turns")},
            "peak_context_tokens": max(r.get("peak_context_tokens") or 0 for r in runs),
            "cost_usd": round(sum(priced), 6) if priced else None, "unpriced_runs": len(runs) - len(priced), "invocations": len(runs), "runs": runs}


def fail_closed(args: argparse.Namespace, state: Path, started: str, stream: Path, queue: str | None, machine: str | None, problems: list[str],
                run_id: str | None = None, mcp: list[str] | None = None, previous: dict | None = None) -> int:
    """The plugin or the Pai MCP is not proven: the run is already killed; journal and print a BLOCKER, record failed, exit non-zero."""
    reason = init_reason(problems, mcp or [])
    lib.blocker(state, args.issue, reason)
    record = {"issue": args.issue, "queue": queue, "machine": machine, "role": args.role, "started": started, "finished": lib.stamp(),
              "stream": str(stream), "resumed": bool(args.resume_run), "state": "failed", "reason": reason, "exit_code": None,
              "session_id": None, "cost_usd": None, "turns": None, "run_id": run_id}
    if args.resume_run and previous:  # the failed self-check must not erase what the earlier invocations spent
        record.update({k: v for k, v in previous.items() if k in (*SPENT_KEYS, "peak_context_tokens", "cost_usd", "turns", "runs", "unpriced_runs", "invocations", "session_id")})
        record["failed_resume"] = {"run_id": run_id, "started": started, "reason": reason}
    lib.write_json(run_paths(state, args.issue)[1], record)
    lib.register(state, args.issue, state="failed")
    lib.emit(state, "run.finished", {k: record[k] for k in ("issue", "state", "reason", "exit_code", "session_id", "cost_usd", "turns")})
    return lib.EXIT_FAILED


def inner(args: argparse.Namespace, config: dict, state: Path, config_path: Path) -> int:
    """Run claude here, write the stream, then the state file. Returns the exit code of the launcher."""
    stream, state_file, stderr_log = run_paths(state, args.issue)
    previous = lib.read_json(state_file) or {}
    resume = previous.get("session_id") if args.resume_run else None
    if args.resume_run and not resume:
        print(f"{args.issue}: no recorded session id to resume", file=sys.stderr)
        return lib.EXIT_USAGE
    prompt = Path(args.prompt_file).read_text(encoding="utf-8") if args.prompt_file else (args.prompt or "")
    queue = args.queue or previous.get("queue")
    if resume:
        _, _, exhausted = remaining_caps(args, config, previous)
        if exhausted:  # fail closed: a capped issue is never resumed into a fresh allowance
            reason = f"{args.issue}: not resumed, {exhausted}"
            lib.blocker(state, args.issue, reason)
            lib.emit(state, "run.blocked", {"issue": args.issue, "role": args.role, "blocker": reason})
            print(reason, file=sys.stderr)
            return lib.EXIT_FAILED
    if not resume and not args.profile:  # the mechanical brief is closed: nothing is prepended to it
        prompt = knowledge_header(args, config, state) + prompt
    lane = None
    if args.profile:  # fail closed before anything runs: the repo root, the start commit and the ignored-files baseline the verifier compares against
        try:
            root, prefix = scope.toplevel(str(Path(args.cwd or os.getcwd()).resolve()))
            lane = {"root": root, "files": scope.root_relative(prefix, args.files), "ignored_baseline": str(scope.write_baseline(root, run_paths(state, args.issue)[1].with_name(f"{args.issue}.ignored.json")))}
        except (scope.ScopeError, OSError) as error:
            reason = f"{args.issue}: the mechanical lane cannot record its baseline: {error}"
            lib.blocker(state, args.issue, reason)
            lib.emit(state, "run.blocked", {"issue": args.issue, "role": args.role, "blocker": reason})
            print(f"BLOCKER {reason}", file=sys.stderr)
            return lib.EXIT_FAILED
    machine = config["queues"].get(queue or "", {}).get("machine")
    started = lib.stamp()
    stream.parent.mkdir(parents=True, exist_ok=True)
    base = launch_base(args, previous)
    lib.register(state, args.issue, state="running", queue=queue, machine=machine, role=args.role, stream=str(stream), base=base)
    lib.emit(state, "run.started", {"issue": args.issue, "queue": queue, "resume": bool(resume)})
    timeout = config["limits"]["turn_timeout_minutes"] * 60
    exit_code, timed_out, last_beat, lines = None, False, time.monotonic(), []
    if args.profile:
        mcp_config = write_empty_mcp_config(state, args.issue)  # always empty and strict: the Pai MCP, its token and OAuth never reach this lane
    else:
        mcp_config = write_mcp_config(config, state, args.issue, config_path) if config["pai"]["mcp_url"] else None
    init = InitCheck(lib.expected_skills(lib.plugin_root()), lib.PAI_SERVER if mcp_config and not args.profile else None)
    run_id = uuid.uuid4().hex[:8]
    renderer = render_stream.Renderer(sys.stderr, render_stream.hooks_of(lib.plugin_root()))
    status = render_stream.HerdrStatus(args.issue, run_id, args.herdr_workspace, args.herdr_tab)

    def show(frame_line: str) -> None:
        """Render one stream line and mirror it to Herdr; a display failure never touches the run."""
        try:
            frame = renderer.feed(frame_line)
            if frame:
                status.observe(frame, renderer)
        except Exception as error:  # noqa: BLE001 - display only
            print(f"render error: {error}", file=sys.stderr)

    usage = {"peak_context_tokens": 0, "compaction_alert": False, "input_tokens": 0, "cache_write_tokens": 0, "cache_read_tokens": 0,
             "output_tokens": 0}
    seen_messages: set[str] = set()
    armed = [True]

    def track(frame_line: str) -> None:
        """Sum token usage once per model message and alert once when the context crosses the compaction threshold."""
        try:
            frame = json.loads(frame_line)
            message = frame.get("message") if frame.get("type") == "assistant" else None
            if not isinstance(message, dict) or frame.get("parent_tool_use_id"):
                return  # a subagent (sidechain) frame is the subagent's own context and spend, not the parent's
            if message.get("id"):
                if message["id"] in seen_messages:
                    return  # a message streams as one frame per content block: count its usage once
                seen_messages.add(message["id"])
            u = message.get("usage") or {}
            usage["input_tokens"] += u.get("input_tokens", 0)
            usage["cache_write_tokens"] += u.get("cache_creation_input_tokens", 0)
            usage["cache_read_tokens"] += u.get("cache_read_input_tokens", 0)
            usage["output_tokens"] += u.get("output_tokens", 0)
            context = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
            usage["peak_context_tokens"] = max(usage["peak_context_tokens"], context)
            threshold = config["limits"]["compaction_alert_tokens"]
            if context < threshold:
                armed[0] = True  # the context fell (a compaction): the next crossing alerts again
            elif armed[0]:
                armed[0] = False
                usage["compaction_alert"] = True
                lib.emit(state, "run.compaction_alert", {"issue": args.issue, "run_id": run_id, "context_tokens": context})
                renderer.say(f"⚠ context {context} tokens: compact or hand off")
        except (ValueError, AttributeError, TypeError):
            pass  # accounting only; never touches the run

    def closing(record_state: str, text: str) -> None:
        renderer.say(f"■ record {record_state} {text}".rstrip())
        status.finish(record_state, renderer.step, renderer.turns)
    renderer.say(f"▶ {args.issue} run {run_id} → {stream}")
    with stream.open("w", encoding="utf-8") as out, stderr_log.open("w", encoding="utf-8") as err:
        try:
            proc = subprocess.Popen(claude_command(args, config, resume, mcp_config, previous), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=err, text=True, cwd=args.cwd or None, env=hook_env(args, config, state, config_path, base=base))
        except OSError as error:
            err.write(f"cannot start claude: {error}\n")
            renderer.say(f"✗ cannot start claude: {error}")
            proc = None
        if proc:
            def feed() -> None:
                try:
                    proc.stdin.write(prompt)
                    proc.stdin.close()
                except (BrokenPipeError, OSError):
                    pass
            threading.Thread(target=feed, daemon=True).start()

            def read() -> None:
                nonlocal last_beat
                for line in proc.stdout:
                    out.write(line)
                    out.flush()
                    lines.append(line)
                    if not args.profile:  # `--output-format json` has no init or live frames: the result is read once the run ends
                        init.feed(line)
                        track(line)
                        show(line)
                    if time.monotonic() - last_beat > 60:
                        lib.register(state, args.issue, state="running")
                        last_beat = time.monotonic()
            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            if not args.profile:
                init_wait = float(os.environ.get("PAI_HARNESS_INIT_TIMEOUT") or lib.INIT_TIMEOUT_SECONDS)
                deadline = time.monotonic() + init_wait
                while not init.done.is_set() and proc.poll() is None and time.monotonic() < deadline:
                    init.done.wait(0.05)
                if proc.poll() is not None:
                    reader.join(10)  # the stream is complete: the init verdict below is final
                if not init.done.is_set():
                    init.problems.append(f"no init event within {init_wait:g}s" if proc.poll() is None else "no init event before the run ended")
                if init.problems or init.mcp:
                    proc.kill()  # the exact child PID; never a pattern
                    proc.wait()
                    reader.join(10)
                    closing("failed", "self-check: " + init_reason(init.problems, init.mcp))
                    return fail_closed(args, state, started, stream, queue, machine, init.problems, run_id, init.mcp, previous)
            try:
                exit_code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.terminate()
                exit_code = proc.wait()
            reader.join(10)
    if args.profile:
        lines = json_frames(lines)
        for frame_line in lines:
            show(frame_line)
            result_usage(frame_line, usage)
    summary = lib.parse_stream(lines)
    verdict = lib.run_state(summary, exit_code, timed_out)
    finished = lib.stamp()
    this_run = {"run_id": run_id, "started": started, "finished": finished, "state": verdict["state"], "reason": verdict.get("reason"),
                "cost_usd": verdict.get("cost_usd"), "turns": verdict.get("turns"), **{k: usage[k] for k in (*SPENT_KEYS, "peak_context_tokens")}}
    # The record's cost_usd / turns / token fields are totals over every invocation of the issue; the last invocation's own numbers are in `runs`.
    record = {"issue": args.issue, "queue": queue, "machine": machine, "role": args.role, "started": started, "finished": finished,
              "stream": str(stream), "resumed": bool(resume), "run_id": run_id, "model": args.model or config["models"].get(args.role or "implementer", "sonnet"),
              "model_reported": init.model, "compaction_alert": usage["compaction_alert"], **verdict, **accumulate(previous, bool(resume), this_run)}
    if args.profile:  # what the verifier needs: the lane, the listed files, the worktree the start commit
        record.update({"profile": args.profile, "base": base, "cwd": str(Path(args.cwd or os.getcwd()).resolve()), **lane})
    lib.write_json(state_file, record)
    lib.register(state, args.issue, state=verdict["state"], session_id=verdict["session_id"])
    lib.emit(state, "run.finished", {k: record[k] for k in ("issue", "state", "reason", "exit_code", "session_id", "cost_usd", "turns")})
    closing(verdict["state"], f"exit={exit_code} {verdict['reason']}")
    return lib.exit_for(verdict["state"])


def mechanical_problem(args: argparse.Namespace, config: dict) -> str | None:
    """Check and complete the arguments of the mechanical profile (closed brief, role, model). Returns the usage error, else None."""
    if args.role not in (None, "mechanical"):
        return f"--profile mechanical runs the mechanical role, not {args.role}"
    if args.prompt or args.prompt_file or args.allowed_tools or args.resume_run:
        return "--profile mechanical takes a closed brief (--files, --instruction) only: no --prompt, --prompt-file, --allowed-tools or --resume"
    if not args.files or not (args.instruction or "").strip():
        return "--profile mechanical needs --files (the explicit file list) and --instruction (the exact instruction)"
    try:
        args.files = clean_files(args.files)
    except ValueError as error:
        return str(error)
    args.role = "mechanical"
    args.model = args.model or config["models"].get("mechanical", "haiku")
    if args.model not in MECHANICAL_MODELS:
        return f"--profile mechanical runs {' or '.join(MECHANICAL_MODELS)}, not {args.model}"
    args.prompt = closed_brief(args.instruction, args.files)
    return None


def result_usage(frame_line: str, usage: dict) -> None:
    """`--output-format json` has no per-message frames: the spend totals come from the result object's own `usage`. There is no per-turn peak."""
    try:
        frame = json.loads(frame_line)
        total = frame.get("usage") if frame.get("type") == "result" else None
        if isinstance(total, dict):
            for key, field in (("input_tokens", "input_tokens"), ("cache_write_tokens", "cache_creation_input_tokens"),
                               ("cache_read_tokens", "cache_read_input_tokens"), ("output_tokens", "output_tokens")):
                usage[key] += int(total.get(field) or 0)
    except (ValueError, AttributeError, TypeError):
        pass  # accounting only


def json_frames(lines: list[str]) -> list[str]:
    """`--output-format json` prints one result object (or, in some versions, an array of frames): return it as one JSON frame per line."""
    try:
        data = json.loads("".join(lines))
    except json.JSONDecodeError:
        return lines  # the bad text is counted by parse_stream and the run fails with "no result frame"
    return [json.dumps(item) for item in data] if isinstance(data, list) else [json.dumps(data)]


def herdr_json(*argv: str) -> dict:
    """Run a herdr command and return its JSON `result` (empty when herdr is absent, fails or prints something else)."""
    herdr = os.environ.get("PAI_HARNESS_HERDR", "herdr")
    try:
        done = run_process([herdr, *argv], capture_output=True, text=True, timeout=10)
        result = json.loads(done.stdout).get("result") if done.returncode == 0 else None
    except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
        return {}
    return result if isinstance(result, dict) else {}


def open_tab(args: argparse.Namespace) -> tuple[str | None, str | None, str | None]:
    """Create the run's own Herdr tab (never focused). Returns (pane, tab, workspace), or Nones when Herdr cannot."""
    workspace = os.environ.get("HERDR_WORKSPACE_ID")
    command = ["tab", "create", "--cwd", str(Path(args.cwd or os.getcwd()).resolve()), "--label", f"{args.issue}{render_stream.SEPARATOR}starting"]
    if workspace:
        command += ["--workspace", workspace]
    made = herdr_json(*command)
    pane = (made.get("root_pane") or {}).get("pane_id")
    tab = (made.get("tab") or {}).get("tab_id")
    return (pane, tab, (made.get("tab") or {}).get("workspace_id") or workspace) if pane else (None, None, None)


def in_pane(args: argparse.Namespace, state: Path, argv: list[str], tab: str | None, workspace: str | None, config_path: Path) -> int:
    """Run the inner launcher in a Herdr pane and wake on a unique marker; the state file it writes is the verdict."""
    herdr = os.environ.get("PAI_HARNESS_HERDR", "herdr")
    marker = f"HARNESS_{uuid.uuid4().hex[:12]}"
    inner_argv = ["--inner", *argv]
    if workspace:
        inner_argv += ["--herdr-workspace", workspace]
    if tab:
        inner_argv += ["--herdr-tab", tab]
    # A pane's shell is a fresh process: hand it this launcher's resolved config and state dir and every PAI_HARNESS_* setting.
    carried = {**{k: v for k, v in os.environ.items() if k.startswith("PAI_HARNESS_")}, "PAI_HARNESS_CONFIG": str(config_path), "PAI_HARNESS_STATE_DIR": str(state)}
    command = f"{shlex.join(['env', *[f'{k}={v}' for k, v in sorted(carried.items())], sys.executable, str(Path(__file__).resolve()), *inner_argv])}; echo {marker}_RC=$?"
    run_process([herdr, "pane", "run", args.pane, command], check=True)
    waited = run_process([herdr, "pane", "wait-output", args.pane, "--regex", f"{marker}_RC=[0-9]+", "--timeout", str(args.wait_ms)])
    record = lib.read_json(run_paths(state, args.issue)[1])
    if waited.returncode != 0 or not record or record.get("finished") is None:
        print(f"{args.issue}: the pane did not finish with a state file", file=sys.stderr)
        return lib.EXIT_FAILED
    return lib.exit_for(record["state"])


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="launch.sh", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("issue")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--pane", help="run in this Herdr pane (default inside Herdr: the launcher opens its own tab; outside Herdr: this terminal)")
    parser.add_argument("--model")
    parser.add_argument("--role")
    parser.add_argument("--cwd")
    parser.add_argument("--queue")
    parser.add_argument("--stream", help="Knowledge stream (default: the queue name, else the default [knowledge] target)")
    parser.add_argument("--allowed-tools", nargs="+")
    parser.add_argument("--profile", choices=("mechanical",), help="the mechanical lane: closed brief (--files, --instruction), Haiku, empty strict MCP, Read/Edit/Grep/Glob")
    parser.add_argument("--files", nargs="+", help="mechanical profile: the only files the run may change (literal relative paths)")
    parser.add_argument("--instruction", help="mechanical profile: the exact instruction")
    parser.add_argument("--config")
    parser.add_argument("--wait-ms", type=int, default=5400000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inner", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--herdr-workspace", help=argparse.SUPPRESS)
    parser.add_argument("--herdr-tab", help=argparse.SUPPRESS)
    parser.add_argument("--resume", dest="resume_run", action="store_true", help="resume the recorded session of ISSUE")
    parser.add_argument("--park", action="store_true", help="mark ISSUE parked")
    parser.add_argument("--status", action="store_true", help="print the recorded state of ISSUE")
    args = parser.parse_args(argv)
    config, config_path = lib.load_config(args.config)
    state = lib.state_dir(config)
    args.issue = lib.issue_id(args.issue, config)
    _, state_file, _ = run_paths(state, args.issue)

    if args.status:
        record = lib.read_json(state_file)
        if not record:
            print(f"{args.issue}: no run recorded", file=sys.stderr)
            return lib.EXIT_USAGE
        lib.show(record)
        return lib.exit_for(record["state"])
    if args.park:
        plan = {"action": "park", "issue": args.issue}
        if args.dry_run:
            lib.show({**plan, "dry_run": True})
            return 0
        lib.register(state, args.issue, state="parked")
        lib.emit(state, "run.parked", {"issue": args.issue})
        lib.show(plan)
        return 0
    if args.profile:
        problem = mechanical_problem(args, config)
        if problem:
            print(f"{args.issue}: {problem}", file=sys.stderr)
            return lib.EXIT_USAGE
    elif args.files or args.instruction:
        print("--files and --instruction belong to --profile mechanical", file=sys.stderr)
        return lib.EXIT_USAGE
    if not (args.prompt or args.prompt_file or args.resume_run):
        print("need --prompt or --prompt-file (or --resume)", file=sys.stderr)
        return lib.EXIT_USAGE
    role = args.role or "implementer"
    if args.stream and args.stream not in config["knowledge"].get("streams", {}):
        print(f"{args.issue}: --stream {args.stream!r} has no [knowledge.streams.{args.stream}] entry in the config", file=sys.stderr)
        return lib.EXIT_USAGE
    if role in lib.WRITING_ROLES and not lib.in_git_worktree(args.cwd):
        # Fail closed: Stop reads the changed paths from git, so a writing role outside a worktree would go unchecked.
        blocker = f"BLOCKER {args.issue}: writing role {role} must run inside a git worktree; {args.cwd or os.getcwd()} is not one"
        print(blocker, file=sys.stderr)
        if not args.dry_run:
            lib.emit(state, "run.blocked", {"issue": args.issue, "role": role, "blocker": blocker})
        return lib.EXIT_FAILED
    if args.profile and worktree_dirty(args.cwd):
        # Fail closed: the verifier discards a bad run by path, so the lane only starts from a clean tree (nothing of yours can be discarded).
        blocker = f"BLOCKER {args.issue}: the mechanical lane needs a clean worktree; commit or stash the changes in {args.cwd or os.getcwd()} first"
        print(blocker, file=sys.stderr)
        if not args.dry_run:
            lib.emit(state, "run.blocked", {"issue": args.issue, "role": role, "blocker": blocker})
        return lib.EXIT_FAILED
    if args.dry_run:
        previous = lib.read_json(state_file) or {}
        resume = previous.get("session_id") if args.resume_run else None
        lib.show({"dry_run": True, "issue": args.issue, "command": claude_command(args, config, resume, mcp_config_path(state, args.issue) if (config["pai"]["mcp_url"] or args.profile) else None, previous), "pane": args.pane,
                  "hook_env": {k: v for k, v in hook_env(args, config, state, config_path, write=False, base=launch_base(args, previous)).items() if k in HOOK_KEYS},
                  "stream": str(run_paths(state, args.issue)[0]), "state_file": str(state_file), "state_dir": str(state)})
        return 0
    if not args.inner:
        tab = workspace = None
        if args.pane:
            info = herdr_json("pane", "get", args.pane).get("pane") or {}
            tab, workspace = info.get("tab_id"), info.get("workspace_id")
        elif os.environ.get("HERDR_ENV") == "1":
            args.pane, tab, workspace = open_tab(args)
            if not args.pane:
                print(f"{args.issue}: could not open a Herdr tab; running in this terminal", file=sys.stderr)
        if args.pane:
            passed, skip = [], False
            for item in argv:
                if skip:
                    skip = False
                elif item == "--pane":
                    skip = True
                elif not item.startswith("--pane="):
                    passed.append(item)
            return in_pane(args, state, passed, tab, workspace, config_path)
    return inner(args, config, state, config_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
