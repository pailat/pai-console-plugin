#!/usr/bin/env bash
# Thin entry point; the logic is in cost_report.py (stdlib only). Run with --help.
exec python3 "$(dirname "${BASH_SOURCE[0]}")/cost_report.py" "$@"
