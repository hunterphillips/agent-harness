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

# True when some workflow other than the factory caller runs on pull requests,
# so a PR with no check runs means CI did not run rather than CI does not exist.
repo_has_pr_workflows() {
  local p
  for p in $(gh api "repos/$REPO/actions/workflows" --jq '.workflows[] | select(.state == "active") | .path'); do
    case "$p" in *factory-caller.yml|*factory.yml) continue ;; esac
    if gh api "repos/$REPO/contents/$p" -H 'Accept: application/vnd.github.raw' 2> /dev/null | grep -qE '^\s*pull_request'; then
      return 0
    fi
  done
  return 1
}

check_runs_on() { gh api "repos/$REPO/commits/$1/check-runs" --jq .total_count; }

# Hand the issue to a human: one status label, one mention, nothing else.
hand_off() { # hand_off <n> <reason> [pr]
  local n=$1 reason=$2 pr=${3:-}
  set_status "$n" ready-for-human
  mention_owner "$n" "The implement run stopped: ${reason}. ${pr:+PR #$pr is a draft and was not merged. }A fresh \`ready-for-agent\` label resumes the branch. Run: ${RUN_URL:-}"
}
