#!/usr/bin/env python3
"""pai.turn-recorder: append pane events and stream-json frames to one JSONL file per turn.

Hook for pane.agent_status_changed and pane.exited. The journal is the future degraded-mode record of what an agent did.
Layout in $HERDR_PLUGIN_STATE_DIR:
  turns/<pane>-<turn>.jsonl   one file per turn, append-only, one JSON object per line
  pane-<pane>.json            recorder state: turn counter, open flag, last status, stream path and offset
  pane-<pane>.seen            idempotency keys already written (append-only)
A line is {"key","kind":"event"|"frame","ts","pane","name","turn","data"}. The key is unique per fact, so a redelivered
event or a re-read stream range adds no line. Event key: the event's own id or timestamp when the payload has one,
else pane, type, status, turn and the previous status (a status change to the status the pane already has is a redelivery).
Frame key: pane, stream path, byte offset and the line. Stream path: pane token "stream", else PAI_RECORDER_STREAM with
{name} and {pane}. Config: environment first, then config.env in the plugin config dir. NEVER fails: exit 0, decisions go to record.log.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path
from subprocess import SubprocessError, run as run_command

DEFAULT_MAX_BYTES = 8 * 1024 * 1024
CONFIG_KEYS = ("PAI_RECORDER_STREAM", "PAI_RECORDER_MAX_BYTES")
UNSAFE = re.compile(r"[^A-Za-z0-9_-]")


def safe(text: str) -> str:
    return UNSAFE.sub("_", text) or "_"


def digest(*parts: object) -> str:
    return hashlib.sha256("\x1f".join(str(p) for p in parts).encode()).hexdigest()[:32]


def now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


class Recorder:
    def __init__(self, env: dict[str, str]):
        self.env = env
        self.state_dir = Path(env.get("HERDR_PLUGIN_STATE_DIR") or Path.home() / ".herdr-pai-recorder")
        self.config_dir = Path(env.get("HERDR_PLUGIN_CONFIG_DIR") or self.state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "turns").mkdir(exist_ok=True)
        self.settings = self.load_settings()

    def log(self, message: str) -> None:
        try:
            with open(self.state_dir / "record.log", "a") as handle:
                handle.write(f"{now()} {message}\n")
        except OSError:
            pass

    def load_settings(self) -> dict[str, str]:
        settings: dict[str, str] = {}
        for base in (self.state_dir, self.config_dir):
            try:
                lines = (base / "config.env").read_text().splitlines()
            except OSError:
                continue
            for line in lines:
                key, sep, value = line.partition("=")
                if sep and key in CONFIG_KEYS and not line.startswith("#"):
                    settings[key] = value.strip().strip('"')
        for key in CONFIG_KEYS:
            if self.env.get(key):
                settings[key] = self.env[key]
        return settings

    def live_pane(self, pane: str) -> dict:
        herdr = self.env.get("HERDR_BIN_PATH", "herdr")
        try:
            out = run_command([herdr, "pane", "get", pane], capture_output=True, text=True, timeout=10, check=False).stdout
            data = json.loads(out)["result"]["pane"]
            return data if isinstance(data, dict) else {}
        except (OSError, SubprocessError, ValueError, KeyError, TypeError):
            return {}

    def load(self, path: Path, default):
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return default

    def save(self, path: Path, value: dict) -> None:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, sort_keys=True))
        os.replace(tmp, path)

    def stream_path(self, tokens: dict, name: str, pane_key: str, remembered: str) -> str:
        if tokens.get("stream"):
            return str(tokens["stream"])
        template = self.settings.get("PAI_RECORDER_STREAM", "")
        if template:
            return template.replace("{name}", safe(name)).replace("{pane}", pane_key)
        return remembered

    def handle(self, event: dict) -> None:
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        kind = str(data.get("type") or event.get("event") or event.get("type") or "").replace(".", "_")
        pane = str(data.get("pane_id") or event.get("pane_id") or "")
        status = str(data.get("agent_status") or event.get("agent_status") or "")
        if not pane or kind not in ("pane_agent_status_changed", "pane_exited"):
            self.log(f"ignored {kind or 'event'} pane={pane or '?'}")
            return
        pane_key = safe(pane)
        lock = open(self.state_dir / f"pane-{pane_key}.lock", "a")
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            self.record(event, data, kind, pane, pane_key, status)
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)
            lock.close()

    def record(self, event: dict, data: dict, kind: str, pane: str, pane_key: str, status: str) -> None:
        state_path = self.state_dir / f"pane-{pane_key}.json"
        seen_path = self.state_dir / f"pane-{pane_key}.seen"
        state = self.load(state_path, {})
        seen = set(seen_path.read_text().split()) if seen_path.exists() else set()
        live = self.live_pane(pane)
        tokens = live.get("tokens") if isinstance(live.get("tokens"), dict) else {}
        name = str(tokens.get("name") or live.get("label") or state.get("name") or pane_key)
        state["name"] = name
        state["stream"] = self.stream_path(tokens, name, pane_key, state.get("stream", ""))
        previous = state.get("status", "")
        exiting = kind == "pane_exited"
        # A turn opens when the pane starts working and closes on done, idle or exit; blocked stays inside the turn.
        if status == "working" and not state.get("open"):
            state.update(turn=int(state.get("turn", 0)) + 1, open=True)
        elif not state.get("open") and not state.get("turn"):
            state.update(turn=1, open=True)  # an event before any working: record it in turn 1 rather than lose it
        turn = int(state["turn"])
        own_id = next((str(data[k]) for k in ("id", "event_id", "seq", "ts", "timestamp") if data.get(k) not in (None, "")), "")
        if own_id:
            key = digest("event", pane, kind, status, own_id)
        elif exiting:
            key = digest("event", pane, kind, turn, "exit")
        else:
            key = digest("event", pane, kind, status, turn, previous)
        redelivery = not own_id and not exiting and status == previous  # a pane cannot change to the status it already has
        lines = []
        if key not in seen and not redelivery:
            lines.append({"key": key, "kind": "event", "ts": now(), "pane": pane, "name": name, "turn": turn, "data": data or event})
            seen.add(key)
        lines += self.frames(state, pane, name, turn, seen, final=exiting or status in ("done", "idle"))
        if lines:
            path = self.state_dir / "turns" / f"{pane_key}-{turn:04d}.jsonl"
            payload = "".join(json.dumps(line, sort_keys=True, separators=(",", ":")) + "\n" for line in lines)
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            try:
                os.write(fd, payload.encode())
            finally:
                os.close(fd)
            with open(seen_path, "a") as handle:
                handle.write("".join(line["key"] + "\n" for line in lines))
        state["status"] = status or previous
        if exiting or status in ("done", "idle"):
            state["open"] = False
        self.save(state_path, state)
        self.log(f"{kind} {pane} status={status or '-'} turn={turn} wrote={len(lines)}")

    def frames(self, state: dict, pane: str, name: str, turn: int, seen: set, final: bool) -> list[dict]:
        stream = state.get("stream", "")
        if not stream:
            return []
        try:
            limit = int(self.settings.get("PAI_RECORDER_MAX_BYTES", DEFAULT_MAX_BYTES))
        except ValueError:
            limit = DEFAULT_MAX_BYTES
        offset = int(state.get("offset", 0)) if state.get("offset_stream") == stream else 0
        try:
            size = os.path.getsize(stream)
            if size < offset:
                offset = 0  # truncated or rotated: read it again from the start; the keys keep it duplicate-free
            with open(stream, "rb") as handle:
                handle.seek(offset)
                chunk = handle.read(limit)
        except OSError:
            self.log(f"stream unreadable for {pane}: {stream}")
            return []
        end = chunk.rfind(b"\n") + 1
        if final and end < len(chunk):
            end = len(chunk)  # last turn event: a trailing line without a newline is complete now
        out = []
        position = offset
        for raw in chunk[:end].split(b"\n"):
            line = raw.decode("utf-8", "replace").strip()
            here = position
            position += len(raw) + 1
            if not line:
                continue
            key = digest("frame", pane, stream, here, line)
            if key in seen:
                continue
            try:
                frame = json.loads(line)
            except ValueError:
                frame = {"raw": line}
            out.append({"key": key, "kind": "frame", "ts": now(), "pane": pane, "name": name, "turn": turn, "data": frame})
            seen.add(key)
        state["offset"] = offset + end
        state["offset_stream"] = stream
        return out


def main() -> int:
    raw = os.environ.get("HERDR_PLUGIN_EVENT_JSON", "")
    try:
        recorder = Recorder(dict(os.environ))
    except OSError:
        return 0
    try:
        event = json.loads(raw) if raw else None
        if not isinstance(event, dict):
            recorder.log("no event json")
            return 0
        recorder.handle(event)
    except Exception as error:  # a hook must never fail the Herdr event
        recorder.log(f"error {type(error).__name__}: {error}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
