---
name: aside
description: ALWAYS invoke when the user interrupts the work in flight with a side thought — an idea, question, piece of feedback, or small request that is not the current task — signalled by `/aside`, "side note", "sidebar", "while I think of it", "unrelated, but". Decide whether to answer it, do it, fork it, or catalog it, then return to the main thread. Not for `/brain` (verbatim vault capture about Hunter's world) and not for the task already in progress.
argument-hint: <the thought>
---

# Aside

Handle a side thought without losing the main thread. You decide what happens to it; the user should not have to.

If invoked with no text, ask what the aside is.

## 1. Judge

Pick one. Say which in a few words.

- **Do it now**: a quick, unambiguous update (a label, a line of copy, a config value). Do it, confirm in one line.
- **Answer it**: a question answerable from what the session already knows. Answer briefly. (For a question you want kept out of the conversation entirely, the native `/btw` does that.)
- **Fork it**: independent work that needs tools but not the main thread. Dispatch a subagent (or the native `/subtask`) with a self-contained brief; its result comes back later.
- **Catalog it**: anything that needs discussion, design, or planning, or that belongs to a later phase. This is the default when in doubt.

Ask a clarifying question only if the decision itself depends on the answer. Otherwise record what you assumed in the ticket.

## 2. Catalog

Write `thoughts/shared/tickets/YYYY-MM-DD-<slug>.md`:

```markdown
---
created: YYYY-MM-DD
status: backlog
area: <lane or component>
source: Hunter, <lane> conversation YYYY-MM-DD (aside)
trust: self
context: <one or two sentences: what prompted it, and when it should come up — a phase, a plan, a decision it depends on>
---

<The ask, shaped as a ticket. Keep Hunter's own phrasing for the parts that carry intent; add the one or two facts from the session a future reader needs. Note any assumption you made.>
```

Then add one line under `## Next` in the active lane's `thoughts/shared/lanes/<lane>/handoff.md` pointing at the ticket, with when it should surface. No active lane: use that lane's `inbox.md`, or the ticket alone if there are no lanes. `pickup` lists backlog tickets at session start, so nothing else is needed for it to resurface.

Never a GitHub issue unless the user says so; issues come from `to-issues` or an explicit ask. If the thought is about Hunter's world rather than this project (a preference, a decision, a life fact), say so and point at `/brain`.

## 3. Return

Reply in two or three lines: the outcome and path, then "Back to: <what the main thread was doing, in the user's terms>". Then continue that work. Don't summarize the aside again later.
