#!/usr/bin/env bash
# Shared helpers for the factory's mechanical steps. Sourced by the other
# scripts in this directory; never run on its own.
#
# Expects: gh authenticated (GH_TOKEN), REPO (owner/name). Most helpers take an
# issue number. State and the agent's marker files live in .factory/ inside the
# target checkout, which preflight.sh excludes from git.
set -euo pipefail

STATUS_LABELS="needs-triage ready-for-agent ready-for-human needs-info wait in-progress"
FACTORY_DIR="${FACTORY_DIR:-.factory}"
STATE_FILE="$FACTORY_DIR/state"
mkdir -p "$FACTORY_DIR/transcripts"

log() { printf '%s\n' "$*" >&2; }

state_get() { if [ -f "$STATE_FILE" ]; then sed -n "s/^$1=//p" "$STATE_FILE" | tail -1; fi; }
state_set() {
  touch "$STATE_FILE"
  { grep -v "^$1=" "$STATE_FILE" || true; echo "$1=$2"; } > "$STATE_FILE.tmp"
  mv "$STATE_FILE.tmp" "$STATE_FILE"
}
output() { # output <key> <value>: a step output when run under Actions, else a log line
  if [ -n "${GITHUB_OUTPUT:-}" ]; then echo "$1=$2" >> "$GITHUB_OUTPUT"; fi
  log "output $1=$2"
}

default_branch() { gh repo view "$REPO" --json defaultBranchRef --jq .defaultBranchRef.name; }
remote_with_token() { echo "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"; }
# The branch's head on GitHub, read with the workflow token. After an agent step
# the checkout's `origin` carries the action's own token, which it revokes when
# the step ends, so `git ls-remote origin` fails on a runner that kept nothing
# else (seen on hub, 2026-10-13); the token URL works everywhere.
remote_head_of() { git ls-remote "$(remote_with_token)" "refs/heads/$1" | cut -f1; }

issue_state() { gh issue view "$1" --repo "$REPO" --json state --jq .state; }
issue_labels() { gh issue view "$1" --repo "$REPO" --json labels --jq '[.labels[].name] | join(",")'; }
issue_author() { gh issue view "$1" --repo "$REPO" --json author --jq .author.login; }
issue_title() { gh issue view "$1" --repo "$REPO" --json title --jq .title; }
has_label() { case ",$(issue_labels "$1")," in *",$2,"*) return 0 ;; *) return 1 ;; esac; }

# The one status label an issue carries, or "none".
status_of() {
  local labels l
  labels=",$(issue_labels "$1"),"
  for l in $STATUS_LABELS; do
    case "$labels" in *",$l,"*) echo "$l"; return ;; esac
  done
  echo none
}

# set_status <n> <label|none>: afterwards the issue carries exactly that status
# label (or none). The only function anywhere that changes a status label.
set_status() {
  local n=$1 want=$2 l remove=()
  for l in $STATUS_LABELS; do [ "$l" = "$want" ] || remove+=("$l"); done
  local args=(--remove-label "$(IFS=,; echo "${remove[*]}")")
  [ "$want" = none ] || args+=(--add-label "$want")
  gh issue edit "$n" --repo "$REPO" "${args[@]}" > /dev/null
  log "issue #$n status -> $want"
}

comment() { gh issue comment "$1" --repo "$REPO" --body "$2" > /dev/null; }
mention_owner() { comment "$1" "@${OWNER} $2"; }

# Parent issue number when <n> is a part of a split issue, else empty.
part_parent() {
  gh issue view "$1" --repo "$REPO" --json body --jq .body \
    | sed -n 's/.*<!-- factory-part-of: \([0-9]*\) -->.*/\1/p' | head -1
}

pr_for_branch() { # open PR whose head is <branch>, or empty
  gh pr list --repo "$REPO" --head "$1" --state open --json number --jq '.[0].number // empty'
}

# Paths of the workflows other than the factory's that run on pull requests,
# one per line. Empty when the repo has none. The trigger grep matches a
# `pull_request:` key, a `- pull_request` item, and an inline `on:` list or
# map; scripts/enroll-repo.sh's runner guard uses the same expression.
pr_workflow_paths() {
  local p
  for p in $(gh api "repos/$REPO/actions/workflows" --jq '.workflows[] | select(.state == "active") | .path'); do
    case "$p" in *factory-caller.yml|*factory.yml) continue ;; esac
    if gh api "repos/$REPO/contents/$p" -H 'Accept: application/vnd.github.raw' 2> /dev/null | grep -qE '^\s*(-\s*|on:.*[[:space:][,{])?pull_request'; then
      echo "$p"
    fi
  done
}
repo_has_pr_workflows() { [ -n "$(pr_workflow_paths)" ]; }

# Workflow runs on <sha> other than the factory's own (the monitor's run
# carries the failed run's head): "<id> <path> <conclusion>" per line. Needs
# the full sha; GitHub matches head_sha exactly.
ci_runs_on() {
  gh api "repos/$REPO/actions/runs?head_sha=$1&per_page=100" \
    --jq '.workflow_runs[] | select(.path | test("factory-caller\\.yml$|/factory\\.yml$") | not) | "\(.id) \(.path) \(.conclusion // "pending")"'
}

