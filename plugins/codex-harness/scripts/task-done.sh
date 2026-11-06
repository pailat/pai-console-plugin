#!/usr/bin/env bash
# Thin entry point; the logic is in task_done.py (stdlib only). Run with --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/task_done.py" "$@"
