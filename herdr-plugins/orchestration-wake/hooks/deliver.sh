#!/usr/bin/env bash
# deliver.sh <targets> <message>: send one `herdr agent prompt` to each comma-separated target (bundled with the plugin; no
# machine-specific paths). A target is an agent name or pane id on this machine, or <alias>:<agent> for a host in PAI_WAKE_HOSTS
# (alias=ssh-host[:remote-shell], default shell bash). Local calls go through HERDR_BIN_PATH. NEVER fails: exit 0; failures go to
# $HERDR_PLUGIN_STATE_DIR/wake.log. bash 3.2 and macOS safe.
H=${HERDR_BIN_PATH:-herdr}; S=${HERDR_PLUGIN_STATE_DIR:-${HOME}/.herdr-pai-wake}; mkdir -p "$S" 2>/dev/null
targets=${1:-}; msg=${2:-}; [ -n "$targets" ] && [ -n "$msg" ] || exit 0
ts() { date +%Y-%m-%dT%H:%M:%S%z; }
log() { printf '%s deliver %s\n' "$(ts)" "$*" >>"$S/wake.log" 2>/dev/null; }
to() { if command -v timeout >/dev/null 2>&1; then timeout "$@"; else shift; "$@"; fi; }
[ -n "${PAI_WAKE_OUTBOX:-}" ] && printf '%s %s %s\n' "$(ts)" "$targets" "$msg" >>"$PAI_WAKE_OUTBOX" 2>/dev/null
OLDIFS=$IFS; IFS=,; set -- $targets; IFS=$OLDIFS
for t in "$@"; do
  t=$(printf %s "$t" | tr -d ' '); [ -n "$t" ] || continue
  # Split alias:target at the FIRST colon only, and only when the prefix is a host alias in PAI_WAKE_HOSTS; a pane id such as
  # wAY:p24 (or desktop:wAY:p24 -> alias desktop, target wAY:p24) keeps its own colon.
  alias=""; who=$t; pre=${t%%:*}
  if [ "$pre" != "$t" ]; then for kv in ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "$pre" ] && { alias=$pre; who=${t#*:}; }; done; fi
  case "$who" in *[!A-Za-z0-9_:-]*|"") log "bad target $t"; continue ;; esac
  if [ -z "$alias" ]; then
    to 20 "$H" agent prompt "$who" "$msg" >/dev/null 2>&1 </dev/null || log "failed $t"
  else
    entry=""; for kv in ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "$alias" ] && entry=${kv#*=}; done
    [ -n "$entry" ] || { log "no host alias $alias for $t"; continue; }
    host=${entry%%:*}; sh=bash; case "$entry" in *:*) sh=${entry#*:} ;; esac
    cmd="herdr agent prompt $who $(printf '%q' "$msg")"
    to 30 ssh -o BatchMode=yes -o ConnectTimeout=8 "$host" "$sh -lc $(printf '%q' "$cmd")" >/dev/null 2>&1 </dev/null || log "failed $t"
  fi
done
exit 0
