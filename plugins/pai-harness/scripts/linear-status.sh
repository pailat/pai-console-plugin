#!/usr/bin/env bash
# Thin entry point; the logic is in linear_status.py (stdlib only). Run with --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/linear_status.py" "$@"
