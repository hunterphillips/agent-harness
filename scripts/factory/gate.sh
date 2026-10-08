#!/usr/bin/env bash
# After a review: judge the branch and record the verdict for finish.sh. When
# the stop is one the agent can check its way out of (review findings, a
# failed check) and a heal round is left, write .factory/feedback.md and ask
# for one. A heal round that changed nothing ends the loop.
# Usage: gate.sh <round>. Round 1 follows the attempts; round k+1 follows heal
# round k. Env: N REPO BRANCH MAX_HEALS GH_TOKEN REVIEW_JSON (may be empty).
# State written: GATE (clean|findings|checks_failed|no_ci|no_verdict|no_pr),
# GATE_DETAIL, GATE_HEAD, HEALS. Output: heal (true|false).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

round=$1
max_heals=${MAX_HEALS:-2}
head=$(git rev-parse HEAD)
pr=$(pr_for_branch "$BRANCH")

verdict() { # verdict <gate> <detail>: record and stop without a heal
  state_set GATE "$1"; state_set GATE_DETAIL "$2"; state_set GATE_HEAD "$head"
  output heal false
  log "gate round $round: $1${2:+ ($2)}"
  exit 0
}

heal() { # heal <gate> <detail> <feedback body>: record and ask for a heal round
  local k=$((round))
  if [ "$k" -gt "$max_heals" ]; then verdict "$1" "$2 (no heal rounds left)"; fi
  if [ "$round" -gt 1 ] && [ "$head" = "$(state_get GATE_HEAD)" ]; then
    verdict "$1" "$2 (heal round $((round - 1)) changed nothing)"
  fi
  state_set GATE "$1"; state_set GATE_DETAIL "$2"; state_set GATE_HEAD "$head"; state_set HEALS "$k"
  {
    echo "# Merge gate, round $round: $1"
    echo
    echo "The workflow stopped this branch short of the merge. Fix what is below on this"
    echo "branch, re-run the checks, push, and leave \`.factory/done\` in place. If a fix"
    echo "needs a decision the issue and its parent do not settle, write it to"
    echo "\`.factory/handoff\` instead. Heal round $k of $max_heals."
    echo
    printf '%s\n' "$3"
  } > "$FACTORY_DIR/feedback.md"
  output heal true
  log "gate round $round: $1; heal round $k requested"
  exit 0
}

[ -f "$FACTORY_DIR/done" ] || verdict no_verdict "the run did not report done"

# Commits the agent left unpushed reach the branch before anything is judged
# on the PR head. Pushed with the workflow token, so CI does not run on them;
# the no_ci verdict below catches that.
remote_head=$(git ls-remote origin "refs/heads/$BRANCH" | cut -f1)
if [ "$head" != "$remote_head" ]; then
  git push -q "$(remote_with_token)" "HEAD:refs/heads/$BRANCH" && log "pushed leftover commits"
fi
[ -n "$pr" ] || verdict no_pr "the run reported done but opened no pull request"

critical=$(jq -r '.critical // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
important=$(jq -r '.important // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
summary=$(jq -r '.summary // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
[ -n "$critical" ] || verdict no_verdict "the merge-gate review produced no verdict"

gh pr comment "$pr" --repo "$REPO" --body "**Merge-gate review (opus, round $round):** critical $critical, important $important. $summary" > /dev/null

if [ "$critical" -gt 0 ] || [ "$important" -gt 0 ]; then
  heal findings "the merge-gate review found $critical critical and $important important finding(s): $summary" \
    "## Review findings (critical $critical, important $important)

$summary

Fix every finding. If a finding reflects a scope choice the issue left open, the
issue's parent (for a part) or its stated end state decides it; say what you
decided in the PR body."
fi

allowed=$(state_get MERGE_ALLOWED)
[ "$allowed" = true ] || verdict clean "the review is clean; auto-merge is not allowed, so PR #$pr awaits human review"

if repo_has_pr_workflows; then
  head_sha=$(gh pr view "$pr" --repo "$REPO" --json headRefOid --jq .headRefOid)
  if [ "$(check_runs_on "$head_sha")" -eq 0 ]; then
    verdict no_ci "no CI ran on ${head_sha:0:7} (the last push came from the workflow token)"
  fi
  if ! gh pr checks "$pr" --repo "$REPO" --watch --fail-fast > /dev/null; then
    failed=$(gh pr checks "$pr" --repo "$REPO" --json name,state,link \
      --jq '[.[] | select(.state != "SUCCESS" and .state != "SKIPPED" and .state != "NEUTRAL")] | map("- \(.name): \(.state) \(.link)") | join("\n")')
    logs=""
    for run in $(gh run list --repo "$REPO" --commit "$head_sha" --status failure --limit 3 --json databaseId --jq '.[].databaseId'); do
      logs+=$(printf '\n### run %s\n```\n%s\n```\n' "$run" "$(gh run view "$run" --repo "$REPO" --log-failed 2> /dev/null | tail -c 12000)")
    done
    heal checks_failed "a check failed on PR #$pr" \
      "## Failed checks on ${head_sha:0:7}

$failed
$logs"
  fi
fi

verdict clean "review clean, checks green"
