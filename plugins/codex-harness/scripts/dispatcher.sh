#!/usr/bin/env bash
# Thin entry point; the logic is in dispatcher.py (stdlib only). Run with --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/dispatcher.py" "$@"
