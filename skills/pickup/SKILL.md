---
name: pickup
description: Resume a thread of work at session start — when the user says "pickup", "resume", "continue where we left off", or names past work to restart — instead of reconstructing context by hand
argument-hint: [lane, or plain-language description of the work to resume (optional)]
---

# Resume Session

Pick up a lane — a durable thread of work whose state lives at `thoughts/shared/lanes/<lane-name>/` (written by `/handoff`).

## Step 1: Load Project Context

Read `.claude/CLAUDE.md`; run `/onboard` first if this session has no project context yet.

## Step 2: Resolve the Lane

List `thoughts/shared/lanes/` and read each `handoff.md` frontmatter (`lane`, `description`, `updated`).

- **Argument given**: match it against lane names and descriptions **semantically** — the user won't know exact lane names. "the frontend refactor work" resolves to a lane described as "components, styling, UX flows". Peek at candidates' handoff bodies if descriptions don't settle it (resolution reads are exempt from Step 3's scoping, which applies after resolution). **State the resolution before proceeding** ("picking up **ui** — Frontend look/feel") so a wrong match is caught immediately. Genuinely ambiguous → ask, showing the candidates.
- **No argument**: list lanes as one-liners — name · description · updated date · headline next step — and ask which to pick up.

**Fallbacks**: no `lanes/` directory but `.claude/pickup.md` exists → read that instead (legacy format; the next `/handoff` migrates it, leaving a `.migrated` rename behind as the marker). Neither exists → say so and ask what to work on.

## Step 3: Load Lane State

Read ONLY the resolved lane's files:

1. `handoff.md` — current state, decisions, next steps
2. `inbox.md` (if present) — items queued for this lane by the user or other sessions. Surface them explicitly at pickup; later, once an item is absorbed into the session's work (or deliberately declined), remove it from `inbox.md`, confirming first. An emptied inbox.md is deleted.

Do not load other lanes' state into context — lane-scoped context is the point (the frontmatter scans during resolution don't count).

## Step 4: Orient and Continue

Briefly confirm: what this lane was working on, its status, uncommitted changes or pending decisions. Then act on the user's request:

$ARGUMENTS

If the argument only identified the lane (no task in it), ask what to focus on, informed by the lane's Next section and inbox.

## Tools Available

- `@.claude/agents/codebase-analyzer.md` — understand how code works
- `@.claude/agents/codebase-locator.md` — find relevant files and components

## Guidelines

- Don't re-explain project basics already covered in CLAUDE.md
- Reference lane context naturally; don't recite the handoff back verbatim
- Prioritize continuity — pick up the thread, don't start fresh
