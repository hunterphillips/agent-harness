#!/usr/bin/env bash
# Start the implement job for an issue. Labels only show state: the factory's
# own label events start no workflows, so anything that must start a run calls
# this. Waits until the dispatched run has a live implement job; exits 1 if it
# never appears (a run that fails at startup is accepted by `gh workflow run`
# and only shows up afterwards). Usage: dispatch.sh <issue>. Env: REPO.
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

n=$1
title="factory #$n"
base=$(default_branch)
since=$(date -u -d '-2 minutes' +%Y-%m-%dT%H:%M:%SZ 2> /dev/null || date -u -v-2M +%Y-%m-%dT%H:%M:%SZ)
gh workflow run factory-caller.yml --repo "$REPO" --ref "$base" -f issue_number="$n"

run=""
for _ in $(seq 1 18); do
  sleep 10
  run=$(gh run list --repo "$REPO" --workflow factory-caller.yml --event workflow_dispatch --limit 10 \
    --json databaseId,displayTitle,createdAt \
    --jq "[.[] | select(.displayTitle == \"$title\" and .createdAt >= \"$since\")] | first | .databaseId // empty")
  [ -n "$run" ] || continue
  live=$(gh run view "$run" --repo "$REPO" --json jobs \
    --jq '[.jobs[] | select(.name | test("implement")) | select(.conclusion != "skipped")] | length')
  if [ "$live" -gt 0 ]; then
    log "dispatched #$n: run $run"
    output run_id "$run"
    exit 0
  fi
  [ "$(gh run view "$run" --repo "$REPO" --json status --jq .status)" = completed ] && break
done
log "dispatch of #$n did not start an implement job${run:+ (run $run)}"
output run_id "${run:-}"
exit 1
