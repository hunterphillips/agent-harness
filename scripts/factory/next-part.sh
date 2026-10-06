#!/usr/bin/env bash
# A split issue's parts run one at a time. After a run that split its issue or
# finished a part: start the next waiting part, and close the parent once the
# last part is closed. Env: N REPO OWNER RUN_URL GH_TOKEN.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

sleep 5 # let a merge's auto-close land
parent=$(part_parent "$N")
if [ -n "$parent" ]; then
  [ "$(issue_state "$N")" = CLOSED ] || { log "part #$N is still open; the chain waits"; exit 0; }
  [ "$(issue_state "$parent")" = OPEN ] || { log "parent #$parent is closed; the chain stops"; exit 0; }
else
  has_label "$N" wait || { log "#$N is not a split issue"; exit 0; }
  parent=$N
fi

marker="<!-- factory-part-of: $parent -->"
next=$(gh issue list --repo "$REPO" --state open --label wait --limit 100 --json number,body \
  --jq "[.[] | select(.body | contains(\"$marker\")) | .number] | sort | .[0] // empty")

if [ -n "$next" ]; then
  set_status "$next" ready-for-agent
  if "$(dirname "$0")/dispatch.sh" "$next"; then
    comment "$parent" "Started part #$next."
  else
    set_status "$next" ready-for-human
    mention_owner "$parent" "Part #$next did not start: the dispatched run never reached its implement job. Fix the cause, then relabel #$next \`ready-for-agent\`. Run: $RUN_URL"
  fi
elif [ "$parent" != "$N" ]; then
  open=$(gh issue list --repo "$REPO" --state open --limit 100 --json body \
    --jq "[.[] | select(.body | contains(\"$marker\"))] | length")
  if [ "$open" = 0 ]; then
    set_status "$parent" none
    gh issue close "$parent" --repo "$REPO" --comment "All parts merged." > /dev/null
  fi
fi
