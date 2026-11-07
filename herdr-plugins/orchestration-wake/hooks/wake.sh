#!/usr/bin/env bash
# pai.orchestration-wake. Event hook for pane.agent_status_changed and pane.exited. Self-contained: it ships
# inside this directory (and in the pai-console repository). Portable: bash 3.2, Linux and macOS, no GNU-only flags,
# local Herdr calls only through HERDR_BIN_PATH, no machine paths. Works for any agent kind (Claude, Codex): it reads Herdr's
# semantic agent_status, not the screen. NEVER fails: exit 0 always; every decision is logged to $HERDR_PLUGIN_STATE_DIR/wake.log.
# Config: environment first, then config.env in the plugin config dir (see config.env.example): PAI_WAKE_FALLBACK, PAI_WAKE_OUTBOX,
# PAI_WAKE_MACHINES (alias=label of a saved Herdr machine, delivered with `herdr --machine`; never ssh). The old PAI_WAKE_HOSTS,
# PAI_WAKE_SSH_OPTS and PAI_WAKE_REMOTE_PATH are deprecated: still read so deliver.sh can print a loud message, never used.
# PAI_WAKE_MIN_INTERVAL (seconds between finish wakes from one pane to one target, default 60),
# PAI_WAKE_MAX_PER_HOUR (backstop on wakes of any kind per source pane and target, default 20). Pane tokens (role parent requester issue name verdict wake_on_done) come from the live pane, then from the cache
# written by bin/pai-pane-meta in <plugin config dir>/agents/<name>.json (older caches: panes/<id>.json) (Herdr drops tokens on a server restart and before pane.exited).
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
    case "$k" in PAI_WAKE_FALLBACK|PAI_WAKE_OUTBOX|PAI_WAKE_MACHINES|PAI_WAKE_HOSTS|PAI_WAKE_SSH_OPTS|PAI_WAKE_REMOTE_PATH|PAI_WAKE_MIN_INTERVAL|PAI_WAKE_MAX_PER_HOUR) [ -n "$(eval "printf %s \"\${$k:-}\"")" ] || export "$k=$v" ;; esac
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
# Cache: <config dir>/agents/<agent name>.json = {"pane":"<id>","tokens":{...}}, found by its "pane" field, so a relaunched agent rewrites its own
# file in place. The older pane-keyed file panes/<id>.json is the fallback until every agent has been re-tokened.
cache_file() { # echo the cache file of a pane id: agents/*.json by its "pane" field, else the older panes/<id>.json
  local f
  for f in "$C"/agents/*.json; do [ -f "$f" ] || continue; [ "$(jq -r '.pane // empty' "$f" 2>/dev/null)" = "$1" ] && { printf %s "$f"; return 0; }; done
  printf %s "$C/panes/$(printf %s "$1" | tr -c 'A-Za-z0-9' _).json"
}
cache=$(cache_file "$pane")
live=$("$H" pane get "$pane" 2>/dev/null | jq -c '.result.pane | {tokens: (.tokens // {}), label}' 2>/dev/null); [ -n "$live" ] || live='{}'
tok() { local v; v=$(jq -r --arg k "$1" '(.tokens // {})[$k] // empty' <<<"$live" 2>/dev/null); [ -n "$v" ] || v=$(jq -r --arg k "$1" '(.tokens // {})[$k] // empty' "$cache" 2>/dev/null); printf %s "$v"; }
role=$(tok role); issue=$(tok issue)
[ -n "$role$issue" ] || { log "$type $pane: no pai tokens, ignored"; exit 0; }
wod=$(tok wake_on_done); parent=$(tok parent); req=$(tok requester); issue=$(tok issue); name=$(tok name); verdict=$(tok verdict)
name=${name:-$(jq -r '.label // empty' <<<"$live")}; name=${name:-$pane}
# Fallback only for a pane with no cache file (launched without pai-pane-meta). A pane WITH a file but no parent/requester is a test or a misuse: no wake.
if [ ! -s "$cache" ]; then parent=${parent:-$FALLBACK}; req=${req:-$FALLBACK}; fi
FLOOR=${PAI_WAKE_MIN_INTERVAL:-60}; case "$FLOOR" in ''|*[!0-9]*) FLOOR=60 ;; esac
CAP=${PAI_WAKE_MAX_PER_HOUR:-20}; case "$CAP" in ''|*[!0-9]*) CAP=20 ;; esac
PK=$(printf %s "$pane" | tr -c 'A-Za-z0-9' _)
# Loop and flood guards. (1) Never wake the pane itself. (2) Never wake a target whose own parent is this pane: two panes that name
# each other as parent would otherwise prompt each other forever. (3) A "finished" wake is sent at most once per $FLOOR seconds per
# source pane and target, so a pane that flaps between working and done cannot spam; blocked and exited wakes are one-offs and are
# never held back by that interval, and different panes never suppress each other. (4) A backstop caps the wakes of any kind per
# source pane and target to $CAP per hour (0 = no cap). Messages start with fixed text so a pane name that begins with a dash can
# never be read as a CLI option.
parent_of() { # echo the parent token of a local target (agent name or pane id); empty when it cannot be resolved here
  local t=$1 id="" par kv
  case "$t" in *[!A-Za-z0-9_:-]*|"") return 0 ;; esac
  if [ "${t#*:}" != "$t" ]; then
    for kv in ${PAI_WAKE_MACHINES:-} ${PAI_WAKE_HOSTS:-}; do [ "${kv%%=*}" = "${t%%:*}" ] && return 0; done # alias:agent is a remote target
    id=$t
  else id=$("$H" agent get "$t" 2>/dev/null | jq -r '.result.agent.pane_id // empty' 2>/dev/null); fi
  [ -n "$id" ] || return 0
  par=$("$H" pane get "$id" 2>/dev/null | jq -r '.result.pane.tokens.parent // empty' 2>/dev/null)
  [ -n "$par" ] || par=$(jq -r '.tokens.parent // empty' "$(cache_file "$id")" 2>/dev/null)
  printf %s "$par"
}
send() { # send <finish|blocked|exit> <targets> <message>
  local kind=$1 out="" t tk now last tp n
  [ -n "$2" ] || { log "$type $pane role=$role: no target (parent/requester unset), no wake"; return 0; }
  for t in $(printf %s "$2" | tr ',' ' '); do
    [ -n "$t" ] || continue
    if [ "$t" = "$pane" ] || [ "$t" = "$name" ]; then log "$type $pane role=$role: target $t is the pane itself, skipped"; continue; fi
    tp=$(parent_of "$t")
    if [ -n "$tp" ] && { [ "$tp" = "$pane" ] || [ "$tp" = "$name" ]; }; then log "$type $pane role=$role: target $t has this pane as its parent, skipped (loop)"; continue; fi
    tk=$(printf %s "$t" | tr -c 'A-Za-z0-9' _); now=$(date +%s)
    if [ "$kind" = finish ] && [ "$FLOOR" -gt 0 ]; then
      last=$(cat "$S/sent-$PK-$tk-finish.ts" 2>/dev/null); case "$last" in ''|*[!0-9]*) last=0 ;; esac
      if [ $((now - last)) -lt "$FLOOR" ]; then log "$type $pane role=$role: $t woken for a finish less than ${FLOOR}s ago, skipped"; continue; fi
    fi
    if [ "$CAP" -gt 0 ]; then
      n=$(awk -v c=$((now - 3600)) '$1 > c' "$S/sent-$PK-$tk.log" 2>/dev/null | wc -l | tr -d ' ')
      if [ "${n:-0}" -ge "$CAP" ]; then log "$type $pane role=$role: $t already woken $n times this hour (cap $CAP), skipped"; continue; fi
      { awk -v c=$((now - 3600)) '$1 > c' "$S/sent-$PK-$tk.log" 2>/dev/null; echo "$now"; } >"$S/sent-$PK-$tk.log.new" && mv "$S/sent-$PK-$tk.log.new" "$S/sent-$PK-$tk.log"
    fi
    [ "$kind" = finish ] && printf %s "$now" >"$S/sent-$PK-$tk-finish.ts"
    out=${out:+$out,}$t
  done
  [ -n "$out" ] || return 0
  "$D/deliver.sh" "$out" "wake: $3"; log "$type $pane role=$role -> $out: $3"
}
case "$type" in
  pane_agent_status_changed)
    last="$S/last-$(basename "$cache" .json).txt"; prev=$(cat "$last" 2>/dev/null); printf %s "$st" >"$last"
    case "$st" in
      done|idle) # Only one-shot roles (token wake_on_done=1) wake on finish; leads/writers/orchestrators report up themselves .
                 [ "$wod" = 1 ] || { log "$type $pane $st: no wake_on_done, ignored"; exit 0; }
                 [ "$prev" = working ] || [ "$prev" = blocked ] || { log "$type $pane $st: not after working ($prev), ignored"; exit 0; }
                 send finish "$parent" "$name finished${issue:+ ($issue)}: read it" ;;
      blocked)   [ "$prev" = blocked ] && { log "$type $pane blocked again: not repeated"; exit 0; }
                 send blocked "$parent" "$name BLOCKED${issue:+ ($issue)}: needs an answer"
                 "$H" notification show "wake: $name blocked" --body "${issue:-}" --sound request >/dev/null 2>&1 ;;
      *) log "$type $pane $st: ignored" ;;
    esac ;;
  pane_exited)
    send exit "$req" "$name exited${issue:+ ($issue)}${verdict:+: verdict $verdict}"; rm -f "$cache" "$S/last-$(basename "$cache" .json).txt" "$S"/sent-"$PK"-* ;;
  *) log "unhandled $type" ;;
esac
exit 0
