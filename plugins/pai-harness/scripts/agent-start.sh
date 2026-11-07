#!/usr/bin/env bash
# agent-start.sh <name> --role R --parent P --pane X [--issue I] -- <agent args>
# Starts an interactive agent with `herdr agent start` and tags its pane with the pai wake tokens (name, role, parent, issue,
# wake_on_done=1) in one step. Fails closed: if the start or the tagging fails, it reports the start as failed and exits non-zero,
# so no agent runs invisible to its parent. The agent args pass through unchanged; permission policy is not decided here.
# Env: HERDR_BIN_PATH (herdr binary, default herdr), PAI_HARNESS_PANE_META (pai-pane-meta path override).
set -u
usage() { echo "usage: agent-start.sh <name> --role R --parent P --pane X [--issue I] [--kind K] -- <agent args>" >&2; exit 2; }
[ $# -ge 1 ] || usage
name=$1; shift
role=; parent=; pane=; issue=; kind=
while [ $# -gt 0 ]; do
  case $1 in
    --role) role=${2:-}; shift 2 || usage ;;
    --parent) parent=${2:-}; shift 2 || usage ;;
    --pane) pane=${2:-}; shift 2 || usage ;;
    --issue) issue=${2:-}; shift 2 || usage ;;
    --kind) kind=${2:-}; shift 2 || usage ;;
    --) shift; break ;;
    *) echo "agent-start.sh: unknown option $1" >&2; usage ;;
  esac
done
[ -n "$role" ] && [ -n "$parent" ] && [ -n "$pane" ] || { echo "agent-start.sh: --role, --parent and --pane are required" >&2; usage; }
H=${HERDR_BIN_PATH:-herdr}
meta=${PAI_HARNESS_PANE_META:-$(dirname "${BASH_SOURCE[0]}")/../herdr-plugins/orchestration-wake/bin/pai-pane-meta}
[ -x "$meta" ] || { echo "agent-start.sh: FAILED $name: pai-pane-meta not found at $meta" >&2; exit 1; }
start=("$H" agent start "$name" --pane "$pane")
[ -z "$kind" ] || start+=(--kind "$kind")
# Tag first so the pane already carries its tokens when the agent comes up; tag again after the start in case herdr reset them.
tags=(name="$name" role="$role" parent="$parent" wake_on_done=1)
[ -z "$issue" ] || tags+=(issue="$issue")
tag() { HERDR_BIN_PATH=$H "$meta" "$pane" "${tags[@]}"; }
tag || { echo "agent-start.sh: FAILED $name: could not tag pane $pane" >&2; exit 1; }
if [ $# -gt 0 ]; then start+=(-- "$@"); fi
"${start[@]}" || { echo "agent-start.sh: FAILED $name: herdr agent start exited non-zero" >&2; exit 1; }
tag || { echo "agent-start.sh: FAILED $name: started, but tagging pane $pane failed; the parent would not be woken" >&2; exit 1; }
# pai-pane-meta never fails by design; verify the tokens are really on the pane.
got=$("$H" agent list 2>/dev/null | jq -r --arg n "$name" '.result.agents[]? | select(.name==$n) | .tokens.parent // empty' 2>/dev/null)
[ "$got" = "$parent" ] || { echo "agent-start.sh: FAILED $name: pane $pane has no parent token after tagging (agent list shows '${got}')" >&2; exit 1; }
echo "agent-start.sh: started $name in $pane (role=$role parent=$parent)"
