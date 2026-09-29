# Issue Tracker Conventions

Shared by `to-prd` and `to-issues`: where PRDs and issues get published. Works with or without git.

## Resolve the tracker (per invocation)

1. **Explicit override wins**: if the user says "local" or "github", use that mode.
2. **Otherwise detect**: `git remote -v 2>/dev/null | grep -qi github` succeeds AND `gh auth status` succeeds → **GitHub mode**.
3. **Otherwise** → **Local mode** (no git required).

State which mode you're using when you publish.

## GitHub mode

- **Create an issue**: `gh issue create --title "..." --body "..." --label ready-for-agent` (heredoc for multi-line bodies)
- **Ensure the label vocabulary exists** (idempotent; run once per repo, safe to rerun):

  ```bash
  while IFS='|' read -r name color desc; do
    gh label create "$name" --color "$color" --description "$desc" 2>/dev/null \
      || gh label edit "$name" --color "$color" --description "$desc" >/dev/null
  done <<'EOF'
  needs-triage|fbca04|New; the triage job has not classified it yet
  ready-for-agent|0e8a16|Fully specified; an agent can pick this up with no human context
  ready-for-human|d93f0b|Needs a human: judgment call, design decision, or external access
  needs-info|c5def5|Triage asked up to three questions; answer and remove this label to re-triage
  wait|bfdadc|Blocked on an external event; not actionable yet
  in-progress|1d76db|Claimed by an agent or a session
  monitor|5319e7|Opened by the monitor job for a failed workflow run; one per failure signature
  EOF
  ```
- **Read / list / comment**: `gh issue view <n> --comments` · `gh issue list --label ready-for-agent` · `gh issue comment <n> --body "..."`
- Reference issues by number (`#42`).

## Local mode

- One feature per directory: `thoughts/shared/tickets/<feature-slug>/`
- The PRD is `thoughts/shared/tickets/<feature-slug>/PRD.md`
- Issues are `thoughts/shared/tickets/<feature-slug>/issues/NN-<slug>.md`, numbered from `01`
- Record status as a `Status:` line near the top of each issue file
- Comments and follow-ups append under a `## Comments` heading
- Reference issues by path.

## Status vocabulary

One status label per issue. Triage (the [triage workflow](../triage/triage.md), locally or as the cloud job) replaces `needs-triage` with exactly one of the next four.

- `needs-triage` — default on every new issue in an enrolled repo; nothing has classified it yet
- `ready-for-agent` — fully specified; an AFK agent can pick it up with no human context
- `ready-for-human` — needs human implementation (judgment calls, design decisions, external access); note why it can't be delegated
- `needs-info` — triage asked at most three questions in a comment; the reporter answers and removes the label, which re-triages it
- `wait` — blocked on an external event (a dependency, a decision elsewhere); not actionable yet
- `in-progress` — added by whoever claims the issue (a cloud run or a local `pickup`); removed when the PR opens or the work is dropped
- `monitor` — opened by the monitor job for a failed workflow run; one issue per failure signature, later occurrences append as comments

## Cloud contract

Cloud runs (GitHub Actions, routines) see only the repository and its issues. They never see `thoughts/`, the vault, lane handoffs, or anything on the laptop. An issue that a cloud agent might work must therefore be self-contained: the observed behavior, how to reproduce it, where in the code it lives if known, and what done looks like. If a detail lives only in a local plan or ticket, copy it into the issue body.

## Working the backlog

Published issues are self-contained work items: a fresh session can pick one up and implement it directly, or feed it to the [create-plan workflow](../create-plan/create-plan.md) for a phased implementation plan. Write them durably — behavior and interfaces, not file paths — so they stay correct as the codebase moves.
