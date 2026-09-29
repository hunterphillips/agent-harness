#!/usr/bin/env bash
# Enroll a repository in the factory: create the label vocabulary, set the
# CLAUDE_CODE_OAUTH_TOKEN secret, and write the caller workflow that delegates
# to the reusable jobs in hunterphillips/agent-harness.
#
# Usage: scripts/enroll-repo.sh <path-to-local-clone> [--no-push]
#
# The token comes from $CLAUDE_CODE_OAUTH_TOKEN if set, otherwise you are
# prompted (generate one with `claude setup-token`). Pass --no-push to write the
# workflow without committing it.
set -euo pipefail

repo_path="${1:?usage: enroll-repo.sh <path-to-local-clone> [--no-push]}"
push=1; [[ "${2:-}" == "--no-push" ]] && push=0
cd "$repo_path"

slug=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
echo "Enrolling $slug"

# 1. Labels (idempotent). Same vocabulary as skills/coding/to-issues/tracker-conventions.md.
while IFS='|' read -r name color desc; do
  gh label create "$name" --color "$color" --description "$desc" 2>/dev/null \
    || gh label edit "$name" --color "$color" --description "$desc" >/dev/null
done <<'LABELS'
needs-triage|fbca04|New; the triage job has not classified it yet
ready-for-agent|0e8a16|Fully specified; an agent can pick this up with no human context
ready-for-human|d93f0b|Needs a human: judgment call, design decision, or external access
needs-info|c5def5|Triage asked up to three questions; answer and remove this label to re-triage
wait|bfdadc|Blocked on an external event; not actionable yet
in-progress|1d76db|Claimed by an agent or a session
monitor|5319e7|Opened by the monitor job for a failed workflow run; one per failure signature
LABELS
echo "  labels ok"

# 2. Secret.
if gh secret list --json name --jq '.[].name' | grep -qx CLAUDE_CODE_OAUTH_TOKEN; then
  echo "  secret CLAUDE_CODE_OAUTH_TOKEN already set (leave as is)"
else
  token="${CLAUDE_CODE_OAUTH_TOKEN:-}"
  if [[ -z "$token" ]]; then
    read -r -s -p "  CLAUDE_CODE_OAUTH_TOKEN (from 'claude setup-token'): " token; echo
  fi
  [[ -n "$token" ]] || { echo "  no token given; aborting" >&2; exit 1; }
  printf '%s' "$token" | gh secret set CLAUDE_CODE_OAUTH_TOKEN
  echo "  secret set"
fi

# 3. Caller workflow. Phases 3 and 4 extend the triggers in this same file.
mkdir -p .github/workflows
cat > .github/workflows/factory-caller.yml <<'YAML'
# Factory caller: delegates to the reusable jobs in hunterphillips/agent-harness.
# Written by scripts/enroll-repo.sh in that repo; edit there, re-run to refresh.
name: factory
on:
  issues:
    types: [opened]
permissions:
  contents: read
  issues: write
  pull-requests: read
  id-token: write
jobs:
  triage:
    if: github.event.action == 'opened' && github.actor != 'claude[bot]'
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: triage
      issue_number: ${{ github.event.issue.number }}
    secrets: inherit
YAML
echo "  wrote .github/workflows/factory-caller.yml"

if (( push )); then
  git add .github/workflows/factory-caller.yml
  if git diff --cached --quiet; then
    echo "  caller unchanged; nothing to commit"
  else
    git commit -q -m "Enroll in the factory: triage caller workflow" -- .github/workflows/factory-caller.yml
    git push -q
    echo "  committed and pushed"
  fi
else
  echo "  --no-push: commit .github/workflows/factory-caller.yml yourself"
fi
echo "Done: $slug"
