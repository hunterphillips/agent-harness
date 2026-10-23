#!/usr/bin/env bash
# After a review: judge the branch and record the verdict for finish.sh. When
# the stop is one the agent can check its way out of (review findings, a
# failed check) and a heal round is left, write .factory/feedback.md and ask
# for one. A heal round that changed nothing ends the loop.
# Usage: gate.sh <round>. Round 1 follows the attempts; round k+1 follows heal
# round k. Env: N REPO BRANCH MAX_HEALS GH_TOKEN REVIEW_JSON (may be empty);
# optional CI_RUN_WAIT (default 120), the seconds lib.sh waits for CI runs
# to appear; GATE_MINUTES (default 30), the step's cap: the wait for CI,
# queued or running, stops three minutes short of it, and the re-run is
# skipped when it would not finish.
# State written: GATE (clean|findings|checks_failed|no_ci|no_verdict|no_pr),
# GATE_DETAIL, GATE_HEAD, HEALS, CI_RERUN (head whose failed jobs were re-run
# once), TOKEN_PUSH (head the gate pushed itself). Output: heal (true|false).
# GATE is also checks_unfinished when a run outlasted the window, still
# running or still queued behind other runs on the repo's checks runner.
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

round=$1
max_heals=${MAX_HEALS:-2}
window=$(( ${GATE_MINUTES:-30} * 60 ))   # the step's cap in seconds; $SECONDS counts from the script's start
export CI_DEADLINE=$(( window - 180 ))   # lib.sh stops watching here: three minutes for logs, feedback, and the verdict
head=$(git rev-parse HEAD)
pr=$(pr_for_branch "$BRANCH")

unfinished() { # unfinished <what>: the window closed on <what>, queued or running
  if [ "${CI_QUEUED:-0}" = 1 ]; then
    verdict checks_unfinished "$1 on ${head_sha:0:7} was still queued when the gate's ${GATE_MINUTES:-30}-minute window closed: nothing failed; the repo's checks runner was busy with other runs the whole time (or the workflow's runs-on label is not served while this job holds the factory runner)"
  fi
  verdict checks_unfinished "$1 on ${head_sha:0:7} was still running when the gate's ${GATE_MINUTES:-30}-minute window closed; this repo's suite needs a wider one (enroll-repo.sh --runner --gate-minutes N)"
}
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
# on the PR head. Pushed with the workflow token, which starts no CI; the CI
# section below turns that into a heal round that pushes once more.
remote_head=$(remote_head_of "$BRANCH")
if [ "$head" != "$remote_head" ]; then
  if git push -q "$(remote_with_token)" "HEAD:refs/heads/$BRANCH"; then
    log "pushed leftover commits"
    state_set TOKEN_PUSH "$head"   # only a push that landed can have started no CI
    dismiss_held_runs "$head"
  fi
fi
[ -n "$pr" ] || verdict no_pr "the run reported done but opened no pull request"

critical=$(jq -r '.critical // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
important=$(jq -r '.important // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
summary=$(jq -r '.summary // empty' <<< "${REVIEW_JSON:-}" 2> /dev/null || true)
[ -n "$critical" ] || verdict no_verdict "the merge-gate review produced no verdict"

pr_checks=false; repo_has_pr_workflows && pr_checks=true
note=""; [ "$pr_checks" = true ] || note=" No pull-request workflow in this repo; this review is the only check."
gh pr comment "$pr" --repo "$REPO" --body "**Merge-gate review (opus, round $round):** critical $critical, important $important. $summary$note" > /dev/null

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

if [ "$pr_checks" = true ]; then
  head_sha=$(gh pr view "$pr" --repo "$REPO" --json headRefOid --jq .headRefOid)
  if [ "$(state_get TOKEN_PUSH)" = "$head" ]; then
    heal no_ci "the last push came from the workflow token, which starts no CI" \
      "## No CI on ${head_sha:0:7}

The workflow pushed commits the attempt left unpushed, using its own token, and
GitHub starts no checks from that token. Make one empty commit
(\`git commit --allow-empty -m \"Run CI\"\`) and push it so the checks run on
this branch. Change nothing else; the review was clean."
  fi
  runs=$(wait_for_ci_runs "$head_sha")
  [ -n "$runs" ] || verdict no_ci "no CI ran on ${head_sha:0:7}"
  ids=$(cut -d' ' -f1 <<< "$runs")
  log "CI runs on ${head_sha:0:7}: $(tr '\n' ' ' <<< "$ids")"
  # shellcheck disable=SC2086
  if ! ci_passed $ids; then
    [ "${CI_UNFINISHED:-0}" = 1 ] && unfinished "the suite"
    # One re-run of the failed jobs first: a timing or runner flake passes the
    # second time, and a heal round cannot fix a flake. A real failure fails
    # again and goes to the agent with its log. A re-run takes about as long as the
    # run it repeats (the run's own timestamps, since the suite may have
    # started during the review), so when that much is not left before the
    # deadline, skip it: a heal round can still fix the failure.
    longest=0
    for run in $ids; do
      t=$(run_seconds "$run"); [ "$t" -gt "$longest" ] && longest=$t
    done
    rerun_note=""
    if [ $((SECONDS + longest + 60)) -gt "$CI_DEADLINE" ]; then
      rerun_note="The gate skipped its usual re-run of the failed jobs: the run took $((longest / 60)) minutes and the round's window of ${GATE_MINUTES:-30} could not hold another. If the failure looks like a flake, re-run that test yourself before changing code."
      log "skipping the re-run: the run took ${longest}s with ${SECONDS}s of the ${window}s window spent"
    elif [ "$(state_get CI_RERUN)" != "$head" ]; then
      state_set CI_RERUN "$head"
      for run in $ids; do
        gh run rerun "$run" --repo "$REPO" --failed > /dev/null 2>&1 && log "re-running failed jobs of run $run"
      done
      sleep 30
      # shellcheck disable=SC2086
      if ci_passed $ids; then
        verdict clean "review clean, checks green after one re-run"
      fi
      [ "${CI_UNFINISHED:-0}" = 1 ] && unfinished "the re-run"
    fi
    failed=""; logs=""
    for run in $ids; do
      line=$(gh api "repos/$REPO/actions/runs/$run" --jq '"- \(.name): \(.conclusion // .status) \(.html_url)"')
      case "$line" in *": success "*|*": skipped "*|*": neutral "*) continue ;; esac
      failed+="$line"$'\n'
      logs+=$(printf '\n### run %s\n```\n%s\n```\n' "$run" "$(gh run view "$run" --repo "$REPO" --log-failed 2> /dev/null | tail -c 12000)")
    done
    heal checks_failed "a check failed on PR #$pr" \
      "## Failed checks on ${head_sha:0:7}

${rerun_note:+$rerun_note

}$failed
$logs"
  fi
fi

verdict clean "review clean, checks green"