# Wait up to CI_RUN_WAIT seconds (default 120) for a run on <sha> from every
# pull-request workflow. GitHub writes a run within seconds of the push; check
# runs come later, when a runner takes the job, which is why the gate never
# counts those (a queued job read as "no CI ran" on scout #57, 2026-10-08).
# Prints whatever runs exist once every expected path has one or the wait is
# over: a workflow whose path or branch filter skipped this PR only costs the
# wait.
wait_for_ci_runs() {
  local sha=$1 waited=0 runs expected p missing
  expected=$(pr_workflow_paths)
  while :; do
    runs=$(ci_runs_on "$sha")
    missing=0
    for p in $expected; do grep -q " $p " <<< "$runs" || missing=1; done
    if { [ -n "$runs" ] && [ "$missing" -eq 0 ]; } || [ "$waited" -ge "${CI_RUN_WAIT:-120}" ]; then
      printf '%s\n' "$runs"; return
    fi
    sleep 10; waited=$((waited + 10))
  done
}

# ci_passed <run id>...: wait for every run; true when each concluded
# success, skipped, or neutral. Conclusions are read back rather than taken
# from `gh run watch`'s exit status, which treats skipped as a failure. No
# wait goes past CI_DEADLINE (a reading of $SECONDS, which the sourcing
# script shares): a run not completed by then counts as failed and sets
# CI_UNFINISHED=1, and one that never left `queued` also sets CI_QUEUED=1, so
# the caller can say what happened instead of being killed mid-wait. A queued
# run waits the whole window on purpose: the repo's checks runner serves main
# pushes and other pull requests too (a suite ahead of ours is the common
# case since 2026-10-20), and the shape that can never start (a workflow on
# the label this job holds) still ends inside the window.
CI_UNFINISHED=0
CI_QUEUED=0
# shellcheck disable=SC2034  # CI_UNFINISHED and CI_QUEUED are read by gate.sh after sourcing
ci_passed() {
  local id ok=true c st left
  for id in "$@"; do
    while :; do
      st=$(gh api "repos/$REPO/actions/runs/$id" --jq .status)
      [ "$st" = queued ] || break
      if [ -n "${CI_DEADLINE:-}" ] && [ "$SECONDS" -ge "$CI_DEADLINE" ]; then
        log "run $id still queued at the gate's deadline"
        ok=false; CI_UNFINISHED=1; CI_QUEUED=1; continue 2
      fi
      sleep 30
    done
    if [ -n "${CI_DEADLINE:-}" ]; then
      left=$((CI_DEADLINE - SECONDS)); [ "$left" -gt 0 ] || left=1
      timeout "$left" gh run watch "$id" --repo "$REPO" > /dev/null 2>&1 || true
    else
      gh run watch "$id" --repo "$REPO" > /dev/null 2>&1 || true
    fi
    if [ "$(gh api "repos/$REPO/actions/runs/$id" --jq .status)" != completed ]; then
      log "run $id still running at the gate's deadline"
      ok=false; CI_UNFINISHED=1; continue
    fi
    c=$(gh api "repos/$REPO/actions/runs/$id" --jq .conclusion)
    log "run $id concluded $c"
    case "$c" in success|skipped|neutral) ;; *) ok=false ;; esac
  done
  [ "$ok" = true ]
}

# run_seconds <id>: how long the run's latest attempt took, from GitHub's own
# timestamps (the suite may have started during the review before the gate).
run_seconds() {
  gh api "repos/$REPO/actions/runs/$1" --jq '((.updated_at | fromdateiso8601) - (.run_started_at | fromdateiso8601))'
}

# dismiss_held_runs <sha>: a push with the workflow token starts no checks,
# but GitHub can still record a pull-request run on the head and hold it for
# a person's approval, which reads on the PR as a stall nobody in the job can
# clear (personal-assistant #102, 2026-10-20). Cancel any such run on <sha>,
# best effort; the caller's comment says the push started no checks either way.
dismiss_held_runs() {
  local sha=$1 id
  sleep 20   # the held run appeared 13 s after the push on #102
  for id in $(gh api "repos/$REPO/actions/runs?head_sha=$sha&per_page=50" \
      --jq '.workflow_runs[] | select(.status == "action_required" or .conclusion == "action_required") | .id' 2> /dev/null); do
    if gh api -X POST "repos/$REPO/actions/runs/$id/cancel" > /dev/null 2>&1 \
       || gh api -X POST "repos/$REPO/actions/runs/$id/force-cancel" > /dev/null 2>&1; then
      log "cancelled run $id, which GitHub held for approval after the workflow-token push"
    else
      log "run $id is held for approval after the workflow-token push and could not be cancelled"
    fi
  done
}

# Hand the issue to a human: one status label, one mention, nothing else.
# HANDOFF_NOTE, when a script sets it, is one more sentence for the mention.
HANDOFF_NOTE=""
hand_off() { # hand_off <n> <reason> [pr]
  local n=$1 reason=$2 pr=${3:-}
  set_status "$n" ready-for-human
  mention_owner "$n" "The implement run stopped: ${reason}. ${pr:+PR #$pr is a draft and was not merged. }${HANDOFF_NOTE:+$HANDOFF_NOTE }A fresh \`ready-for-agent\` label resumes the branch. Run: ${RUN_URL:-}"
}
