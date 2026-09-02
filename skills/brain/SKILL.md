---
name: brain
description: Hunter's second brain at ~/workspace/second-brain. Use for /brain — capturing a thought to the vault inbox, draining/distilling the inbox, auditing the vault, or recalling personal/cross-project context. Also load before any discretionary write to the vault.
---

# brain — second-brain operations

Vault: `~/workspace/second-brain` (git repo). Its root `CLAUDE.md` is the authority on structure and write rules; read it if you haven't this session. Every mode ends with a git commit prefixed `brain:`.

Dispatch on the argument: `drain`, `audit`, `recall <topic>` — anything else is a capture.

## Capture (default): `/brain <text>`

Capture Hunter's words **verbatim** — no rewriting, no summarizing, no title-casing his phrasing. If invoked with no text, ask what to capture.

1. Write `inbox/YYYY-MM-DD-HHMM-<slug>.md` (slug: 2-4 words from the thought, kebab-case):

   ```markdown
   ---
   captured: <ISO 8601 timestamp>
   source: claude-code
   trust: self
   processed: false
   ---

   (`trust` is `self` for Hunter's own words; `derived` for agent-authored
   summaries of his activity; `external` for content originating outside —
   email, web, other people. Bulk imports land in `inbox/import/` with
   `trust: external`. An optional `context:` key may carry one line of
   capture-time provenance, e.g. what session or situation prompted it.)

   <the user's words, verbatim>
   ```

2. Distill immediately while you still have the session context: write the well-formed version into `notes/` (or `log/` if it's session-state) following the Drain rules below, and set `processed: true` in the inbox file's frontmatter. The inbox body stays verbatim — it's provenance, not the deliverable.
3. Commit both files: `brain: capture <slug>`.
4. Confirm in one line and return to whatever you were doing. No follow-up questions.

## Drain: `/brain drain`

Distill unprocessed captures into durable notes. (Mid-session captures are distilled at capture time; drain mainly sweeps context-free sources like hotkey and phone.)

1. Find inbox files with `processed: false`.
2. For each: **update beats create** — grep `notes/` for an existing note on the topic and extend it; create a new `notes/<topic>.md` only when nothing fits. Notes frontmatter: `created`, `updated`, `source` (the inbox file(s) distilled from). Link related notes with `[[wikilinks]]`.
3. Set `processed: true` in the inbox file's frontmatter. Never touch its body — raw is sacred.
4. **Trust rule**: content tagged `trust: external` (or anything under
   `inbox/import/`) is never promoted into `notes/` in a headless run —
   leave it unprocessed for a supervised session. `self`/`derived` drain
   normally.
5. **Contradictions**: if a capture conflicts with an existing note, don't
   silently overwrite — record both claims and mark the line with
   `#contradiction` so it surfaces at read time, not just at the monthly
   audit.
6. One commit: `brain: drain inbox (N items)`. Summarize what went where.

An item whose meaning or target project is ambiguous: in an interactive session, ask Hunter. In a headless/scheduled run, don't guess — add `needs-context: true` to its frontmatter and leave it unprocessed; a later interactive drain clears the flag by asking. (A nightly launchd job runs drain automatically when unflagged unprocessed items exist; monthly, an audit writes findings to `log/audit-YYYY-MM.md`.)

## Audit: `/brain audit`

Report, fix nothing. **Scope: content hygiene of `notes/` and `log/`
only** — not machine state, infrastructure, scripts, or tooling (that's
the system lane's business, checked on demand, not monthly). Scan for:

- duplicate or overlapping notes on one topic
- contradictory claims
- stale facts (old `updated` dates on fast-changing topics; references to things that no longer exist)
- broken `[[wikilinks]]`
- emergent clusters: ~4–5 flat notes in `notes/` on one theme → propose a
  one-level `notes/<theme>/` subfolder (structure is emergent, never imposed
  at capture — vault write rule 8)
- `log/` entries whose durable content never made it into `notes/`
  (episodic → semantic consolidation candidates)
- `#contradiction` markers still unresolved in `notes/`

Write findings as a `- [ ]` checklist with file paths — the audit file IS
the review queue. Before writing, read the previous month's audit file and
carry forward any still-unchecked findings that still apply (labeled
"carried from YYYY-MM"), so the latest audit file is always the complete
open queue. Resolution is Hunter's (or a supervised session's) call: a
supervised review checks items off in place.

## Recall: `/brain recall <topic>`

1. Grep the vault (skip `.obsidian/`), follow `[[wikilinks]]` from hits.
2. Prefer `notes/` (durable) over `inbox/` (raw) and `log/` (point-in-time); check dates on anything time-sensitive.
3. Summarize with file references.

## Discretionary writes (no /brain invocation)

Any session may write to the vault unprompted when a fact is **durable, cross-project, and about Hunter or his world** (a stated preference, a decision, a life fact). Write to `notes/` (update beats create) or session context to `log/YYYY-MM-DD-<topic>.md`, follow the write rules, commit, and **announce the write in your reply**. Never write inbox/ on Hunter's behalf without his words.
