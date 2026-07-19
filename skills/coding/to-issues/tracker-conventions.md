# Issue Tracker Conventions

Shared by `to-prd` and `to-issues`: where PRDs and issues get published. Works with or without git.

## Resolve the tracker (per invocation)

1. **Explicit override wins**: if the user says "local" or "github", use that mode.
2. **Otherwise detect**: `git remote -v 2>/dev/null | grep -qi github` succeeds AND `gh auth status` succeeds → **GitHub mode**.
3. **Otherwise** → **Local mode** (no git required).

State which mode you're using when you publish.

## GitHub mode

- **Create an issue**: `gh issue create --title "..." --body "..." --label ready-for-agent` (heredoc for multi-line bodies)
- **If a label doesn't exist**, create it first: `gh label create ready-for-agent --description "Fully specified; an agent can pick this up with no human context" 2>/dev/null || true`
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

- `ready-for-agent` — fully specified; an AFK agent can pick it up with no human context
- `ready-for-human` — needs human implementation (judgment calls, design decisions, external access); note why it can't be delegated

## Working the backlog

Published issues are self-contained work items: a fresh session can pick one up and implement it directly, or feed it to the [create-plan workflow](../create-plan/create-plan.md) for a phased implementation plan. Write them durably — behavior and interfaces, not file paths — so they stay correct as the codebase moves.
