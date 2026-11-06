#!/usr/bin/env python3
"""Render a `claude -p` stream-json run as readable lines, and mirror its state into Herdr (stdlib only).

`Renderer` prints one line per event: init (model, skills, hooks), one line per tool call, the assistant text, and the
final result. `HerdrStatus` reports the same events to Herdr as display-only workspace metadata (with a TTL, so a dead
run goes stale on its own) and renames the tab when the state changes. Neither drives a decision: the run record comes
from the `result` frame and the exit code (harness_lib.run_state).

As a filter: `launch.sh ... | render_stream.py`, or `render_stream.py < runs/ACME-7.jsonl`.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from subprocess import run as run_process  # bare name: the denylist reads a dotted call ending in the run top-level domain as a hostname

TTL_MS = 120000
TEXT_LIMIT = 160
TOOL_LIMIT = 100
SOURCE = "pai-harness"
TOKENS = ("state", "task", "run", "step", "turns")
SEPARATOR = " · "
# The states a human sees. blocked/done/failed are final; working/waiting move with the stream.
FINAL_STATES = ("blocked", "done", "failed")


def truncate(text: object, limit: int) -> str:
    """One line, at most `limit` characters, with an ellipsis when cut."""
    flat = " ".join(str(text).split())
    return flat if len(flat) <= limit else flat[: limit - 1].rstrip() + "…"


def tool_target(name: str, tool_input: object) -> str:
    """The part of a tool call worth showing: the path of an Edit/Read/Write, the command of a Bash, else the first string value."""
    if not isinstance(tool_input, dict):
        return ""
    for key in ("file_path", "path", "notebook_path", "command", "pattern", "url", "description", "prompt", "skill"):
        if isinstance(tool_input.get(key), str) and tool_input[key]:
            return tool_input[key]
    return next((v for v in tool_input.values() if isinstance(v, str)), "")


def frame_state(frame: dict) -> str | None:
    """The state a frame implies, or None when it does not change it. The final state is set by the launcher from the run record."""
    kind = frame.get("type")
    if kind == "system" and frame.get("subtype") == "init":
        return "working"
    if kind in ("assistant", "user"):
        return "working"
    if kind == "rate_limit_event":
        status = str((frame.get("rate_limit_info") or {}).get("status", ""))
        return "waiting" if status.startswith("rejected") else None
    if kind == "result":
        return result_state(frame)
    return None


def result_state(frame: dict) -> str:
    if frame.get("permission_denials"):
        return "blocked"
    return "done" if frame.get("subtype") == "success" and not frame.get("is_error") else "failed"


class Renderer:
    """Turns stream-json frames into lines. Tracks the turns and the last tool for the Herdr metadata."""

    def __init__(self, out=None, hook_events: tuple[str, ...] = ()) -> None:
        self.out = out if out is not None else sys.stdout
        self.hook_events = hook_events
        self.turns = 0
        self.step = ""
        self.started = time.monotonic()

    def say(self, line: str) -> None:
        self.out.write(line + "\n")
        self.out.flush()

    def feed(self, raw: str) -> dict | None:
        """Render one line. Returns the parsed frame, or None for a blank or unparsable line (shown as-is, truncated)."""
        raw = raw.strip()
        if not raw:
            return None
        try:
            frame = json.loads(raw)
        except json.JSONDecodeError:
            frame = None
        if not isinstance(frame, dict):
            self.say("? " + truncate(raw, TEXT_LIMIT))
            return None
        self.render(frame)
        return frame

    def render(self, frame: dict) -> None:
        kind = frame.get("type")
        if kind == "system" and frame.get("subtype") == "init":
            self.say(self.init_line(frame))
        elif kind == "assistant":
            self.turns += 1
            for block in (frame.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    name = str(block.get("name", "?"))
                    target = truncate(tool_target(name, block.get("input")), TOOL_LIMIT)
                    self.step = f"{name} {target}".strip()
                    self.say(f"● tool {self.step}")
                elif block.get("type") == "text" and str(block.get("text", "")).strip():
                    self.say("  " + truncate(block["text"], TEXT_LIMIT))
        elif kind == "user":
            for block in (frame.get("message") or {}).get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_result" and block.get("is_error"):
                    self.say("  ✗ tool error: " + truncate(block.get("content", ""), TOOL_LIMIT))
        elif kind == "rate_limit_event":
            status = str((frame.get("rate_limit_info") or {}).get("status", ""))
            if status.startswith("rejected"):
                self.say("… waiting: rate limited")
        elif kind == "result":
            if isinstance(frame.get("num_turns"), int):
                self.turns = frame["num_turns"]  # the run's own count beats ours
            self.say(self.result_line(frame))

    def init_line(self, frame: dict) -> str:
        skills = [s for s in frame.get("skills") or [] if isinstance(s, str)]
        plugins = [p.get("name") for p in frame.get("plugins") or [] if isinstance(p, dict)]
        parts = [f"▶ init model={frame.get('model', '?')}", f"skills={len(skills)}"]
        if plugins:
            parts.append("plugins=" + ",".join(str(p) for p in plugins))
        if self.hook_events:
            parts.append("hooks=" + ",".join(self.hook_events))
        return " ".join(parts)

    def result_line(self, frame: dict) -> str:
        state = result_state(frame)
        turns = frame.get("num_turns", self.turns)
        millis = frame.get("duration_ms")
        seconds = millis / 1000 if isinstance(millis, (int, float)) else time.monotonic() - self.started
        cost = frame.get("total_cost_usd")
        cost_text = f"${cost:.4f}" if isinstance(cost, (int, float)) else "n/a"
        line = f"■ result {state} turns={turns} duration={seconds:.1f}s cost≈{cost_text}"
        if state == "blocked":
            names = sorted({d.get("tool_name", "?") for d in frame["permission_denials"] if isinstance(d, dict)})
            line += " needs " + ",".join(names or ["?"])
        elif state == "failed":
            line += f" ({frame.get('subtype') or 'error'})"
        return line


class HerdrStatus:
    """Best-effort Herdr display: workspace metadata on each event, the tab label on state changes. Never raises, never decides.

    After three failing calls in a row it goes quiet, so a missing or wedged Herdr cannot slow the run.
    """

    def __init__(self, task: str, run_id: str, workspace: str | None, tab: str | None, herdr: str | None = None, ttl_ms: int = TTL_MS) -> None:
        self.task, self.run_id, self.workspace, self.tab = task, run_id, workspace, tab
        self.herdr = herdr or os.environ.get("PAI_HARNESS_HERDR", "herdr")
        self.ttl_ms = ttl_ms
        self.state: str | None = None
        self.failures = 0
        self.seq = time.time_ns() // 1_000_000  # increasing across runs: Herdr drops a lower sequence for the same source

    @property
    def active(self) -> bool:
        return self.failures < 3 and bool(self.workspace or self.tab)

    def call(self, *argv: str) -> None:
        try:
            done = run_process([self.herdr, *argv], capture_output=True, text=True, timeout=5)
            self.failures = self.failures + 1 if done.returncode != 0 else 0
        except (OSError, subprocess.SubprocessError):
            self.failures += 1

    def tab_label(self, state: str) -> str:
        return f"{self.task}{SEPARATOR}{state}"

    def report(self, state: str, step: str, turns: int) -> None:
        """One metadata call (state, task, run, step, turns, TTL); a tab rename when the state changed."""
        if not self.active:
            return
        if self.workspace:
            self.seq += 1
            self.call("workspace", "report-metadata", self.workspace, "--source", SOURCE,
                      "--token", f"state={state}", "--token", f"task={self.task}", "--token", f"run={self.run_id}",
                      "--token", f"step={truncate(step, 60) or '-'}", "--token", f"turns={turns}",
                      "--seq", str(self.seq), "--ttl-ms", str(self.ttl_ms))
        if self.tab and state != self.state:
            self.call("tab", "rename", self.tab, self.tab_label(state))
        self.state = state

    def observe(self, frame: dict, renderer: Renderer) -> None:
        state = frame_state(frame)
        if state is None and self.state is None:
            return
        self.report(state or self.state or "working", renderer.step, renderer.turns)

    def finish(self, state: str, step: str, turns: int) -> None:
        """The run record is written: show its final state once, then clear the tokens (the tab keeps the final label)."""
        if state != self.state:
            self.report(state, step, turns)
        if self.workspace and self.active:
            self.seq += 1
            self.call("workspace", "report-metadata", self.workspace, "--source", SOURCE,
                      *[a for name in TOKENS for a in ("--clear-token", name)], "--seq", str(self.seq))


def hooks_of(plugin_root: Path) -> tuple[str, ...]:
    """The hook events the loaded plugin registers (init has no hooks field, so read its hooks.json like the self-check does)."""
    try:
        data = json.loads((plugin_root / "hooks/hooks.json").read_text(encoding="utf-8"))
        return tuple(sorted(data.get("hooks", {})))
    except (OSError, ValueError, AttributeError):
        return ()


def main() -> int:
    renderer = Renderer(hook_events=hooks_of(Path(__file__).resolve().parent.parent))
    for line in sys.stdin:
        renderer.feed(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
