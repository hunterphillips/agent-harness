# Bootstrap a project WRITING.md

Create a per-project writing style guide at the repo root (`WRITING.md`). Model: the guides this skill was distilled from — scope statement, voice anchor with real quotes, project-specific rules, AI-tells subset, process.

## Process

1. **Map the prose surfaces.** What user-facing prose does this project produce? (Docs, digests, summaries, UI copy, generated LLM output, emails.) List them in the guide's scope line — including any prompts/templates that *generate* prose, since tone is set there ("fix tone at the prompt, not the output").
2. **Pick voice anchors with the user.** Propose 1–2 writers who explain this project's domain plainly (research → Melanie Mitchell; tech/business analysis → Benedict Evans; finance for non-experts → Morgan Housel; adjust to domain). Ask the user to confirm or name their own. Include 1–2 short real quotes per anchor showing the register, and state explicitly: borrow the principles (fewest words, concrete over abstract, honest unknowns), not the tics.
3. **Collect project rules.** Banned internal shorthand, naming conventions, legal/attribution constraints, register per surface. These come from the user and the codebase — don't invent them.
4. **Inline the portable core.** A condensed AI-tells list and the general patterns (billboard test, adjectives state don't sell, no metacommentary, concede-then-commit, shorter-when-equal) — copy from [craft.md](craft.md), trimmed to what this project's surfaces need.
5. **End with process**: draft clean → AI-audit → surgical edits.

## Skeleton

```markdown
# Writing style

Applies to [every prose surface, incl. generating prompts]. The target: prose that
sounds like a person stating things directly. [Register: e.g. plain editorial /
academic-but-plain]. When unsure whether a sentence works, read it aloud.

## Voice anchor
[1–2 writers + short quotes; principles not tics]

## Project rules
[shorthand bans, naming, attribution, per-surface register]

## AI tells to cut
[condensed list]

## General patterns
[billboard test · adjectives state · no metacommentary · concede-then-commit · shorter wins]

## Process
1. Draft clean. 2. Audit for AI tells. 3. Surgical edits only.
```

Keep the whole guide under ~100 lines. It gets read by every future writing session in that project — context is precious there too.
