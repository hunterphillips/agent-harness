#!/usr/bin/env bash
# Enroll a repository in the factory: create the label vocabulary, set the
# CLAUDE_CODE_OAUTH_TOKEN secret, and write the caller workflow that delegates
# to the reusable jobs in hunterphillips/agent-harness.
#
# Usage: scripts/enroll-repo.sh <path-to-local-clone> [--no-push] [--no-implement] [--runner] [--gate-minutes N]
#
# --no-implement enrolls for triage and monitoring only (no ready-for-agent job).
# --runner puts the factory's jobs on the repo's `factory` runner on hub (labels
# self-hosted, linux, factory; installed by scripts/factory/runner.sh add). The
# repo's own workflows run on its `checks` runner instead, and enrolling refuses
# a pull-request workflow on the factory label. A --runner repo with no
# pull-request workflow merges on the review alone. Refused for a public repo:
# GitHub says self-hosted runners should almost never serve one, since any fork's
# pull request could run code on the box.
# --gate-minutes N widens the merge gate's rounds (the wait for the PR's checks,
# one re-run, each heal round) from the default 30 minutes, for a repo whose
# suite runs longer; the implement job's cap becomes 270 + 5 × N. Hub repos
# only (needs --runner): hosted runners stop a job at 360 minutes. 30 to 150.
#
# The token is read from $CLAUDE_CODE_OAUTH_TOKEN, else ~/.config/factory/token
# (one line, mode 600; generate it once with `claude setup-token`), else you are
# prompted. Pass --no-push to write the workflow without committing it.
set -euo pipefail

repo_path="${1:?usage: enroll-repo.sh <path-to-local-clone> [--no-push] [--no-implement] [--runner] [--gate-minutes N]}"
shift
push=1; implement=1; runner=0; gate_minutes=0
while [ $# -gt 0 ]; do
  case "$1" in
    --no-push) push=0 ;;
    --no-implement) implement=0 ;;
    --runner) runner=1 ;;
    --gate-minutes) gate_minutes=${2:-}; shift ;;
    --gate-minutes=*) gate_minutes=${1#--gate-minutes=} ;;
    *) echo "unknown flag: $1" >&2; exit 2 ;;
  esac
  shift
done
if [ "$gate_minutes" != 0 ]; then
  if ! [[ "$gate_minutes" =~ ^[0-9]+$ ]] || (( gate_minutes < 30 || gate_minutes > 150 )); then
    echo "--gate-minutes takes a whole number of minutes from 30 to 150 (got '$gate_minutes')" >&2; exit 2
  fi
  if (( ! runner )); then
    echo "--gate-minutes needs --runner: a hosted runner stops a job at 360 minutes, so only a hub repo can hold a wider gate" >&2; exit 2
  fi
fi
cd "$repo_path"

slug=$(gh repo view --json nameWithOwner --jq .nameWithOwner)
echo "Enrolling $slug"

