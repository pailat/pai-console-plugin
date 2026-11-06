#!/usr/bin/env python3
"""Run `claude -p` for one issue, inside a Herdr pane, and record its stream, state, cost and session id.

The run is never hidden: with --pane it runs in that pane; inside Herdr (HERDR_ENV=1) without --pane the launcher opens
its own tab; outside Herdr it runs in the foreground of your terminal. In every case the stream is teed to the JSONL log
and to render_stream.py, which prints one readable line per event, and (in Herdr) mirrors the run into workspace
metadata (state, task, run, step, turns, 2-minute TTL) and the tab label. That display never decides anything.

State comes only from the stream-json `result` frame and the exit code (see harness_lib.run_state); the Herdr agent
status is never read. A run that needs a permission is not given one: it ends `blocked` (exit 3).

Usage: launch.sh ISSUE (--prompt TEXT | --prompt-file FILE) [--pane PANE] [--model M] [--role R] [--cwd DIR]
                 [--queue Q] [--allowed-tools T ...] [--config FILE] [--dry-run]
       launch.sh --resume ISSUE   continue a parked or blocked run by its recorded session id
       launch.sh --park ISSUE     mark a run parked (no process is touched)
       launch.sh --status ISSUE   print the recorded state
"""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness_lib as lib  # noqa: E402
import render_stream  # noqa: E402


HOOK_KEYS = ("PAI_HARNESS_ROLE", "PAI_HARNESS_AGENT", "PAI_HARNESS_ZONES", "PAI_HARNESS_BRIEF", "PAI_HARNESS_PUSH_WRAPPER")


def run_paths(state: Path, issue: str) -> tuple[Path, Path, Path]:
    runs = state / "runs"
    return runs / f"{issue}.jsonl", runs / f"{issue}.state.json", runs / f"{issue}.stderr.log"


def claude_command(args: argparse.Namespace, config: dict, resume: str | None) -> list[str]:
    model = args.model or config["models"].get(args.role or "implementer", "sonnet")
    command = [os.environ.get("PAI_HARNESS_CLAUDE", "claude"), "-p", "--output-format", "stream-json", "--verbose", "--model", model]
    if not lib.installed_plugin():
        command += ["--plugin-dir", str(lib.plugin_root())]  # every run loads the plugin, from the launcher's own location
    if resume:
        command += ["--resume", resume]
    if args.allowed_tools:
        command += ["--allowed-tools", *args.allowed_tools]
    return command


def hook_env(args: argparse.Namespace, config: dict, state: Path, config_path: Path, write: bool = True) -> dict[str, str]:
    """The environment that activates the hooks for this run: role, agent, zones, brief, push wrapper and Knowledge command."""
    role = args.role or "implementer"
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
    if args.prompt_file:
        env["PAI_HARNESS_BRIEF"] = str(Path(args.prompt_file).resolve())
    elif args.prompt:
        brief = state / "briefs" / f"{args.issue}.md"
        if write:
            brief.parent.mkdir(parents=True, exist_ok=True)
            brief.write_text(args.prompt, encoding="utf-8")
        env["PAI_HARNESS_BRIEF"] = str(brief)
    # PAI_HARNESS_KNOWLEDGE_CMD has no config key (it is site tooling); an operator's value passes through the inherited environment.
    return env


class InitCheck:
    """Watches the stream for the first `system/init` event and proves the pai-harness plugin from it (fail closed)."""

    def __init__(self, skills: list[str]) -> None:
        self.skills, self.problems, self.done = skills, [], threading.Event()

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
            self.problems = lib.init_problems(frame, self.skills)
            self.done.set()
        elif frame.get("type") in ("assistant", "user", "result"):
            self.problems = ["init event came after the first model frame"]
            self.done.set()


