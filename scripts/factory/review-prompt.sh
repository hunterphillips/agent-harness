#!/usr/bin/env bash
# Fill the harness's code-reviewer template for an independent review of the
# issue branch, written to .factory/review-prompt.md. The review step reads it.
# Env: N REPO BRANCH HARNESS (path to the harness checkout).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

template="${HARNESS:-.harness}/skills/coding/requesting-code-review/code-reviewer.md"
base=$(state_get BASE)
head=$(git rev-parse HEAD)
pr=$(pr_for_branch "$BRANCH")
description=$( [ -n "$pr" ] && gh pr view "$pr" --repo "$REPO" --json body --jq .body || echo "(no pull request body)")
issue_text() { # issue_text <n>: title, body, and every comment as markdown
  gh issue view "$1" --repo "$REPO" --json title,body,comments \
    --jq '"# \(.title)\n\n\(.body)\n\n" + ([.comments[] | "---\n\(.author.login):\n\(.body)"] | join("\n\n"))'
}
requirements=$(issue_text "$N")
# A part is judged against its parent too: the parent holds the decisions and
# the end state the parts share, so a scope call the parent settled is not a finding.
parent=$(part_parent "$N")
if [ -n "$parent" ]; then
  requirements+=$(printf '\n\n# Parent issue #%s (decisions and end state shared by every part)\n\n%s' "$parent" "$(issue_text "$parent")")
fi

# Everything between the template's ``` fences after "prompt: |", with the
# placeholders filled. awk strips the YAML indentation of the Agent-tool example.
awk '/^    prompt: \|/{p=1; next} /^```/{if(p) exit} p{sub(/^    /, ""); print}' "$template" \
  | DESC="$description" REQ="$requirements" B="$base" H="$head" perl -pe '
      s/\{DESCRIPTION\}/$ENV{DESC}/g; s/\{PLAN_OR_REQUIREMENTS\}/$ENV{REQ}/g;
      s/\{BASE_SHA\}/$ENV{B}/g; s/\{HEAD_SHA\}/$ENV{H}/g' \
  > "$FACTORY_DIR/review-prompt.md"

cat >> "$FACTORY_DIR/review-prompt.md" <<'EOF'

## How to answer

You are the merge gate, not the implementer: change nothing. Read the diff
with git only. When done, return the structured output the run asked for:
`critical` and `important` are the counts of findings at those severities that
remain in the diff as it stands; `summary` is at most three sentences naming
them, or the one sentence that says the change is sound.
EOF
log "review prompt: $(wc -l < "$FACTORY_DIR/review-prompt.md") lines, range ${base:0:7}..${head:0:7}"
