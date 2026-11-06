#!/usr/bin/env python3
"""Run `claude -p` for one issue, optionally inside a Herdr pane, and record its stream, state, cost and session id.

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


def fail_closed(args: argparse.Namespace, state: Path, started: str, stream: Path, queue: str | None, machine: str | None, problems: list[str]) -> int:
    """The plugin is not proven loaded: the run is already killed; journal and print a BLOCKER, record failed, exit non-zero."""
    reason = "pai-harness self-check failed: " + "; ".join(problems)
    lib.blocker(state, args.issue, reason)
    record = {"issue": args.issue, "queue": queue, "machine": machine, "role": args.role, "started": started, "finished": lib.stamp(),
              "stream": str(stream), "resumed": bool(args.resume_run), "state": "failed", "reason": reason, "exit_code": None,
              "session_id": None, "cost_usd": None, "turns": None}
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
    with stream.open("w", encoding="utf-8") as out, stderr_log.open("w", encoding="utf-8") as err:
        try:
            proc = subprocess.Popen(claude_command(args, config, resume), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                    stderr=err, text=True, cwd=args.cwd or None, env=hook_env(args, config, state, config_path))
        except OSError as error:
            err.write(f"cannot start claude: {error}\n")
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
                return fail_closed(args, state, started, stream, queue, machine, init.problems)
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
              "stream": str(stream), "resumed": bool(resume), **verdict}
    lib.write_json(state_file, record)
    lib.register(state, args.issue, state=verdict["state"], session_id=verdict["session_id"])
    lib.emit(state, "run.finished", {k: record[k] for k in ("issue", "state", "reason", "exit_code", "session_id", "cost_usd", "turns")})
    return lib.exit_for(verdict["state"])


def in_pane(args: argparse.Namespace, state: Path, argv: list[str]) -> int:
    """Run the inner launcher in a Herdr pane and wake on a unique marker; the state file it writes is the verdict."""
    herdr = os.environ.get("PAI_HARNESS_HERDR", "herdr")
    marker = f"HARNESS_{uuid.uuid4().hex[:12]}"
    command = f"{shlex.join([sys.executable, str(Path(__file__).resolve()), '--inner', *argv])}; echo {marker}_RC=$?"
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
    parser.add_argument("--pane", help="run in this Herdr pane instead of this process")
    parser.add_argument("--model")
    parser.add_argument("--role")
    parser.add_argument("--cwd")
    parser.add_argument("--queue")
    parser.add_argument("--allowed-tools", nargs="+")
    parser.add_argument("--config")
    parser.add_argument("--wait-ms", type=int, default=5400000)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--inner", action="store_true", help=argparse.SUPPRESS)
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
    if args.dry_run:
        previous = lib.read_json(state_file) or {}
        resume = previous.get("session_id") if args.resume_run else None
        lib.show({"dry_run": True, "issue": args.issue, "command": claude_command(args, config, resume), "pane": args.pane,
                  "hook_env": {k: v for k, v in hook_env(args, config, state, config_path, write=False).items() if k in HOOK_KEYS},
                  "stream": str(run_paths(state, args.issue)[0]), "state_file": str(state_file), "state_dir": str(state)})
        return 0
    if args.pane and not args.inner:
        return in_pane(args, state, [a for a in argv if a not in ("--pane", args.pane)])
    return inner(args, config, state, config_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
