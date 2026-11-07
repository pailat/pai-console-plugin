#!/usr/bin/env bash
# Thin entry point; the logic is in verify_mechanical.py (stdlib only). Run with --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/verify_mechanical.py" "$@"
