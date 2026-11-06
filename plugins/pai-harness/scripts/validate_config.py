#!/usr/bin/env python3
"""Validate a .pai-harness.toml file. Usage: validate_config.py [path-or-repo-dir]. Exit 0 valid, 1 invalid. Stdlib only."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_config import CONFIG_NAME, ConfigError, find_config, load_file  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print("usage: validate_config.py [path-or-repo-dir]", file=sys.stderr)
        return 2
    target = Path(argv[0]) if argv else Path.cwd()
    try:
        path = target if target.is_file() else find_config(target)
        load_file(path)
    except ConfigError as error:
        print(f"invalid {CONFIG_NAME}: {error}", file=sys.stderr)
        return 1
    print(f"ok: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
