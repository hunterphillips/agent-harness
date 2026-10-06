#!/usr/bin/env bash
# Before the first attempt: decide whether this run should happen, settle the
# merge policy, claim or resume the issue branch, and set in-progress.
# Env: N REPO OWNER BRANCH AUTO_MERGE GH_TOKEN. Outputs: run, merge_line.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

# Keep the harness checkout and the factory's own files out of the agent's git view.
grep -qx '.harness/' .git/info/exclude 2> /dev/null || echo '.harness/' >> .git/info/exclude
grep -qx '.factory/' .git/info/exclude 2> /dev/null || echo '.factory/' >> .git/info/exclude

if [ "$(issue_state "$N")" != OPEN ]; then
  log "issue #$N is not open; nothing to do"; output run false; exit 0
fi
status=$(status_of "$N")
case "$status" in
  ready-for-agent|in-progress) ;;
  *) log "issue #$N is '$status', not ready-for-agent; nothing to do"; output run false; exit 0 ;;
esac

# Auto-merge only for work the owner asked for: the issue's author is the repo
# owner or the factory itself. A part is judged by its parent's author.
parent=$(part_parent "$N")
author=$(issue_author "${parent:-$N}")
allowed=false
if [ "$AUTO_MERGE" = true ]; then
  case "$author" in "$OWNER"|claude|app/claude|"claude[bot]") allowed=true ;; esac
fi
if [ "$allowed" = true ]; then
  line="AUTO-MERGE ALLOWED: the issue author ($author) is the owner or the factory; the workflow merges once the review and checks pass."
else
  line="AUTO-MERGE NOT ALLOWED (author: $author, auto_merge: $AUTO_MERGE): the PR stays a draft for human review. Do not split this issue."
fi

base=$(default_branch)
git fetch -q origin
if git ls-remote --exit-code --heads origin "$BRANCH" > /dev/null; then
  git checkout -q -B "$BRANCH" "origin/$BRANCH"
  mode=resume
else
  git checkout -q -b "$BRANCH" "origin/$base"
  git push -q "$(remote_with_token)" "HEAD:refs/heads/$BRANCH"
  mode=fresh
fi
set_status "$N" in-progress

state_set BASE "$(git rev-parse "origin/$base")"
state_set BASE_BRANCH "$base"
state_set LAST_HEAD "$(git rev-parse HEAD)"
state_set ATTEMPTS 0
state_set MERGE_ALLOWED "$allowed"
state_set MODE "$mode"
output run true
output merge_line "$line"
output mode "$mode"
log "preflight: #$N $mode on $BRANCH from $base; merge allowed: $allowed"
