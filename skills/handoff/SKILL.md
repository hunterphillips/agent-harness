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
2. **Determine which lane(s) this session worked.** Infer from the session's actual work; arguments override inference. Match inferences against existing lane descriptions **semantically** — "frontend refactor" matches a lane described as "components, styling, UX flows" even though no words overlap. Ambiguous match → ask. Nothing fits → work that will span sessions gets a new lane: propose a short kebab-case name with a one-line description and confirm before creating. A one-off side task is not a lane: write it as a ticket in `thoughts/shared/tickets/`, or as an item in the `inbox.md` of the lane that owns the area, so it is recorded without a lane to maintain.
3. **Check `git status` and `git diff`** for uncommitted changes.
4. **Write one `handoff.md` per worked lane** (create directories as needed). A session that touched multiple lanes writes each lane's file separately — split the content now, while you still have the context to split it correctly. Each fact goes to the lane it belongs to; don't duplicate shared context across files.
5. **Close the loop outside your own handoff.** A session writes only the lanes it worked, so these two go stale unless the session that caused the change records it:
   - **Tickets.** Each ticket in `thoughts/shared/tickets/` this session worked gets its `status` set: `done` when the work landed, `in-progress` plus one line in the body on what remains when it is partly built, `declined` plus one line naming the ticket that absorbed or superseded it. The value is exactly one of `backlog`, `in-progress`, `done`, `declined`, because `pickup` filters on those words; the explanation goes in the body, not the status.
   - **Other lanes.** If this session's work made something in another lane's handoff false (it changed a mechanism that lane relies on, or shipped an item that lane lists as pending), read that handoff and append one line per false statement to that lane's `inbox.md`. Don't edit the other handoff: its session may be live and will rewrite the file in full. `pickup` surfaces the inbox.
6. **Run `/write-claude-md`** to refresh `CLAUDE.md` (and `README.md` if drifted) and ensure it still conforms to the principles outlined in write-claude-md.

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

- Keep each lane file under ~100 lines. A file past that is cut back in this handoff, not carried forward: finished work comes out (git has it), rationale moves to an ADR or research doc and is referenced by path, and a lane holding two threads is split. Keeping older sections "as written" below new ones is appending.
- A dated check carried in Next ("check the 11-14 brief") whose date has passed gets its result recorded or a new date, not dropped.
- Statements about worktrees, branches, and running processes cover this session's own. Other sessions may be live, so "no worktrees remain" is a claim about work you can't see.
- Forward-looking only: what the next session needs, not a log of this one.
