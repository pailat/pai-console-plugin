#!/usr/bin/env python3
"""Print the resolved .pai-harness.toml (defaults applied) as JSON. Usage: load_config.py [path-or-repo-dir]. Stdlib only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness_config import CONFIG_NAME, ConfigError, find_config, load_file  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) > 1:
        print("usage: load_config.py [path-or-repo-dir]", file=sys.stderr)
        return 2
    target = Path(argv[0]) if argv else Path.cwd()
    try:
        path = target if target.is_file() else find_config(target)
        config = load_file(path)
    except ConfigError as error:
        print(f"invalid {CONFIG_NAME}: {error}", file=sys.stderr)
        return 1
    print(json.dumps(config, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
