#!/usr/bin/env bash
# deliver.sh <targets> <message>: send one `herdr agent prompt` to each comma-separated target (bundled with the plugin; no
# machine-specific paths). A target is an agent name or pane id on this machine, or <alias>:<agent> for a machine in
# PAI_WAKE_MACHINES (space separated alias=label, where label is a saved Herdr machine label or id without spaces). A remote
# target is delivered with `herdr --machine <label> agent prompt <agent> <message>`: this script never runs ssh. The old
# PAI_WAKE_HOSTS / PAI_WAKE_SSH_OPTS / PAI_WAKE_REMOTE_PATH settings are deprecated and ignored: when any is set it logs and
# prints a loud message, and a target whose alias is only in PAI_WAKE_HOSTS is not delivered. Local calls go through
# HERDR_BIN_PATH. NEVER fails: exit 0; failures go to $HERDR_PLUGIN_STATE_DIR/wake.log. bash 3.2 and macOS safe.
H=${HERDR_BIN_PATH:-herdr}; S=${HERDR_PLUGIN_STATE_DIR:-${HOME}/.herdr-pai-wake}; mkdir -p "$S" 2>/dev/null
targets=${1:-}; msg=${2:-}; [ -n "$targets" ] && [ -n "$msg" ] || exit 0
ts() { date +%Y-%m-%dT%H:%M:%S%z; }
log() { printf '%s deliver %s\n' "$(ts)" "$*" >>"$S/wake.log" 2>/dev/null; }
to() { if command -v timeout >/dev/null 2>&1; then timeout "$@"; else shift; "$@"; fi; }
[ -n "${PAI_WAKE_OUTBOX:-}" ] && printf '%s %s %s\n' "$(ts)" "$targets" "$msg" >>"$PAI_WAKE_OUTBOX" 2>/dev/null
old=""; for v in PAI_WAKE_HOSTS PAI_WAKE_SSH_OPTS PAI_WAKE_REMOTE_PATH; do eval "[ -n \"\${$v:-}\" ]" && old="$old $v"; done
if [ -n "$old" ]; then
  m="DEPRECATED:$old no longer used. Delivery to another machine uses 'herdr --machine <label> agent prompt', never ssh. Replace PAI_WAKE_HOSTS with PAI_WAKE_MACHINES=\"alias=label ...\" and delete the others."
  log "$m"; printf 'pai.orchestration-wake: %s\n' "$m" >&2
fi
OLDIFS=$IFS; IFS=,; set -- $targets; IFS=$OLDIFS
for t in "$@"; do
  t=$(printf %s "$t" | tr -d ' '); [ -n "$t" ] || continue
  # Split alias:target at the FIRST colon only, and only when the prefix is a machine alias in PAI_WAKE_MACHINES; a pane id such as
  # w1:p2 (or far:w1:p2 -> alias far, target w1:p2) keeps its own colon.
  alias=""; label=""; who=$t; pre=${t%%:*}
  if [ "$pre" != "$t" ]; then
    for kv in ${PAI_WAKE_MACHINES:-}; do [ "${kv%%=*}" = "$pre" ] && { alias=$pre; label=${kv#*=}; who=${t#*:}; }; done
    if [ -z "$alias" ]; then for kv in ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "$pre" ] && { log "target $t uses a PAI_WAKE_HOSTS alias: not delivered (no ssh); define $pre in PAI_WAKE_MACHINES"; continue 2; }; done; fi
  fi
  case "$who" in *[!A-Za-z0-9_:-]*|"") log "bad target $t"; continue ;; esac
  if [ -z "$alias" ]; then
    to 20 "$H" agent prompt "$who" "$msg" >/dev/null 2>&1 </dev/null || log "failed $t"
  else
    case "$label" in *[!A-Za-z0-9_.-]*|"") log "invalid machine label for alias $alias, $t not delivered"; continue ;; esac
    to 30 "$H" --machine "$label" agent prompt "$who" "$msg" >/dev/null 2>&1 </dev/null || log "failed $t (machine $label)"
  fi
done
exit 0
