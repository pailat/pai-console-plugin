#!/usr/bin/env bash
# pai.orchestration-wake. Event hook for pane.agent_status_changed and pane.exited. Self-contained: it ships
# inside this directory (and in the pai-console repository). Portable: bash 3.2, Linux and macOS, no GNU-only flags,
# local Herdr calls only through HERDR_BIN_PATH, no machine paths. Works for any agent kind (Claude, Codex): it reads Herdr's
# semantic agent_status, not the screen. NEVER fails: exit 0 always; every decision is logged to $HERDR_PLUGIN_STATE_DIR/wake.log.
# Config: environment first, then config.env in the plugin config dir (see config.env.example): PAI_WAKE_FALLBACK, PAI_WAKE_OUTBOX,
# PAI_WAKE_HOSTS, PAI_WAKE_MIN_INTERVAL (seconds between wakes to one target, default 60). Pane tokens (role parent requester issue name verdict wake_on_done) come from the live pane, then from the cache
# written by bin/pai-pane-meta in <plugin config dir>/panes/ (Herdr drops tokens on a server restart and before pane.exited).
set -u
H=${HERDR_BIN_PATH:-herdr}; S=${HERDR_PLUGIN_STATE_DIR:-$HOME/.herdr-pai-wake}; C=${HERDR_PLUGIN_CONFIG_DIR:-$S}
D=$(cd "$(dirname "$0")" && pwd); mkdir -p "$S" "$C/panes" 2>/dev/null
ts() { date +%Y-%m-%dT%H:%M:%S%z; }
log() { printf '%s %s\n' "$(ts)" "$*" >>"$S/wake.log" 2>/dev/null; }
# Config file supplies defaults; variables already set in the environment win.
for cf in "$S/config.env" "$C/config.env"; do
  [ -f "$cf" ] || continue
  while IFS= read -r line; do
    case "$line" in ''|'#'*) continue ;; esac
    k=${line%%=*}; v=${line#*=}; v=${v#\"}; v=${v%\"}
    case "$k" in PAI_WAKE_FALLBACK|PAI_WAKE_OUTBOX|PAI_WAKE_HOSTS|PAI_WAKE_MIN_INTERVAL) [ -n "$(eval "printf %s \"\${$k:-}\"")" ] || export "$k=$v" ;; esac
  done <"$cf"
done
FALLBACK=${PAI_WAKE_FALLBACK:-}
ev=${HERDR_PLUGIN_EVENT_JSON:-}; [ -n "$ev" ] || { log "no event json"; exit 0; }
# Real payload (0.9.0): {"event":"pane_agent_status_changed","data":{"type":..,"pane_id":..,"workspace_id":..,"agent_status":..,"agent":..}}
type=$(jq -r '.data.type // .event // .type // empty' <<<"$ev" | tr . _); pane=$(jq -r '.data.pane_id // .pane_id // empty' <<<"$ev")
st=$(jq -r '.data.agent_status // .agent_status // empty' <<<"$ev")
[ -n "$pane" ] || { log "no pane in event: ${ev:0:200}"; exit 0; }
# Tokens, per key: the live pane token first, then the file written by bin/pai-pane-meta (herdr drops tokens on a server restart
# and before pane.exited fires). A pane with neither is not ours and is ignored.
cache="$C/panes/$(printf %s "$pane" | tr -c 'A-Za-z0-9' _).json"
live=$("$H" pane get "$pane" 2>/dev/null | jq -c '.result.pane | {tokens: (.tokens // {}), label}' 2>/dev/null); [ -n "$live" ] || live='{}'
tok() { local v; v=$(jq -r --arg k "$1" '(.tokens // {})[$k] // empty' <<<"$live" 2>/dev/null); [ -n "$v" ] || v=$(jq -r --arg k "$1" '(.tokens // {})[$k] // empty' "$cache" 2>/dev/null); printf %s "$v"; }
role=$(tok role); issue=$(tok issue)
[ -n "$role$issue" ] || { log "$type $pane: no pai tokens, ignored"; exit 0; }
wod=$(tok wake_on_done); parent=$(tok parent); req=$(tok requester); issue=$(tok issue); name=$(tok name); verdict=$(tok verdict)
name=${name:-$(jq -r '.label // empty' <<<"$live")}; name=${name:-$pane}
# Fallback only for a pane with no cache file (launched without pai-pane-meta). A pane WITH a file but no parent/requester is a test or a misuse: no wake.
if [ ! -s "$cache" ]; then parent=${parent:-$FALLBACK}; req=${req:-$FALLBACK}; fi
FLOOR=${PAI_WAKE_MIN_INTERVAL:-60}; case "$FLOOR" in ''|*[!0-9]*) FLOOR=60 ;; esac
# Loop and flood guards: never wake the pane itself, and send each target at most one wake per $FLOOR seconds (a pair of panes that
# name each other as parent would otherwise prompt each other forever). Messages start with fixed text so a pane name that begins
# with a dash can never be read as a CLI option.
send() {
  [ -n "$1" ] || { log "$type $pane role=$role: no target (parent/requester unset), no wake"; return 0; }
  local out="" t k now last; OLDIFS=$IFS; IFS=,
  for t in $1; do
    t=$(printf %s "$t" | tr -d ' ')
    [ -n "$t" ] || continue
    [ "$t" = "$pane" ] || [ "$t" = "$name" ] && { log "$type $pane role=$role: target $t is the pane itself, skipped"; continue; }
    k="$S/sent-$(printf %s "$t" | tr -c 'A-Za-z0-9' _).ts"; now=$(date +%s); last=$(cat "$k" 2>/dev/null)
    case "$last" in ''|*[!0-9]*) last=0 ;; esac
    if [ "$FLOOR" -gt 0 ] && [ $((now - last)) -lt "$FLOOR" ]; then log "$type $pane role=$role: $t woken less than ${FLOOR}s ago, skipped"; continue; fi
    printf %s "$now" >"$k"; out=${out:+$out,}$t
  done
  IFS=$OLDIFS
  [ -n "$out" ] || return 0
  "$D/deliver.sh" "$out" "wake: $2"; log "$type $pane role=$role -> $out: $2"
}
case "$type" in
  pane_agent_status_changed)
    last="$S/last-$(basename "$cache" .json).txt"; prev=$(cat "$last" 2>/dev/null); printf %s "$st" >"$last"
    case "$st" in
      done|idle) # Only one-shot roles (token wake_on_done=1) wake on finish; leads/writers/orchestrators report up themselves .
                 [ "$wod" = 1 ] || { log "$type $pane $st: no wake_on_done, ignored"; exit 0; }
                 [ "$prev" = working ] || [ "$prev" = blocked ] || { log "$type $pane $st: not after working ($prev), ignored"; exit 0; }
                 send "$parent" "$name finished${issue:+ ($issue)}: read it" ;;
      blocked)   [ "$prev" = blocked ] && { log "$type $pane blocked again: not repeated"; exit 0; }
                 send "$parent" "$name BLOCKED${issue:+ ($issue)}: needs an answer"
                 "$H" notification show "wake: $name blocked" --body "${issue:-}" --sound request >/dev/null 2>&1 ;;
      *) log "$type $pane $st: ignored" ;;
    esac ;;
  pane_exited)
    send "$req" "$name exited${issue:+ ($issue)}${verdict:+: verdict $verdict}"; rm -f "$cache" "$S/last-$(basename "$cache" .json).txt" ;;
  *) log "unhandled $type" ;;
esac
exit 0