# --runner only for private repos, checked before anything is created or set.
if (( runner )); then
  visibility=$(gh repo view --json visibility --jq .visibility)
  if [[ "$visibility" != PRIVATE && "$visibility" != INTERNAL ]]; then
    echo "  refusing --runner: $slug is $visibility, and a self-hosted runner on a public repo runs forks' code" >&2
    exit 2
  fi
  # A pull-request workflow on the factory's own runner can never start while
  # the implement job holds it, and the gate would wait on it for hours. Such
  # workflows belong on the repo's checks runner.
  # A grep, not a parser (the trigger expression is the one in lib.sh's
  # pr_workflow_paths): it misses a multi-line runs-on and a pull-request job
  # that comes from a reusable workflow, and it refuses a file whose
  # pull-request job is on checks while a push-only job is on factory (move
  # that job too). lib.sh's queued-run bound catches what this misses.
  for wf in .github/workflows/*.yml .github/workflows/*.yaml; do
    [[ -f "$wf" && "$(basename "$wf")" != factory-caller.yml ]] || continue
    if grep -qE '^\s*(-\s*|on:.*[[:space:][,{])?pull_request' "$wf" && grep -qE 'runs-on:.*\bfactory\b' "$wf"; then
      echo "  refusing --runner: $wf runs on pull requests with the factory label; use [self-hosted, linux, checks]" >&2
      exit 2
    fi
  done
fi

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
  [[ "$n" == "factory" || "$n" == "factory-jobs" || "$n" == "smoke" ]] && continue   # the caller, the reusable jobs, and the harness's own smoke (it reports itself)
  names+=("$n")
done

runs_on_line=""
(( runner )) && runs_on_line="      runs_on: '[\"self-hosted\",\"linux\",\"factory\"]'"
# The gate window and the job cap it needs, on the implement job only.
gate_lines=""
(( gate_minutes )) && gate_lines=$(printf '      gate_minutes: %d\\n      job_minutes: %d' "$gate_minutes" $((270 + 5 * gate_minutes)))   # awk -v turns the \n into a newline
mkdir -p .github/workflows
{
cat <<'YAML'
# Factory caller: delegates to the reusable jobs in hunterphillips/agent-harness.
# Written by scripts/enroll-repo.sh in that repo; edit there, re-run to refresh.
name: factory
# Dispatched runs are found by this title (scripts/factory/dispatch.sh).
run-name: "${{ github.event_name == 'workflow_run' && format('factory monitor {0}', github.event.workflow_run.name) || format('factory #{0}', inputs.issue_number || github.event.issue.number) }}"
on:
  issues:
    types: [opened, labeled]
  # The factory starts work by dispatch: triage on a gate pass, the next part
  # of a split issue. Its own label events start nothing.
  workflow_dispatch:
    inputs:
      issue_number:
        description: Issue for the implement job
        required: true
        type: number
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
  actions: write
  checks: read
  statuses: read
  id-token: write
jobs:
  triage:
    if: >-
      github.repository == 'SLUG' &&
      github.event_name == 'issues' && github.event.action == 'opened' &&
      github.actor != 'claude[bot]' &&
      !contains(github.event.issue.labels.*.name, 'ready-for-agent') &&
      !contains(github.event.issue.labels.*.name, 'in-progress')
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: triage
      issue_number: ${{ github.event.issue.number }}
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
YAML
if (( ${#names[@]} )); then
cat <<'YAML'
  monitor:
    if: >-
      github.repository == 'SLUG' &&
      github.event_name == 'workflow_run' &&
      github.event.workflow_run.conclusion == 'failure' &&
      github.event.workflow_run.name != 'factory' &&
      !startsWith(github.event.workflow_run.head_branch, 'claude/')
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: monitor
      run_id: ${{ github.event.workflow_run.id }}
      run_url: ${{ github.event.workflow_run.html_url }}
      workflow_name: ${{ github.event.workflow_run.name }}
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
YAML
fi
if (( implement )); then
cat <<'YAML'
  implement:
    if: >-
      github.repository == 'SLUG' && (
      github.event_name == 'workflow_dispatch' || (
      github.event_name == 'issues' &&
      github.event.action == 'labeled' &&
      github.event.label.name == 'ready-for-agent' &&
      github.actor != 'claude[bot]'))
    uses: hunterphillips/agent-harness/.github/workflows/factory.yml@main
    with:
      job: implement
      model: claude-opus-5-5
      issue_number: ${{ github.event.issue.number || fromJSON(inputs.issue_number || '0') }}   # dispatch inputs arrive as strings
    secrets:
      CLAUDE_CODE_OAUTH_TOKEN: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
YAML
fi
} | sed "s|SLUG|$slug|g" | awk -v line="$runs_on_line" -v gate="$gate_lines" '{ print } line != "" && /^      job: / { print line } gate != "" && /^      job: implement$/ { print gate }' > .github/workflows/factory-caller.yml
echo "  wrote .github/workflows/factory-caller.yml (monitoring ${#names[@]} workflow(s): ${names[*]:-none}; implement job: $implement; runner: $runner; gate window: $(( gate_minutes ? gate_minutes : 30 )) min)"

if (( push )); then
  git add -f .github/workflows/factory-caller.yml   # -f: some repos ignore .github
  if git diff --cached --quiet; then
    echo "  caller unchanged; nothing to commit"
  else
    git commit -q -m "Factory caller workflow (enroll-repo.sh)" -- .github/workflows/factory-caller.yml
    git pull -q --rebase --autostash || { echo "  rebase failed; resolve and push manually" >&2; exit 1; }
    git push -q
    echo "  committed and pushed"
  fi
else
  echo "  --no-push: commit .github/workflows/factory-caller.yml yourself"
fi
echo "Done: $slug"
