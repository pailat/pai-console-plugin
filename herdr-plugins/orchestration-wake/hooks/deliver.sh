#!/usr/bin/env bash
# deliver.sh <targets> <message>: send one `herdr agent prompt` to each comma-separated target (bundled with the plugin; no
# machine-specific paths). A target is an agent name or pane id on this machine, or <alias>:<agent> for a host in PAI_WAKE_HOSTS
# (alias=ssh-host[:remote-shell], default shell bash). ssh runs with PAI_WAKE_SSH_OPTS (default "-o BatchMode=yes -o ConnectTimeout=8");
# PAI_WAKE_REMOTE_PATH (chars A-Za-z0-9_./:~-) is prefixed to PATH for the remote herdr call, and an invalid value is skipped and
# logged. Local calls go through HERDR_BIN_PATH. NEVER fails: exit 0; failures go to
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
  # w1:p2 (or host-a:w1:p2 -> alias host-a, target w1:p2) keeps its own colon.
  alias=""; who=$t; pre=${t%%:*}
  if [ "$pre" != "$t" ]; then for kv in ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "$pre" ] && { alias=$pre; who=${t#*:}; }; done; fi
  case "$who" in *[!A-Za-z0-9_:-]*|"") log "bad target $t"; continue ;; esac
  if [ -z "$alias" ]; then
    to 20 "$H" agent prompt "$who" "$msg" >/dev/null 2>&1 </dev/null || log "failed $t"
  else
    entry=""; for kv in ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "$alias" ] && entry=${kv#*=}; done
    [ -n "$entry" ] || { log "no host alias $alias for $t"; continue; }
    host=${entry%%:*}; sh=bash; case "$entry" in *:*) sh=${entry#*:} ;; esac
    rp=${PAI_WAKE_REMOTE_PATH:-}
    case "$rp" in *[!A-Za-z0-9_./:~-]*) log "invalid PAI_WAKE_REMOTE_PATH, ignored"; rp="" ;; esac
    cmd="${rp:+PATH=$rp:\$PATH }herdr agent prompt $who $(printf '%q' "$msg")"
    # shellcheck disable=SC2086 # the options are a word list on purpose
    to 30 ssh ${PAI_WAKE_SSH_OPTS:--o BatchMode=yes -o ConnectTimeout=8} "$host" "$sh -lc $(printf '%q' "$cmd")" >/dev/null 2>&1 </dev/null || log "failed $t"
  fi
done
exit 0
