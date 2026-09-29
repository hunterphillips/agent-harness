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
- **No argument**: list lanes as one-liners — name · description · updated date · headline next step — plus a count of backlog tickets (Step 3.3) if any exist, and ask which to pick up.

**Fallbacks**: no `lanes/` directory but `.claude/pickup.md` exists → read that instead (legacy format; the next `/handoff` migrates it, leaving a `.migrated` rename behind as the marker). Neither exists → say so and ask what to work on.

## Step 3: Load Lane State

Read ONLY the resolved lane's files:

1. `handoff.md` — current state, decisions, next steps
2. `inbox.md` (if present) — items queued for this lane by the user or other sessions. Surface them explicitly at pickup; later, once an item is absorbed into the session's work (or deliberately declined), remove it from `inbox.md`, confirming first. An emptied inbox.md is deleted.
3. **Backlog tickets** — `thoughts/shared/tickets/*.md` with `status: backlog` in frontmatter, project-wide (not lane-scoped). Discrete work items waiting for a session: written by other sessions, by `to-issues`, or routed in from the second-brain drain (those carry `source:` pointing at the vault inbox capture and `routed_to:` listing every project that received it — the item may only partly concern this project). List them as one-liners (date · title · area) alongside the inbox; don't load bodies until one is chosen. Taking one up sets `status: in-progress` (then `done`); one that doesn't belong here gets `status: declined` with a one-line reason, never deleted.
4. **GitHub issues** — when the repo resolves to GitHub mode (remote on GitHub and `gh auth status` succeeds; see `coding/to-issues/tracker-conventions.md`), also list open issues that are actionable by a session:
   ```bash
   gh issue list --state open --label ready-for-agent,ready-for-human,needs-info \
     --json number,title,labels,updatedAt --jq '.[] | "#\(.number) · \(.title) · \([.labels[].name] | join(",")) · \(.updatedAt[:10])"'
   ```
   (`--label a,b,c` matches issues carrying **all** listed labels on some `gh` versions; if the list comes back empty, run one `gh issue list --label <x>` per label.) One-liners alongside the local tickets; don't load bodies until one is chosen. Taking one up adds `in-progress` (`gh issue edit <n> --add-label in-progress`) and removes it when the work lands or is dropped.

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
