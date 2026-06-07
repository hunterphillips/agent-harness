---
name: to-issues
description: Use when the user wants to convert a plan into issues, create implementation tickets, or break down work for parallel or AFK pickup. Breaks a plan, spec, or PRD into independently-grabbable tracer-bullet vertical slices, published to GitHub Issues when available or local markdown under thoughts/ otherwise.
---

# To Issues

Break a plan into independently-grabbable issues using vertical slices (tracer bullets).

Tracker resolution and publishing mechanics: [tracker-conventions.md](./tracker-conventions.md).

## Process

### 1. Gather context

Work from whatever is already in the conversation. If the user passes a reference (issue number, path, or URL — e.g. a PRD or a `thoughts/shared/plans/` doc), fetch and read it fully.

### 2. Explore the codebase (optional)

If you haven't already, explore to understand the current state of the code. Issue titles and descriptions should use the project's domain glossary (`CONTEXT.md`) vocabulary and respect ADRs in the area you're touching.

### 3. Draft vertical slices

Break the plan into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices are 'HITL' or 'AFK'. HITL slices require human interaction (an architectural decision, a design review). AFK slices can be implemented and merged without human interaction. Prefer AFK where possible.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories this addresses (if the source has them)

Ask: Does the granularity feel right? Are the dependencies correct? Should any slices merge or split? Are the right slices HITL vs AFK?

Iterate until the user approves.

### 5. Publish to the issue tracker

For each approved slice, publish an issue per the tracker conventions, using the template below. Mark AFK slices `ready-for-agent` and HITL slices `ready-for-human` (noting why), unless instructed otherwise.

Publish in dependency order (blockers first) so "Blocked by" can reference real issue identifiers (`#42` or the issue file path).

<issue-template>
## Parent

Reference to the parent PRD/issue (omit if none).

## What to build

A concise description of this vertical slice — the end-to-end behavior, not layer-by-layer implementation.

Avoid specific file paths or code snippets — they go stale fast. Exception: a prototype-derived snippet that encodes a decision more precisely than prose (state machine, reducer, schema, type shape) — inline the decision-rich parts and note the origin.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2

## Blocked by

- Reference to the blocking issue, or "None - can start immediately"

</issue-template>

Do NOT close or modify any parent issue or PRD.