def fail_closed(args: argparse.Namespace, state: Path, started: str, stream: Path, queue: str | None, machine: str | None, problems: list[str],
                run_id: str | None = None) -> int:
    """The plugin is not proven loaded: the run is already killed; journal and print a BLOCKER, record failed, exit non-zero."""
    reason = "pai-harness self-check failed: " + "; ".join(problems)
    lib.blocker(state, args.issue, reason)
    record = {"issue": args.issue, "queue": queue, "machine": machine, "role": args.role, "started": started, "finished": lib.stamp(),
              "stream": str(stream), "resumed": bool(args.resume_run), "state": "failed", "reason": reason, "exit_code": None,
              "session_id": None, "cost_usd": None, "turns": None, "run_id": run_id}
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
    machine = config["queues"].get(queue or "", {}).get("machine")
    started = lib.stamp()
    stream.parent.mkdir(parents=True, exist_ok=True)
    lib.register(state, args.issue, state="running", queue=queue, machine=machine, role=args.role, stream=str(stream))
    lib.emit(state, "run.started", {"issue": args.issue, "queue": queue, "resume": bool(resume)})
    timeout = config["limits"]["turn_timeout_minutes"] * 60
    exit_code, timed_out, last_beat, lines = None, False, time.monotonic(), []
    init = InitCheck(lib.expected_skills(lib.plugin_root()))
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

    def closing(record_state: str, text: str) -> None:
        renderer.say(f"■ record {record_state} {text}".rstrip())
        status.finish(record_state, renderer.step, renderer.turns)
    renderer.say(f"▶ {args.issue} run {run_id} → {stream}")
    with stream.open("w", encoding="utf-8") as out, stderr_log.open("w", encoding="utf-8") as err:
        try:
            proc = subprocess.Popen(claude_command(args, config, resume), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=err, text=True, cwd=args.cwd or None, env=hook_env(args, config, state, config_path))
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
                    init.feed(line)
                    show(line)
                    if time.monotonic() - last_beat > 60:
                        lib.register(state, args.issue, state="running")
                        last_beat = time.monotonic()
            reader = threading.Thread(target=read, daemon=True)
            reader.start()
            init_wait = float(os.environ.get("PAI_HARNESS_INIT_TIMEOUT") or lib.INIT_TIMEOUT_SECONDS)
            deadline = time.monotonic() + init_wait
            while not init.done.is_set() and proc.poll() is None and time.monotonic() < deadline:
                init.done.wait(0.05)
            if proc.poll() is not None:
                reader.join(10)  # the stream is complete: the init verdict below is final
            if not init.done.is_set():
                init.problems.append(f"no init event within {init_wait:g}s" if proc.poll() is None else "no init event before the run ended")
            if init.problems:
                proc.kill()  # the exact child PID; never a pattern
                proc.wait()
                reader.join(10)
                closing("failed", "self-check: " + "; ".join(init.problems))
                return fail_closed(args, state, started, stream, queue, machine, init.problems, run_id)
            try:
                exit_code = proc.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.terminate()
                exit_code = proc.wait()
            reader.join(10)
    summary = lib.parse_stream(lines)
    verdict = lib.run_state(summary, exit_code, timed_out)
    record = {"issue": args.issue, "queue": queue, "machine": machine, "role": args.role, "started": started, "finished": lib.stamp(),
              "stream": str(stream), "resumed": bool(resume), "run_id": run_id, **verdict}
    lib.write_json(state_file, record)
    lib.register(state, args.issue, state=verdict["state"], session_id=verdict["session_id"])
    lib.emit(state, "run.finished", {k: record[k] for k in ("issue", "state", "reason", "exit_code", "session_id", "cost_usd", "turns")})
    closing(verdict["state"], f"exit={exit_code} {verdict['reason']}")
    return lib.exit_for(verdict["state"])


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
    parser.add_argument("--allowed-tools", nargs="+")
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
    if not (args.prompt or args.prompt_file or args.resume_run):
        print("need --prompt or --prompt-file (or --resume)", file=sys.stderr)
        return lib.EXIT_USAGE
    role = args.role or "implementer"
    if role in lib.WRITING_ROLES and not lib.in_git_worktree(args.cwd):
        # Fail closed: Stop reads the changed paths from git, so a writing role outside a worktree would go unchecked.
        blocker = f"BLOCKER {args.issue}: writing role {role} must run inside a git worktree; {args.cwd or os.getcwd()} is not one"
        print(blocker, file=sys.stderr)
        if not args.dry_run:
            lib.emit(state, "run.blocked", {"issue": args.issue, "role": role, "blocker": blocker})
        return lib.EXIT_FAILED
    if args.dry_run:
        previous = lib.read_json(state_file) or {}
        resume = previous.get("session_id") if args.resume_run else None
        lib.show({"dry_run": True, "issue": args.issue, "command": claude_command(args, config, resume), "pane": args.pane,
                  "hook_env": {k: v for k, v in hook_env(args, config, state, config_path, write=False).items() if k in HOOK_KEYS},
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
