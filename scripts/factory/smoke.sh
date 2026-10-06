#!/usr/bin/env bash
# End-to-end smoke of the factory, in agent-harness: open an owner-authored
# issue the triage gate must pass, then wait for triage, the dispatched
# implement run, the merged PR, and the closed issue. Run locally with gh
# authenticated as the owner, or from .github/workflows/smoke.yml with
# FACTORY_SMOKE_TOKEN (a fine-grained PAT of the owner's: issues read/write on
# agent-harness). The issue must be owner-authored, or the merge policy leaves a
# draft and the smoke fails for the wrong reason.
set -euo pipefail

REPO=${SMOKE_REPO:-hunterphillips/agent-harness}
OWNER=${REPO%%/*}
TIMEOUT=${SMOKE_TIMEOUT:-1800}
run_link="${GITHUB_SERVER_URL:-https://github.com}/$REPO/actions${GITHUB_RUN_ID:+/runs/$GITHUB_RUN_ID}"
n=""

fail() {
  echo "smoke failed: $1" >&2
  [ -n "$n" ] && gh issue comment "$n" --repo "$REPO" --body "@$OWNER Smoke failed: $1. $run_link" > /dev/null
  exit 1
}

me=$(gh api user --jq .login)
[ "$me" = "$OWNER" ] || { echo "smoke must run as $OWNER (authenticated as $me)" >&2; exit 2; }

stamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
body="Append one line to \`smoke/log.md\`: \`- $stamp\`. Nothing else changes.

Done when: the last line of \`smoke/log.md\` is exactly \`- $stamp\`. Docs-only change; no test.

Opened by \`scripts/factory/smoke.sh\` to prove the factory chain end to end: triage passes, triage starts the implement run, the run opens a PR, the merge gate merges it, this issue closes."
n=$(gh issue create --repo "$REPO" --title "[smoke] append $stamp to smoke/log.md" --body "$body" | grep -o '[0-9]*$')
echo "smoke issue #$n ($stamp)"

stage=triage
start=$(date +%s)
while :; do
  sleep 20
  labels=$(gh issue view "$n" --repo "$REPO" --json labels --jq '[.labels[].name] | join(",")')
  state=$(gh issue view "$n" --repo "$REPO" --json state --jq .state)
  pr=$(gh pr list --repo "$REPO" --head "claude/issue-$n" --state all --json number,mergedAt --jq '.[0] // empty')
  case ",$labels," in
    *,ready-for-human,*|*,needs-info,*|*,wait,*) fail "issue left as [$labels] at stage $stage" ;;
  esac
  case "$stage" in
    triage)
      case ",$labels," in *,ready-for-agent,*|*,in-progress,*) stage=implement; echo "triage passed" ;; esac ;;
    implement)
      [ -n "$pr" ] && { stage=merge; echo "PR #$(jq -r .number <<< "$pr") opened"; } ;;
    merge)
      [ -n "$(jq -r '.mergedAt // empty' <<< "$pr")" ] && { stage=close; echo "PR merged"; } ;;
    close)
      if [ "$state" = CLOSED ]; then
        [ -z "$labels" ] || fail "closed with labels left on it: $labels"
        echo "smoke passed: #$n in $(( $(date +%s) - start ))s"
        # Keep the three newest smoke issues; close the rest.
        gh issue list --repo "$REPO" --state open --search '"[smoke]" in:title' --json number --jq '.[].number' \
          | sort -rn | tail -n +4 | while read -r old; do
              gh issue close "$old" --repo "$REPO" --comment "Superseded by smoke #$n." > /dev/null
            done
        exit 0
      fi ;;
  esac
  [ $(( $(date +%s) - start )) -lt "$TIMEOUT" ] || fail "timed out after ${TIMEOUT}s at stage $stage"
done
