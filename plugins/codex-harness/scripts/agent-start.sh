#!/usr/bin/env bash
# agent-start.sh <name> --role R --parent P --pane X [--issue I] [--kind K] -- <agent args>
# Starts an interactive agent with `herdr agent start` and tags its pane with the pai wake tokens (name, role, parent, issue,
# wake_on_done=1 for one-shot roles only) in one step. Fails closed: the tags are set in strict mode and VERIFIED afterwards (agent list, by pane id: name, role,
# parent, and wake_on_done for a one-shot role, must be present); a start that cannot be verified exits non-zero. Agent args pass through unchanged;
# permission policy is not decided here.
# wake_on_done=1 is set only for one-shot roles (implementer, reviewer, answerer, gate, verifier, mechanical): a lead, orchestrator or relay
# lives across turns and would wake its parent on every turn end. --wake / --no-wake override the role default.
# Exit: 0 started, tagged and ready; 1 failed (nothing runs untagged); 2 usage; 3 the agent RUNS and is tagged but herdr reported it
# not ready (agent_not_ready, e.g. blocked at a dialog): do not start it again, read it and wait for idle.
# Env: HERDR_BIN_PATH (herdr binary, default herdr), PAI_HARNESS_PANE_META (pai-pane-meta path override).
set -u
usage() { echo "usage: agent-start.sh <name> --role R --parent P --pane X [--issue I] [--kind K] [--wake|--no-wake] -- <agent args>" >&2; exit 2; }
fail() { echo "agent-start.sh: FAILED ${name:-?}: $1" >&2; exit 1; }
[ $# -ge 1 ] || usage
name=$1; shift
role=; parent=; pane=; issue=; kind=; wake=
while [ $# -gt 0 ]; do
  case $1 in
    --role) role=${2:-}; shift 2 || usage ;;
    --parent) parent=${2:-}; shift 2 || usage ;;
    --pane) pane=${2:-}; shift 2 || usage ;;
    --issue) issue=${2:-}; shift 2 || usage ;;
    --kind) kind=${2:-}; shift 2 || usage ;;
    --wake) wake=1; shift ;;
    --no-wake) wake=0; shift ;;
    --) shift; break ;;
    *) echo "agent-start.sh: unknown option $1" >&2; usage ;;
  esac
done
[ -n "$role" ] && [ -n "$parent" ] && [ -n "$pane" ] || { echo "agent-start.sh: --role, --parent and --pane are required" >&2; usage; }
# Validate before anything is tagged. Name rule is herdr's; the others are a safe charset (no spaces, newlines or control characters).
safe='^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$'
[[ $name =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || { echo "agent-start.sh: name '$name' must match [a-z][a-z0-9_-]{0,31}" >&2; usage; }
[[ $role =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || { echo "agent-start.sh: role '$role' must match [a-z][a-z0-9_-]{0,31}" >&2; usage; }
[[ $parent =~ $safe ]] || { echo "agent-start.sh: parent '$parent' must match $safe" >&2; usage; }
[[ $pane =~ $safe ]] || { echo "agent-start.sh: pane '$pane' must match $safe" >&2; usage; }
[ -z "$issue" ] || [[ $issue =~ $safe ]] || { echo "agent-start.sh: issue '$issue' must match $safe" >&2; usage; }
[ -z "$kind" ] || [[ $kind =~ ^[a-z][a-z0-9_-]{0,31}$ ]] || { echo "agent-start.sh: kind '$kind' is not a plain word" >&2; usage; }
command -v jq >/dev/null 2>&1 || fail "jq is required to verify the tags"
H=${HERDR_BIN_PATH:-herdr}
here=$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)
meta=${PAI_HARNESS_PANE_META:-$here/../herdr-plugins/orchestration-wake/bin/pai-pane-meta}
[ -x "$meta" ] || fail "pai-pane-meta not found at $meta"
start=("$H" agent start "$name" --pane "$pane")
[ -z "$kind" ] || start+=(--kind "$kind")
if [ -z "$wake" ]; then
  case $role in implementer|reviewer|answerer|gate|verifier|mechanical) wake=1 ;; *) wake=0 ;; esac
fi
tags=(name="$name" role="$role" parent="$parent")
[ "$wake" = 0 ] || tags+=(wake_on_done=1)
[ -z "$issue" ] || tags+=(issue="$issue")
# pai-pane-meta is best-effort by default; strict mode makes a failed tag exit non-zero.
tag() { PAI_PANE_META_STRICT=1 HERDR_BIN_PATH=$H "$meta" "$pane" "${tags[@]}"; }
# The tags really on the pane (by pane id, not name): prints the missing ones, empty output = all of name/role/parent/wake_on_done present.
missing() {
  "$H" agent list 2>/dev/null | jq -r --arg p "$pane" --arg n "$name" --arg r "$role" --arg a "$parent" --arg w "$wake" '
    [.result.agents[]? | select(.pane_id==$p)] as $m
    | if ($m|length)==0 then "agent not listed on pane"
      elif ($m|length)>1 then "several agents on the pane"
      else ($m[0].tokens // {}) as $t
        | [if $t.name!=$n then "name" else empty end, if $t.role!=$r then "role" else empty end,
           if $t.parent!=$a then "parent" else empty end, if ($w=="1" and $t.wake_on_done!="1") then "wake_on_done" else empty end] | join(",") end' 2>/dev/null || echo "agent list unreadable"
}
listed() { "$H" agent list 2>/dev/null | jq -e --arg p "$pane" --arg n "$name" '.result.agents[]? | select(.pane_id==$p and .name==$n)' >/dev/null 2>&1; }
# Tag first so the pane already carries its tokens when the agent comes up; tag again after the start in case herdr reset them.
tag || fail "could not tag pane $pane"
if [ $# -gt 0 ]; then start+=(-- "$@"); fi
"${start[@]}"; rc=$?
if [ $rc -ne 0 ]; then
  # `agent start` can exit non-zero (agent_not_ready) while the agent IS running. Never leave a live agent untagged.
  if listed; then
    tag && [ -z "$(missing)" ] || fail "the agent is running in $pane (herdr agent start exited $rc) but its tags could not be verified; tag it by hand with pai-pane-meta"
    echo "agent-start.sh: STARTED-NOT-READY $name in $pane (role=$role parent=$parent): herdr agent start exited $rc but the agent runs and is tagged; read it, wait for idle, do not start it again" >&2
    exit 3
  fi
  c=${HERDR_PLUGIN_CONFIG_DIR:-}; [ -n "$c" ] && rm -f "$c/agents/$name.json" 2>/dev/null
  fail "herdr agent start exited $rc and the agent is not running; the tags written before the start remain on pane $pane until it is reused"
fi
tag || fail "started, but tagging pane $pane failed; the parent would not be woken"
gap=$(missing)
[ -z "$gap" ] || fail "started, but pane $pane is missing tokens after tagging: $gap"
echo "agent-start.sh: started $name in $pane (role=$role parent=$parent)"
