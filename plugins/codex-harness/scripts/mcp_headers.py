#!/usr/bin/env python3
"""headersHelper for the Pai MCP: read the machine token file and print ONLY {"Authorization":"Bearer ..."} on stdout.

Claude Code runs this command to get the MCP request headers, so a headless `claude -p` can reach the Pai MCP without OAuth.
The token file is named by PAI_HARNESS_TOKEN_FILE, else by `[pai] token_file` of the config (--config, PAI_HARNESS_CONFIG or
the nearest .pai-harness.toml), else the default ~/.config/pai-harness/token. The value is never written anywhere but the one
stdout line: not to stderr, not to a log. Every refusal prints nothing on stdout, a short reason without the value on
stderr, and exits non-zero:

  missing file, not a regular file, a symlink, not mode 0600, not owned by the current user, empty, or not a single
  printable token (no whitespace or control characters, so the value cannot inject a header).

Usage: mcp_headers.sh [--config FILE]. Stdlib only.
"""
from __future__ import annotations

import json
import os
import re
import stat
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_config import DEFAULT_TOKEN_FILE, ConfigError, find_config, load_file  # noqa: E402

TOKEN = re.compile(rb"[\x21-\x7e]{1,4096}")  # printable ASCII, no whitespace: one header value
EXIT_REFUSED, EXIT_USAGE = 1, 2


class Refused(Exception):
    """The token file is not usable. The message never carries the token."""


def token_path(config_file: str | None) -> Path:
    """The token file: PAI_HARNESS_TOKEN_FILE, else the config's [pai] token_file, else the default. Only a path, never a value."""
    chosen = os.environ.get("PAI_HARNESS_TOKEN_FILE")
    if not chosen:
        explicit = config_file or os.environ.get("PAI_HARNESS_CONFIG")
        try:
            config = load_file(Path(explicit) if explicit else find_config(Path.cwd()))
            chosen = config["pai"]["token_file"]
        except ConfigError as error:
            if explicit:
                raise Refused(f"cannot read the config: {error}") from None
            chosen = DEFAULT_TOKEN_FILE  # no config anywhere: the documented default
    return Path(chosen).expanduser()


def read_token(path: Path) -> str:
    """Return the token in `path`, or raise Refused. The file is opened without following a symlink and checked on its descriptor."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except FileNotFoundError:
        raise Refused(f"token file {path} is missing") from None
    except OSError:
        raise Refused(f"token file {path} cannot be opened (a symlink, or no permission)") from None
    with os.fdopen(fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise Refused(f"token file {path} is not a regular file")
        if stat.S_IMODE(info.st_mode) != 0o600:
            raise Refused(f"token file {path} has mode {stat.S_IMODE(info.st_mode):04o}; it must be 0600")
        if info.st_uid != os.geteuid():
            raise Refused(f"token file {path} is not owned by the current user")
        data = handle.read(8192).strip()
    if not TOKEN.fullmatch(data):
        raise Refused(f"token file {path} is empty or is not a single printable token")
    return data.decode("ascii")


def header(token: str) -> str:
    return json.dumps({"Authorization": f"Bearer {token}"}, separators=(",", ":"))


def main(argv: list[str]) -> int:
    config_file = None
    if argv[:1] == ["--config"] and len(argv) == 2:
        config_file = argv[1]
    elif argv:
        print("usage: mcp_headers.sh [--config FILE]", file=sys.stderr)
        return EXIT_USAGE
    try:
        token = read_token(token_path(config_file))
    except Refused as error:
        print(f"mcp_headers: {error}", file=sys.stderr)
        return EXIT_REFUSED
    sys.stdout.write(header(token) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
