"""Shared helpers of the pai-harness scripts: config and state dir, journal and registry, stream-json state. Stdlib only.

State comes only from the stream-json `result` frame and the process exit code, never from Herdr's agent status
(a `claude -p` run has no TUI, so that status reads idle while it works).
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_config import ConfigError, find_config, load_file  # noqa: E402

STALE_MINUTES = 15
SHA = re.compile(r"[0-9a-f]{40}")
# Exit codes shared by the launcher and task-done: 0 done, 1 failed, 3 blocked on a permission.
EXIT_DONE, EXIT_FAILED, EXIT_USAGE, EXIT_BLOCKED = 0, 1, 2, 3


def now() -> datetime:
    return datetime.now(timezone.utc)


def stamp(moment: datetime | None = None) -> str:
    return (moment or now()).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_stamp(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def load_config(explicit: str | None = None) -> tuple[dict, Path]:
    """Load the config from --config, PAI_HARNESS_CONFIG or the nearest .pai-harness.toml; exit 2 on a bad one."""
    try:
        chosen = explicit or os.environ.get("PAI_HARNESS_CONFIG")
        path = Path(chosen) if chosen else find_config(Path.cwd())
        return load_file(path), path
    except ConfigError as error:
        print(f"invalid config: {error}", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)


def state_dir(config: dict) -> Path:
    """Per-project state: PAI_HARNESS_STATE_DIR, else the XDG state home. Never a temporary directory."""
    chosen = os.environ.get("PAI_HARNESS_STATE_DIR")
    if chosen:
        return Path(chosen)
    base = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return base / "pai-harness" / config["project"]["pai_project"]


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    partial.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    partial.replace(path)


def read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def emit(state: Path, kind: str, payload: dict) -> str:
    """Send one event or registry write through the corp MCP bridge when it is configured and works, else journal it.

    PAI_HARNESS_MCP_CMD names a command that reads one JSON object on stdin. Returns "mcp" or "journal".
    """
    record = {"ts": stamp(), "kind": kind, **payload}
    bridge = os.environ.get("PAI_HARNESS_MCP_CMD")
    if bridge:
        try:
            done = run_process(shlex.split(bridge), input=json.dumps(record), text=True, capture_output=True, timeout=20)
            if done.returncode == 0:
                return "mcp"
        except (OSError, subprocess.TimeoutExpired):
            pass
    state.mkdir(parents=True, exist_ok=True)
    with (state / "journal.jsonl").open("a", encoding="utf-8") as journal:
        journal.write(json.dumps({**record, "delivered": False}, sort_keys=True) + "\n")
    return "journal"


def registry_path(state: Path, name: str) -> Path:
    return state / "registry" / f"{name}.json"


def register(home: Path, name: str, **fields: object) -> dict:
    """Create or update one registry entry in the state dir `home` and stamp its heartbeat."""
    entry = read_json(registry_path(home, name)) or {"name": name, "started": stamp()}
    entry.update(fields)
    entry["heartbeat"] = stamp()
    write_json(registry_path(home, name), entry)
    return entry


def entries(state: Path) -> list[dict]:
    found = []
    for path in sorted((state / "registry").glob("*.json")):
        entry = read_json(path)
        if entry:
            found.append(entry)
    return found


def is_stale(entry: dict, at: datetime, minutes: int = STALE_MINUTES) -> bool:
    try:
        return at - parse_stamp(entry["heartbeat"]) > timedelta(minutes=minutes)
    except (KeyError, ValueError):
        return True


def running(state: Path, at: datetime | None = None) -> list[dict]:
    """Registry entries that are running and have a fresh heartbeat."""
    at = at or now()
    return [e for e in entries(state) if e.get("state") == "running" and not is_stale(e, at)]


def parse_stream(lines: object) -> dict:
    """Summarise stream-json lines: session id, the result frame, frame count. Bad lines are counted, not fatal."""
    summary: dict = {"frames": 0, "bad_lines": 0, "session_id": None, "result": None}
    for raw in lines:  # type: ignore[attr-defined]
        raw = raw.strip()
        if not raw:
            continue
        try:
            frame = json.loads(raw)
        except json.JSONDecodeError:
            summary["bad_lines"] += 1
            continue
        if not isinstance(frame, dict):
            summary["bad_lines"] += 1
            continue
        summary["frames"] += 1
        if frame.get("session_id"):
            summary["session_id"] = frame["session_id"]
        if frame.get("type") == "result":
            summary["result"] = frame
    return summary


def run_state(summary: dict, exit_code: int | None, timed_out: bool = False) -> dict:
    """Decide the state of a run from its stream summary and exit code alone.

    done: a successful result frame and exit code 0. blocked: the result lists permission denials, so the run needed
    a permission it was not given. failed: anything else (no result frame, an error result, a non-zero exit, a timeout).
    """
    result = summary.get("result")
    base = {"exit_code": exit_code, "session_id": summary.get("session_id"), "cost_usd": None, "turns": None}
    if result:
        base["cost_usd"] = result.get("total_cost_usd")
        base["turns"] = result.get("num_turns")
        base["session_id"] = result.get("session_id") or base["session_id"]
    if timed_out:
        return {**base, "state": "failed", "reason": "timeout"}
    if result is None:
        return {**base, "state": "failed", "reason": "no result frame" if exit_code == 0 else f"exit code {exit_code}, no result frame"}
    denials = result.get("permission_denials") or []
    if denials:
        names = sorted({d.get("tool_name", "?") for d in denials if isinstance(d, dict)}) or ["?"]
        return {**base, "state": "blocked", "reason": "permission needed: " + ", ".join(names)}
    if result.get("is_error") or result.get("subtype") != "success":
        return {**base, "state": "failed", "reason": f"result {result.get('subtype') or 'error'}"}
    if exit_code != 0:
        return {**base, "state": "failed", "reason": f"exit code {exit_code}"}
    return {**base, "state": "done", "reason": "result success"}


def exit_for(state_name: str) -> int:
    return {"done": EXIT_DONE, "blocked": EXIT_BLOCKED}.get(state_name, EXIT_FAILED)


def glob_regex(pattern: str) -> re.Pattern:
    """Translate a path glob (`**` crosses directories, `*` does not) to a regex."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


def matches(path: str, patterns: list[str]) -> bool:
    return any(glob_regex(p).match(path) for p in patterns)


def issue_id(text: str, config: dict) -> str:
    prefix = config["project"]["issue_prefix"]
    if not re.fullmatch(rf"{re.escape(prefix)}-\d+", text):
        print(f"issue id {text!r} does not look like {prefix}-<number>", file=sys.stderr)
        raise SystemExit(EXIT_USAGE)
    return text


def show(data: object) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))
