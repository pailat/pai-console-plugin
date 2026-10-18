#!/usr/bin/env python3
"""Inspect, install or switch Pai plugins with native Codex commands (Python 3.11+)."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import tomllib

MARKETPLACE = "pai-console-plugin"
ENVIRONMENTS = {
    "staging": "https://mcp-edge-corp-staging.up.railway.app/mcp",
    "develop": "https://mcp-corp.paitesting.com/mcp",
    "production": "https://mcp-corp.pai.lat/mcp",
}
PLUGIN = re.compile(r"^pai-console-(staging|develop|production)@.+$")
DIAGNOSTICS = [
    "Status describes user configuration only; project or managed settings can override it.",
    "Hook trust and effective native approvals are not verified by this helper.",
    "Restart the client or open a fresh session after switching; authenticate the selected pai_console_<environment> connection manually.",
]


def get_path(data: dict, path: tuple[str, ...], default=None):
    value = data
    for part in path:
        if not isinstance(value, dict) or part not in value:
            return default
        value = value[part]
    return value


def key_path(text: str, table: bool = False) -> tuple[str, ...]:
    """Let the TOML parser decode quoted and dotted keys, rather than splitting on dots."""
    marker = "__pai_key_marker__"
    parsed = tomllib.loads(text + f"\n{marker} = true\n" if table else text + f' = "{marker}"\n')
    path = []
    while isinstance(parsed, dict):
        if table and marker in parsed:
            return tuple(path)
        if len(parsed) != 1:
            raise ValueError("Unsupported TOML key layout")
        part, parsed = next(iter(parsed.items()))
        path.append(part)
    return tuple(path)


def advance_quote(line: str, quote: str | None) -> str | None:
    """Track multiline strings so header-like text inside strings is never edited."""
    i = 0
    while i < len(line):
        if quote:
            if quote.startswith('"') and line[i] == "\\":
                i += 2
            elif line.startswith(quote, i):
                length = len(quote)
                if length == 3:
                    while i + length < len(line) and line[i + length] == quote[0]:
                        length += 1
                i += length
                quote = None
            else:
                i += 1
        elif line[i] == "#":
            break
        elif line[i] in "\"'":
            quote = line[i] * (3 if line.startswith(line[i] * 3, i) else 1)
            i += len(quote)
        else:
            i += 1
    return quote


def toml_key(value: str) -> str:
    return value if re.fullmatch(r"[A-Za-z0-9_-]+", value) else json.dumps(value)


def update_toml(text: str, updates: dict[tuple[str, ...], object]) -> str:
    """Surgically change owned scalar keys; preserve all other bytes and comments.

    Unusual inline definitions of owned tables fail before mutation. Unrelated
    inline tables, arrays, strings and comments are retained verbatim.
    """
    original = tomllib.loads(text)
    lines = text.splitlines(keepends=True)
    tables: dict[tuple[str, ...], tuple[int, int]] = {}
    assignments: dict[tuple[str, ...], tuple[int, re.Match]] = {}
    current: tuple[str, ...] = ()
    start = 0
    quote = None
    atom = r'[A-Za-z0-9_-]+|"(?:[^"\\]|\\.)*"|\x27[^\x27]*\x27'
    assignment = re.compile(r"^(\s*(?:" + atom + r")(?:\s*\.\s*(?:" + atom + r"))*\s*=\s*)(.*?)(\r?\n)?$")
    for index, line in enumerate(lines):
        if quote is None:
            array_header = re.match(r"^\s*\[\[.*\]\]\s*(?:#.*)?$", line.rstrip("\r\n"))
            header = re.match(r"^\s*\[(?!\[).*\]\s*(?:#.*)?$", line.rstrip("\r\n"))
            if array_header:
                tables[current] = (start, index)
                current = (f"__pai_array_table_{index}__",)
                start = index + 1
            elif header:
                tables[current] = (start, index)
                current = key_path(line.rstrip("\r\n"), table=True)
                start = index + 1
            else:
                match = assignment.match(line)
                if match:
                    raw_key = match[1].rsplit("=", 1)[0].strip()
                    assignments[current + key_path(raw_key)] = (index, match)
        quote = advance_quote(line, quote)
    tables[current] = (start, len(lines))
    additions: dict[tuple[str, ...], list[str]] = {}
    for path, value in updates.items():
        encoded = json.dumps(value, ensure_ascii=False)
        if path in assignments:
            index, match = assignments[path]
            old = match[2]
            # Owned values are only booleans or single-line strings. Keep inline comments.
            scalar = re.match(r'(?:true|false|"(?:[^"\\]|\\.)*"|\x27[^\x27]*\x27)(\s*(?:#.*)?)$', old)
            if not scalar:
                raise ValueError(f"Unsupported owned TOML value: {'.'.join(path)}")
            lines[index] = match[1] + encoded + scalar[1] + (match[3] or "")
        else:
            sentinel = object()
            if get_path(original, path, sentinel) is not sentinel:
                raise ValueError(f"Owned TOML key requires an explicit scalar assignment: {'.'.join(path)}")
            additions.setdefault(path[:-1], []).append(f"{toml_key(path[-1])} = {encoded}\n")
    # Insert into existing tables from the end, then append new tables.
    inserts = []
    appended = []
    for table, values in additions.items():
        if table in tables:
            inserts.append((tables[table][1], "".join(values)))
        else:
            header = ".".join(toml_key(part) for part in table)
            appended.append(f"\n[{header}]\n" + "".join(values))
    for index, value in sorted(inserts, reverse=True):
        if index and not lines[index - 1].endswith("\n"):
            value = "\n" + value
        lines.insert(index, value)
    result = "".join(lines)
    if appended:
        result += ("\n" if result and not result.endswith("\n") else "") + "".join(appended)
    parsed = tomllib.loads(result)
    for path, value in updates.items():
        if get_path(parsed, path) != value:
            raise ValueError(f"Could not safely update TOML key {path}")
    return result


def policy_updates(data: dict, environment: str, tools: dict) -> dict[tuple[str, ...], object]:
    updates = {}
    # Disable Pai environment identities even when installed from another marketplace.
    for identity in data.get("plugins", {}):
        if PLUGIN.fullmatch(identity):
            updates[("plugins", identity, "enabled")] = False
    for env in ENVIRONMENTS:
        identity = f"pai-console-{env}@{MARKETPLACE}"
        base = ("plugins", identity)
        updates[base + ("enabled",)] = env == environment
        server = base + ("mcp_servers", f"pai_console_{env}")
        updates[server + ("enabled",)] = True
        updates[server + ("default_tools_approval_mode",)] = "prompt"
        existing = get_path(data, server + ("tools",), {})
        for tool in sorted(tools.keys() | existing.keys()):
            annotation = tools.get(tool, {})
            annotation = annotation if isinstance(annotation, dict) else {}
            known = tool in tools and isinstance(annotation.get("readOnly"), bool)
            approve = known and (annotation["readOnly"] or env in ("staging", "develop"))
            updates[server + ("tools", tool, "approval_mode")] = "approve" if approve else "prompt"
    return updates


def atomic_write(path: Path, content: bytes, mode: int = 0o600) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing to replace symlinked configuration: {path}")
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.pai-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if path.is_symlink():
            raise ValueError(f"Refusing to replace symlinked configuration: {path}")
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def backup_config(path: Path, content: bytes) -> Path:
    fd, temporary = tempfile.mkstemp(prefix=".pai-backup-", dir=path.parent)
    os.close(fd)
    backup = Path(temporary).with_name(Path(temporary).name + ".toml")
    Path(temporary).unlink()
    atomic_write(backup, content)
    return backup


def read_config(home: Path) -> tuple[bytes, dict]:
    path = home / "config.toml"
    raw = path.read_bytes() if path.exists() else b""
    return raw, tomllib.loads(raw.decode())


def git_marketplace_root(home: Path, executable: str) -> Path:
    """Ask the native CLI for its configured Git snapshot; never guess cache paths."""
    help_text = run_cli(executable, ["plugin", "marketplace", "list", "--help"], home, home)
    if "--json" not in help_text:
        raise ValueError("Git snapshot discovery requires codex plugin marketplace list --json; pass --marketplace-root")
    listing = json.loads(run_cli(executable, ["plugin", "marketplace", "list", "--json"], home, home))
    matches = [entry for entry in listing.get("marketplaces", [])
               if entry.get("name") == MARKETPLACE
               and entry.get("marketplaceSource", {}).get("sourceType") == "git"]
    if len(matches) != 1 or not isinstance(matches[0].get("root"), str):
        raise ValueError("Configured Git snapshot could not be resolved; use codex plugin marketplace list --json and --marketplace-root")
    return Path(matches[0]["root"]).resolve()


def find_marketplace(data: dict, explicit: Path | None) -> Path:
    if explicit:
        root = explicit.expanduser().resolve()
    else:
        configured = data.get("marketplaces", {}).get(MARKETPLACE, {})
        if configured.get("source_type") == "local":
            root = Path(configured["source"]).expanduser().resolve()
        else:
            root = next((p for p in Path(__file__).resolve().parents
                         if (p / ".agents/plugins/marketplace.json").is_file()), None)
            if root is None:
                raise ValueError("Source marketplace not found; pass --marketplace-root /path/to/checkout")
    catalog = json.loads((root / ".agents/plugins/marketplace.json").read_text())
    if catalog.get("name") != MARKETPLACE:
        raise ValueError(f"Expected marketplace {MARKETPLACE}")
    entries = {entry["name"]: entry for entry in catalog["plugins"]}
    for env, url in ENVIRONMENTS.items():
        name = f"pai-console-{env}"
        source = entries[name]["source"]
        if source != {"source": "local", "path": f"./plugins/codex/{env}"}:
            raise ValueError(f"Unexpected package source for {name}")
        metadata = json.loads((root / source["path"] / "environment.json").read_text())
        if metadata != {"environment": env, "url": url, "plugin_name": name, "server_name": f"pai_console_{env}"}:
            raise ValueError(f"Unexpected environment metadata for {name}")
    return root


def run_cli(executable: str, arguments: list[str], home: Path, cwd: Path) -> str:
    result = subprocess.run([executable, *arguments], env={**os.environ, "CODEX_HOME": str(home)},
                            cwd=cwd, capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise ValueError(f"Codex command failed: {' '.join(arguments)}\n{result.stderr.strip()}")
    return result.stdout


def verify_cli(executable: str, home: Path, cwd: Path) -> None:
    for arguments, required in [
        (["plugin", "marketplace", "add", "--help"], ("<SOURCE>", "--json")),
        (["plugin", "add", "--help"], ("PLUGIN", "--json")),
    ]:
        help_text = run_cli(executable, arguments, home, cwd)
        if not all(token in help_text for token in required):
            raise ValueError("Installed Codex CLI does not support the required native plugin commands")


def status(home: Path) -> dict:
    _, data = read_config(home)
    active = [key for key, value in data.get("plugins", {}).items()
              if PLUGIN.fullmatch(key) and value.get("enabled") is True]
    return {"config": str(home / "config.toml"), "active": active,
            "exactly_one_environment": len(active) == 1, "diagnostics": DIAGNOSTICS}


def expected_native_change(before: bytes, after: bytes, command: list[str]) -> bool:
    """Recognize only the narrow config edits made by our native commands.

    Everything else, including unrelated comment/formatting changes, is a
    conflict. Unknown future CLI serialization fails conservatively with a backup.
    """
    if before == after:
        return True
    text = before.decode()
    data = tomllib.loads(text)
    if command[:3] == ["plugin", "marketplace", "add"]:
        updates = {("marketplaces", MARKETPLACE, "source_type"): "local",
                   ("marketplaces", MARKETPLACE, "source"): command[3]}
        expected = update_toml(text, updates)
        candidates = [expected]
        if get_path(data, ("marketplaces", MARKETPLACE)) is None:
            # toml_edit uses bare keys for a newly appended marketplace table.
            portable_header = '.'.join(json.dumps(p) for p in ("marketplaces", MARKETPLACE))
            native = expected.replace(f"[{portable_header}]", f"[marketplaces.{MARKETPLACE}]")
            native = native.replace('"source_type" = "local"', 'source_type = "local"')
            native = native.replace('"source" = ' + json.dumps(command[3]), 'source = ' + json.dumps(command[3]))
            candidates.append(native)
            block = (f"[marketplaces.{MARKETPLACE}]\nsource_type = \"local\"\nsource = "
                     + json.dumps(command[3]) + "\n")
            # toml_edit inserts beside existing marketplaces rather than at EOF.
            for insertion in (block, "\n" + block, block + "\n"):
                if after.decode().count(insertion) == 1 and after.decode().replace(insertion, "", 1) == text:
                    return True
        return after.decode() in candidates
    if command[:2] == ["plugin", "add"]:
        expected = update_toml(text, {("plugins", command[2], "enabled"): True})
        return after.decode() == expected
    return False


def configure(home: Path, environment: str, marketplace_root: Path | None = None,
              dry_run: bool = False, executable: str = "codex") -> dict:
    if environment not in ENVIRONMENTS:
        raise ValueError("Unknown Pai environment; no configuration was changed")
    if (home / "config.toml").is_symlink():
        raise ValueError("Symlinked config.toml is not supported by setup/switch; the link and its target were left unchanged. Manage this plugin's configuration through your dotfile source instead.")
    raw, data = read_config(home)
    configured_git = data.get("marketplaces", {}).get(MARKETPLACE, {}).get("source_type") == "git"
    if configured_git and marketplace_root is None:
        # Explicit roots are the fallback when native snapshot discovery is not
        # available. Callers must supply the current snapshot, not another clone.
        # Automatic discovery uses read-only help/list, never upgrade or auth.
        marketplace_root = git_marketplace_root(home, executable)
    root = find_marketplace(data, marketplace_root)
    package_inventory = root / "plugins/codex" / environment / "hooks/tools.json"
    inventory = json.loads(package_inventory.read_text())["tools"]
    source_inventory = root / "hooks/tools.json"
    if source_inventory.exists() and json.loads(source_inventory.read_text())["tools"] != inventory:
        raise ValueError("Package tool inventory is stale; regenerate packages before setup")
    updates = policy_updates(data, environment, inventory)
    update_toml(raw.decode(), updates)  # Reject unsupported owned layouts before native mutations.
    commands = [] if configured_git else [["plugin", "marketplace", "add", str(root), "--json"]]
    commands.append(["plugin", "add", f"pai-console-{environment}@{MARKETPLACE}", "--json"])
    result = {"environment": environment, "marketplace_root": str(root),
              "marketplace_source": "git" if configured_git else "local", "url": ENVIRONMENTS[environment], "dry_run": dry_run,
              "commands": [[executable, *command] for command in commands],
              "config": str(home / "config.toml"), "known_tools": len(inventory),
              "policy": "Known reads approve; nonproduction known writes approve; production writes and unknown tools prompt.",
              "diagnostics": DIAGNOSTICS}
    if dry_run:
        return result
    home.mkdir(parents=True, exist_ok=True)
    with (home / ".pai-plugin.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if read_config(home)[0] != raw:
            raise ValueError("Configuration changed while planning; retry setup")
        path = home / "config.toml"
        existed = path.exists()
        mode = stat.S_IMODE(path.stat().st_mode) if existed else 0o600
        verify_cli(executable, home, root)
        backup = backup_config(path, raw)
        result["backup"] = str(backup)
        last_written = None
        try:
            # Establish native policy before installation can enable any package.
            disabled = dict(updates)
            for key in disabled:
                if len(key) == 3 and key[-1] == "enabled":
                    disabled[key] = False
            last_written = update_toml(raw.decode(), disabled).encode()
            atomic_write(path, last_written, mode)
            observed = last_written
            for command in commands:
                if read_config(home)[0] != observed:
                    raise ValueError("Configuration changed between native commands")
                try:
                    run_cli(executable, command, home, root)
                finally:
                    current = path.read_bytes() if path.exists() else b""
                    if expected_native_change(observed, current, command):
                        # Native edits are recognized transaction writes too;
                        # a later ordinary failure may safely roll these back.
                        last_written = current
                    else:
                        raise ValueError("Configuration changed outside the expected native install edits")
                observed = current
            after_raw, after_data = read_config(home)
            updated = update_toml(after_raw.decode(), policy_updates(after_data, environment, inventory))
            if read_config(home)[0] != after_raw:
                raise ValueError("Configuration changed during installation; refusing to overwrite it")
            atomic_write(path, updated.encode(), mode)
        except BaseException as error:
            # Native commands and other writers can both change config.toml.
            # Roll back only bytes equal to a recognized helper/native write.
            # Any other snapshot must be preserved, never overwritten.
            try:
                current = path.read_bytes() if path.exists() else b""
            except OSError:
                current = None
            if last_written is None or current != last_written:
                raise ValueError(f"{error}. Configuration changed during installation; preserved current contents. Original backup: {backup}") from error
            if existed:
                atomic_write(path, raw, mode)
            else:
                path.unlink(missing_ok=True)
            raise
    result.update(status(home))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("status", "setup", "switch"))
    parser.add_argument("environment", nargs="?", choices=tuple(ENVIRONMENTS))
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser())
    parser.add_argument("--marketplace-root", type=Path)
    parser.add_argument("--codex", default="codex", help="Native Codex CLI executable")
    parser.add_argument("--dry-run", action="store_true", help="Print the plan without running Codex or changing files")
    args = parser.parse_args(argv)
    if args.command != "status" and not args.environment:
        parser.error("setup and switch require an explicit environment")
    if args.command == "status" and args.environment:
        parser.error("status does not accept an environment")
    try:
        home = args.codex_home.expanduser().resolve()
        result = status(home) if args.command == "status" else configure(
            home, args.environment, args.marketplace_root, args.dry_run, args.codex)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as error:
        print(f"Pai plugin helper: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
