---
name: brain
description: Hunter's second brain at ~/workspace/second-brain. Use for /brain — capturing a thought to the vault inbox, draining/distilling the inbox, auditing the vault, or recalling personal/cross-project context. Also load before any discretionary write to the vault.
---

# brain — second-brain operations

Vault: `~/workspace/second-brain` (git repo). Its root `CLAUDE.md` is the authority on structure and write rules; read it if you haven't this session. Every mode ends with a git commit prefixed `brain:`.

Dispatch on the argument: `drain`, `audit`, `recall <topic>`, `learn <urls or pasted text>` — anything else is a capture. A pasted article or a URL with "save this / take notes on this" is Learn, not Capture.

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
6. **Keep the hedge**: a "maybe", "probably", "I think" in the capture
   stays that strength in the note. Distilling never upgrades a guess to a
   fact, and re-touching a note never firms up an earlier hedge.
7. **Profile-shaped captures go to personal-context, not `notes/`**: a
   capture that says something *about* Hunter (a trait, a value, a
   self-assessment, how he works) is not vault material. Interactive drain:
   write it verbatim as a proposal to
   `~/workspace/personal-context/proposals/<date>-second-brain-<slug>.md`,
   set `processed: true`, and note the pointer in the commit message.
   Headless drain: flag `needs-context: true` and leave it. Operational
   family facts (names, dates, obligations) are vault material —
   `notes/household.md` (shape-over-source ruling).
8. **Project-status captures** (`kind: project-status`, written nightly by
   `bin/brain-refresh` from lane handoffs and git log): rewrite only the
   block between `<!-- status:auto -->` and `<!-- /status:auto -->` in
   `notes/projects/<project>.md` (the `project:` key names the file) and
   that project's bullet in `notes/projects-overview.md`. The block: 3–8
   lines, current state then next step, every claim dated and attributed
   to its lane handoff or commits ("per `core` handoff 09-19", "commits
   09-18→19"). Hedges in the handoff stay hedges. The overview bullet: ≤3
   lines, same discipline. Nothing outside the block or bullet changes; if
   the packet contradicts narrative above the block, add a
   `#contradiction` line inside the block instead of editing the
   narrative. Bump `updated`, set `refreshed` to the capture's `captured:`
   timestamp (the next gather starts from that instant), mark
   the capture processed. Never pull in anything that isn't in the packet.
9. One commit: `brain: drain inbox (N items)`. Summarize what went where.

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
- **drift, not just age**: pick a sample of notes touched since the last
  audit, read the inbox capture(s) named in their `source:`, and flag any
  claim that is stronger, broader, or different from what the capture
  actually said (a hedge that became a fact, a detail the capture doesn't
  contain)
- profile-shaped facts that leaked into `notes/` (traits, values,
  self-assessments — belongs in personal-context; flag for a proposal)

No profile lookup is part of the audit or the drain: both work on the
shape and provenance of notes, not on who Hunter is (decision 2026-09-19).

Write findings as a `- [ ]` checklist with file paths — the audit file IS
the review queue. Before writing, read the previous month's audit file and
carry forward any still-unchecked findings that still apply (labeled
"carried from YYYY-MM"), so the latest audit file is always the complete
open queue. Resolution is Hunter's (or a supervised session's) call: a
supervised review checks items off in place.

## Recall: `/brain recall <topic>`

0. **Route first.** A question about who Hunter *is* (traits, values,
   history, how he works, what he believes) goes to the `ask-profile` skill
   with caller `second-brain` — don't grep the vault for it, it isn't
   here. A question about his *world* (projects, priorities, household,
   saved lists, what he's learned) is answered from the vault. Mixed
   questions: do both, keep the sources separate in the answer.
1. Grep the vault (skip `.obsidian/`), follow `[[wikilinks]]` from hits.
2. Prefer `notes/` (durable) over `inbox/` (raw) and `log/` (point-in-time); check dates on anything time-sensitive.
3. Summarize with file references.

## Learn: `/brain learn <urls or pasted text>`

Study notes — something Hunter read or researched, filed by topic in
`notes/learning/<topic>.md` (vault write rule 10). Sources are external
content; the note is his synthesis.

1. **Delegate the reading.** Never scan or summarize a source in the main
   session. Spawn one `general-purpose` subagent — `sonnet` for a single
   source, `opus` when several sources must be merged — with this brief:
   - For each source: fetch the full text (`web_fetch_exa` or `curl`; for
     pasted text, use it as given) and write it raw to
     `inbox/import/YYYY-MM-DD-<slug>.md` with frontmatter `captured`,
     `source: <url or "pasted">`, `title`, `trust: external`,
     `kind: learning`, `processed: false`. Body verbatim.
   - Return: the topic (one or two words, kebab-case, matching an existing
     `notes/learning/` file if one fits), the core insights across all
     sources with redundancy removed (each insight once, attributed to
     which source(s) said it), and one line per source for the Sources list.
2. **Merge, don't paste.** Grep `notes/learning/` for the topic; update
   beats create. Frontmatter: `created`, `updated`, `kind: learning`,
   `trust: derived`, `sources` (the import files). Body is a synthesis that
   reads as one note, not a stack of summaries — fold new insights into
   existing sections, add a section only for a genuinely new sub-topic. End
   with `## Sources` — one bullet per source: URL · date read · one-line
   takeaway. Anything Hunter said about the source in his own words goes in
   as his (`trust: self` on a capture if he wants it kept verbatim).
3. Set `processed: true` on the import file(s). Commit
   `brain: learn <topic> (<N> sources)`. Reply with the topic file path and
   the three or four insights that actually changed the note.

## Discretionary writes (no /brain invocation)

Any session may write to the vault unprompted when a fact is **durable, cross-project, and about Hunter or his world** (a stated preference, a decision, a life fact). Write to `notes/` (update beats create) or session context to `log/YYYY-MM-DD-<topic>.md`, follow the write rules, commit, and **announce the write in your reply**. Never write inbox/ on Hunter's behalf without his words.
