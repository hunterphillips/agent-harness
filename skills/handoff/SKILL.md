---
name: handoff
description: Save session state before closing or clearing context, when the user says "handoff" or "save state", or when a stream of work wraps up — do not end a working session without it
argument-hint: [lane and/or next-session focus (optional)]
allowed-tools: Bash(git status:*), Bash(git diff:*), Bash(ls:*), Bash(mv:*)
---

# Session Handoff

Save session state to per-lane handoff files so the next session on each thread of work can continue seamlessly.

A **lane** is a durable thread of work in a project — a concern like `ui`, `architecture`, `research`, or a named effort like `auth-refactor`. Sessions come and go; lanes persist. Each lane's state lives at:

```
thoughts/shared/lanes/<lane-name>/handoff.md
```

`handoff.md` is **rewritten in full each handoff, never appended** — it holds current state and what's next, not history (git covers the past).

## Task

1. **Discover existing lanes**: `ls thoughts/shared/lanes/*/handoff.md` and read each file's frontmatter `description`. No `lanes/` directory yet → you'll create it in step 4.
2. **Determine which lane(s) this session worked.** Infer from the session's actual work; arguments override inference. Match inferences against existing lane descriptions **semantically** — "frontend refactor" matches a lane described as "components, styling, UX flows" even though no words overlap. Ambiguous match → ask. Nothing fits → propose a new short kebab-case lane name with a one-line description and confirm before creating.
3. **Check `git status` and `git diff`** for uncommitted changes.
4. **Write one `handoff.md` per worked lane** (create directories as needed). A session that touched multiple lanes writes each lane's file separately — split the content now, while you still have the context to split it correctly. Each fact goes to the lane it belongs to; don't duplicate shared context across files.
5. **Absorb legacy state**: if `.claude/pickup.md` exists, fold its still-relevant content into the lane file(s) — this session's facts supersede stale legacy notes — then rename it to `.claude/pickup.md.migrated`.
6. **Run `/write-claude-md`** to refresh `CLAUDE.md` (and `README.md` if drifted).

## File Format

```markdown
---
lane: ui
description: Frontend look/feel — components, styling, UX flows
updated: 2026-08-26
---

## Current State

[What's in flight: complete / in progress / blocked, with specifics]

## Uncommitted Changes

- `path/to/file` — [what and why] (omit section if clean)

## Key Decisions

- [Decision]: [rationale]

## Next

- [Open thread, pending decision, or next step]
- [Suggested workflow to route through, e.g. implement-plan for thoughts/shared/plans/X]
```

The frontmatter `description` is the lane's scope statement — what belongs here, not its status. Write it once when the lane is created; leave it stable so future sessions can match against it. `updated` is today's date. Omit any section with nothing to say. Undecided leanings ("leaning X; blocked on Y") are Current State, not Key Decisions. Files under `thoughts/` never count as uncommitted changes — they're synced, not committed.

## What to Include / Exclude

Include the **delta from baseline project knowledge**: recent work, current state, uncommitted changes and why, decisions made, open threads, suggested next skills/workflows.

Exclude anything already captured elsewhere — project architecture and conventions (CLAUDE.md), plan/research/ADR content (reference by path instead). If valuable content exists only in this session's context (a decision's rationale, analysis, comparison notes), don't let it die with the session: inline it if it fits the line cap, otherwise write it to the proper artifact (`thoughts/shared/research/`, ADR) now and reference it. Redact secrets: API keys, tokens, PII.

## Example

A session that built a settings page and also decided to swap the job queue writes two files:

- `lanes/ui/handoff.md` — settings page state, the uncommitted component files, "next: hook up validation"
- `lanes/architecture/handoff.md` — queue decision + rationale, pointer to the ADR, "next: migration plan"

The git status showing both change sets appears split across the two files by ownership, not copied into both.

## Notes

- Keep each lane file under ~100 lines — content is lane-scoped now; if it's growing past that, it's probably absorbing another lane's work or restating what an artifact already captures.
- Forward-looking only: what the next session needs, not a log of this one.
