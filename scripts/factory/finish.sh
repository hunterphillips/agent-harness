#!/usr/bin/env bash
# After the attempts and the review: leave the issue in exactly one visible
# state. Merged (owner work, clean review, green checks), split (parts waiting,
# parent on wait), or handed to a human with one mention naming the reason.
# Never leaves in-progress on an open issue.
# Env: N REPO OWNER BRANCH RUN_URL GH_TOKEN REVIEW_JSON (may be empty).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

attempts=$(state_get ATTEMPTS); attempts=${attempts:-0}
allowed=$(state_get MERGE_ALLOWED)
base=$(state_get BASE_BRANCH); base=${base:-$(default_branch)}
max=${MAX_ATTEMPTS:-4}

if [ "$(issue_state "$N")" != OPEN ]; then
  log "issue #$N is closed; nothing to finish"; exit 0
fi

# Work the agent committed but did not push (a cut-off attempt) still reaches
# the branch. Pushed with the workflow token, so CI does not run on it; that
# only matters on the merge path, which checks for check runs below.
if [ "$(git rev-parse --abbrev-ref HEAD)" = "$BRANCH" ]; then
  remote_head=$(git ls-remote origin "refs/heads/$BRANCH" | cut -f1)
  if [ "$(git rev-parse HEAD)" != "$remote_head" ]; then
    git push -q "$(remote_with_token)" "HEAD:refs/heads/$BRANCH" && log "pushed leftover commits"
  fi
fi

pr=$(pr_for_branch "$BRANCH")
ahead=$(gh api "repos/$REPO/compare/$base...$BRANCH" --jq .ahead_by 2> /dev/null || echo 0)
if [ -z "$pr" ] && [ "${ahead:-0}" -gt 0 ]; then
  pr=$(gh pr create --repo "$REPO" --draft --base "$base" --head "$BRANCH" \
    --title "$(issue_title "$N")" \
    --body "Closes #$N. Opened by the factory after the run ended; see the issue for its state. Run: $RUN_URL" | grep -o '[0-9]*$')
  log "opened draft PR #$pr"
fi

if [ -f "$FACTORY_DIR/split" ]; then
  parts=$(tr '\n' ' ' < "$FACTORY_DIR/split" | sed 's/ *$//' | sed 's/\([0-9][0-9]*\)/#\1/g')
  if [ "$allowed" != true ]; then
    hand_off "$N" "the work is too large for one run and auto-merge is not allowed for this issue, so it was not split (proposed parts: $parts)" "$pr"
    exit 0
  fi
  set_status "$N" wait
  comment "$N" "Split into parts, in order: $parts. Each part runs on its own and merges on its own; this issue closes when the last one merges."
  exit 0
fi

if [ -f "$FACTORY_DIR/handoff" ]; then
  hand_off "$N" "$(head -c 600 "$FACTORY_DIR/handoff")" "$pr"
  exit 0
fi

if [ ! -f "$FACTORY_DIR/done" ]; then
  if [ "$attempts" -ge "$max" ]; then why="all $max attempts ran out without finishing"
  elif [ "$attempts" -eq 0 ]; then why="no attempt ran"
  else why="attempt $attempts ended without adding any commits"; fi
  hand_off "$N" "$why" "$pr"
  exit 0
fi

# The agent says it finished. The workflow decides what that is worth.
[ -n "$pr" ] || { hand_off "$N" "the run reported done but opened no pull request"; exit 0; }

critical=$(jq -r '.critical // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
important=$(jq -r '.important // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
summary=$(jq -r '.summary // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
if [ -n "$critical" ]; then
  gh pr comment "$pr" --repo "$REPO" --body "**Merge-gate review (opus):** critical $critical, important $important. $summary" > /dev/null
fi

if [ "$allowed" != true ]; then
  hand_off "$N" "auto-merge is not allowed for this issue, so PR #$pr awaits your review" "$pr"
  exit 0
fi
if [ -z "$critical" ]; then
  hand_off "$N" "the merge-gate review produced no verdict" "$pr"; exit 0
fi
if [ "$critical" -gt 0 ] || [ "$important" -gt 0 ]; then
  hand_off "$N" "the merge-gate review found $critical critical and $important important finding(s): $summary" "$pr"
  exit 0
fi

head_sha=$(gh pr view "$pr" --repo "$REPO" --json headRefOid --jq .headRefOid)
if repo_has_pr_workflows; then
  if [ "$(check_runs_on "$head_sha")" -eq 0 ]; then
    hand_off "$N" "no CI ran on ${head_sha:0:7} (the last push came from the workflow token)" "$pr"; exit 0
  fi
  if ! gh pr checks "$pr" --repo "$REPO" --watch --fail-fast > /dev/null; then
    hand_off "$N" "a check failed on PR #$pr" "$pr"; exit 0
  fi
fi

gh pr ready "$pr" --repo "$REPO" > /dev/null
if ! gh pr merge "$pr" --repo "$REPO" --squash --delete-branch > /dev/null; then
  hand_off "$N" "the merge of PR #$pr was refused" "$pr"; exit 0
fi
set_status "$N" none
sleep 5
# No "merged" comment: the merge and the close already notify the author.
[ "$(issue_state "$N")" = OPEN ] && gh issue close "$N" --repo "$REPO" > /dev/null
log "merged PR #$pr for #$N"
