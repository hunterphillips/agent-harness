#!/usr/bin/env bash
# After each attempt: keep its transcript, commit any uncommitted work locally
# (the workspace persists across attempts, so nothing is pushed here), and
# decide whether another attempt runs. Another attempt runs only when this one
# moved HEAD, left no marker file, and the issue is still open.
# Usage: checkpoint.sh <attempt number> [execution file]. Env: N REPO MAX_ATTEMPTS.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

k=$1
exec_file=${2:-}
max=${MAX_ATTEMPTS:-4}

if [ -n "$exec_file" ] && [ -f "$exec_file" ]; then
  cp "$exec_file" "$FACTORY_DIR/transcripts/attempt-$k.json"
fi

if [ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ] && [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -q -m "wip: end of attempt $k"
  log "committed leftover work from attempt $k"
fi

head=$(git rev-parse HEAD)
last=$(state_get LAST_HEAD)
marker=none
for m in "done" handoff split; do [ -f "$FACTORY_DIR/$m" ] && marker=$m; done

go=false
if [ "$marker" = none ] && [ "$head" != "$last" ] && [ "$k" -lt "$max" ] && [ "$(issue_state "$N")" = OPEN ]; then
  go=true
fi

state_set LAST_HEAD "$head"
state_set ATTEMPTS "$k"
output continue "$go"
log "attempt $k: head ${head:0:7} (was ${last:0:7}), marker $marker, continue=$go"
