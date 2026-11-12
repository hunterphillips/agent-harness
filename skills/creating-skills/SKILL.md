---
name: creating-skills
description: Use when creating new skills, editing existing skills, or verifying skills work before deployment
---

# Creating and editing skills

A skill is a prompt the model loads on demand: a reference for a technique, a workflow, or a tool that future sessions should apply the same way. This file holds what is specific to this repo and to current models. Anthropic's general guidance is in [anthropic-best-practices.md](anthropic-best-practices.md), a snapshot of the docs page; re-sync it from the live page rather than hand-editing it.

## When a skill is the right unit

Create one when the technique was not obvious, you would reach for it again across projects, and the pattern is general. Don't create one for a one-off solution, for a practice well documented elsewhere, for a project-specific convention (that is CLAUDE.md), or for a mechanical constraint (if a regex or a script can enforce it, automate it and save prose for judgment calls).

In this repo, software-delivery workflows are not listed skills: they are sub-file bundles under `skills/coding/<workflow>/` reached through the `coding` router, because narrow descriptions competing in the listing under-trigger. A new delivery workflow is a router row plus a bundle, not a new top-level skill.

## Conventions here

- Kebab-case name with distinctive first characters (the name is what slash-autocomplete matches). Frontmatter: `name` and `description` required; `model`, `argument-hint`, and `disable-model-invocation` (user-only invocation) as needed. Router sub-files carry no frontmatter.
- The description says **when to invoke**, trigger-first and directive ("ALWAYS invoke when … do not X without it"), because skills under-trigger and passive phrasing measurably fails to fire. It does not describe the method: a description that summarizes the workflow gets followed in place of the body (a "code review between tasks" summary once produced one review where the body specified two). Descriptions must be disjoint across listed skills; overlap makes routing a coin flip.
- One `SKILL.md`, lean: each rule once, one excellent example, bulk templates and shared rules in sub-files the body links one hop away (deeper chains get partially read). Inside `coding/`, every sub-file is linked from `coding/SKILL.md` and cross-references use relative paths; a dispatched subagent cannot resolve those paths, so a controller reads and inlines what the subagent needs.
- Scripts a skill ships are referenced from the base directory shown when the skill loads, not from `.claude/skills/...`; the skills are symlinked and the path differs by machine and runtime.
- A new skill needs a symlink in `~/.claude/skills/`; a removed or renamed one needs its dead symlink deleted. Update the counts and lists in `CLAUDE.md` in the same session.
- `scripts/check-skills.sh` checks frontmatter and link integrity; CI runs it on every push.

## Writing for current models

Current models follow instructions literally and apply emphasis and caution more than earlier ones did, so a skill written as a script for a weaker model now holds a capable one back.

- State the goal, the constraints, and how to verify. Use numbered steps where order matters or the operation is fragile (a label sequence, a marker file, a `gh` command with the right flags); elsewhere, say what good looks like and let the model choose the method.
- Give each rule its reason. A "never" without one is applied as an absolute, including where the author would have made an exception; a rule with its reason lets the model see the boundary.
- No capitals, "CRITICAL", "MUST", or "always" for emphasis. They over-apply. If a rule matters, the reason carries the weight.
- Name the steps that need no approval as clearly as the ones that do. Stop conditions pile up across files, and a model that loads several will hold routine work. The `coding` router's confirmation rule is the model for this.
- Prefer audience framing to numeric clamps ("as long as the verdict needs", not "1-2 sentences"); counts and word limits are obeyed closely enough to make output choppy.
- One worked example, and make it the behaviour you want copied: the model matches its length, tone, and content. An example that models the wrong move (asking about a flag, extracting a constant for its own sake) teaches it.
- A description, a "think deeply", or a "be thorough" does not change reasoning depth; effort does. Cut those lines.
- Keep what only the author knows: a contract with another system, the cost of a past incident, a decision and its rationale. Context is not cruft; the cuts above are for instructions that restate the obvious or the process.

## Editing a skill from observed failures

Usage telemetry and transcripts will surface sessions where a skill "didn't work." Most of those are model variance, not skill defects. Edit only when all three hold:

1. A missing or wrong instruction caused the failure: you can point to the line that should have said something else.
2. The same gap appears more than once, or once with severe consequences.
3. The fix replaces guidance rather than appending to it. If the section is already correct and the agent ignored it, adding more words will not help.

One bad run is not grounds. If a removal regresses, restore the instruction in its shortest form with its reason, not the original text.

## Testing

Nothing above is known to work until it has run. Two harnesses exist:

- `eval/run.py` runs a task with and without the repo configuration and has Codex judge the pair blind, in both orders. For a new skill or a substantive edit: pick two or three realistic tasks the skill should change, run them without it to see what the bare model does, write the least that closes the observed gap, then run the pair. Cost and usage are in `eval/README.md`; a one-task, one-replicate smoke run comes before a battery.
- `eval/skill-trigger/` measures whether a description fires on the requests it should and stays quiet on the rest (`claude plugin eval`). Run it after any description change.

A skill whose effect you cannot describe as a task outcome is probably a CLAUDE.md line or a hook, not a skill.

## Checklist

- Name and frontmatter per the conventions; description trigger-first, disjoint, method-free.
- Body states goal, constraints, verification; reasons on rules; no emphasis markers; one example.
- Sub-files linked one hop from the body; `check-skills.sh` passes.
- Symlink added or removed; `CLAUDE.md` counts updated.
- Tested: a trigger run for the description, an `eval/` pair for the behaviour; the observed gap and the result noted in the commit message.
