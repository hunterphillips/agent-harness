#!/usr/bin/env bash
# Enroll a repository in the factory: create the label vocabulary, set the
# CLAUDE_CODE_OAUTH_TOKEN secret, and write the caller workflow that delegates
# to the reusable jobs in hunterphillips/agent-harness.
#
# Usage: scripts/enroll-repo.sh <path-to-local-clone> [--no-push] [--no-implement]
#
# --no-implement enrolls for triage and monitoring only (no ready-for-agent job);
# cfo uses this until its unattended-host rule is revisited.
#
# The token is read from $CLAUDE_CODE_OAUTH_TOKEN, else ~/.config/factory/token
# (one line, mode 600; generate it once with `claude setup-token`), else you are
# prompted. Pass --no-push to write the workflow without committing it.
set -euo pipefail

repo_path="${1:?usage: enroll-repo.sh <path-to-local-clone> [--no-push] [--no-implement]}"
shift
push=1; implement=1
for arg in "$@"; do
  case "$arg" in
    --no-push) push=0 ;;
    --no-implement) implement=0 ;;
    *) echo "unknown flag: $arg" >&2; exit 2 ;;
  esac
done
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
  token_file="$HOME/.config/factory/token"
  if [[ -z "$token" && -s "$token_file" ]]; then
    token=$(tr -d '[:space:]' < "$token_file")
    echo "  token read from $token_file"
  fi
  if [[ -z "$token" ]]; then
    read -r -s -p "  CLAUDE_CODE_OAUTH_TOKEN (from 'claude setup-token'): " token; echo
  fi
  [[ -n "$token" ]] || { echo "  no token given; aborting" >&2; exit 1; }
  printf '%s' "$token" | gh secret set CLAUDE_CODE_OAUTH_TOKEN
  echo "  secret set"
fi

# 3. Caller workflow. The workflow_run trigger must name workflows explicitly, so
#    collect every workflow name in this repo except the caller itself. Re-run this
#    script after adding a workflow so the monitor sees it.
names=()
for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
  [[ -f "$wf" ]] || continue
  [[ "$(basename "$wf")" == "factory-caller.yml" ]] && continue
  n=$(sed -n 's/^name:[[:space:]]*//p' "$wf" | head -1 | tr -d '"'"'"'')
  [[ -n "$n" ]] || n=$(basename "$wf" | sed 's/\.ya\?ml$//')
  [[ "$n" == "factory" || "$n" == "factory-jobs" ]] && continue   # the caller and the reusable jobs
  names+=("$n")
done

mkdir -p .github/workflows
{
cat <<'YAML'
# Factory caller: delegates to the reusable jobs in hunterphillips/agent-harness.
# Written by scripts/enroll-repo.sh in that repo; edit there, re-run to refresh.
name: factory
on:
  issues:
    types: [opened, labeled]
YAML
if (( ${#names[@]} )); then
  echo "  workflow_run:"
  echo "    workflows:"
  for n in "${names[@]}"; do echo "      - \"$n\""; done
  echo "    types: [completed]"
fi
cat <<'YAML'
permissions:
  contents: write
  issues: write
  pull-requests: write
  actions: read
  id-token: write
jobs:
  triage:
    if: github.event_name == 'issues' && github.event.action == 'opened' && github.actor != 'claude[bot]'
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: triage
      issue_number: ${{ github.event.issue.number }}
    secrets: inherit
YAML
if (( ${#names[@]} )); then
cat <<'YAML'
  monitor:
    if: >-
      github.event_name == 'workflow_run' &&
      github.event.workflow_run.conclusion == 'failure' &&
      github.event.workflow_run.name != 'factory' &&
      github.event.workflow_run.triggering_actor.login != 'claude[bot]' &&
      !startsWith(github.event.workflow_run.head_branch, 'claude/')
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: monitor
      run_id: ${{ github.event.workflow_run.id }}
      run_url: ${{ github.event.workflow_run.html_url }}
      workflow_name: ${{ github.event.workflow_run.name }}
    secrets: inherit
YAML
fi
if (( implement )); then
cat <<'YAML'
  implement:
    if: >-
      github.event_name == 'issues' &&
      github.event.action == 'labeled' &&
      github.event.label.name == 'ready-for-agent' &&
      github.actor != 'claude[bot]'
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: implement
      model: claude-opus-5-5
      issue_number: ${{ github.event.issue.number }}
    secrets: inherit
YAML
fi
} > .github/workflows/factory-caller.yml
echo "  wrote .github/workflows/factory-caller.yml (monitoring ${#names[@]} workflow(s): ${names[*]:-none}; implement job: $implement)"

if (( push )); then
  git add .github/workflows/factory-caller.yml
  if git diff --cached --quiet; then
    echo "  caller unchanged; nothing to commit"
  else
    git commit -q -m "Factory caller workflow (enroll-repo.sh)" -- .github/workflows/factory-caller.yml
    git push -q
    echo "  committed and pushed"
  fi
else
  echo "  --no-push: commit .github/workflows/factory-caller.yml yourself"
fi
echo "Done: $slug"
