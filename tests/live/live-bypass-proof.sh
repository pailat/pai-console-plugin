#!/usr/bin/env bash
# Opt-in live proof of the deny baseline against the real client. Never run by CI or `make check`.
# Usage: PAI_HARNESS_LIVE_CLAUDE=1 tests/live/live-bypass-proof.sh [--out FILE] [--claude claude] [--model haiku]
exec python3 "$(dirname "${BASH_SOURCE[0]}")/live_bypass_proof.py" "$@"
