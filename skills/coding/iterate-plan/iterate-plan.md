# Iterate Implementation Plan

You are tasked with updating existing implementation plans based on user feedback. Be skeptical, surgical, and ensure changes are grounded in actual codebase reality.

Shared conventions: [../create-plan/research-conventions.md](../create-plan/research-conventions.md). Plan format: [../create-plan/plan-template.md](../create-plan/plan-template.md).

## Input Handling

Parse the input for a plan file path (e.g., `thoughts/shared/plans/2025-10-16-feature.md`) and the requested changes.

- **No plan file** → ask which plan to update (tip: `ls -lt thoughts/shared/plans/ | head`). Wait.
- **Plan file but no feedback** → ask what changes they want (e.g., "add a phase for migration handling", "split Phase 2", "adjust scope to exclude X"). Wait.
- **Both provided** → proceed immediately.

## Step 1: Read and Understand

Read the existing plan FULLY (no limit/offset). Understand its structure, phases, scope, and success criteria. Parse exactly what the user wants added/modified/removed and whether it requires codebase research.

## Step 2: Research If Needed

**Only spawn research if the changes require new technical understanding** — don't research simple changes. Use the agent roster and spawning practices in the conventions file; read any newly identified files fully before proceeding.

## Step 3: Confirm Before Changing

```
Based on your feedback, I understand you want to:
- [Change with specific detail]

My research found:
- [Relevant pattern or constraint]

I plan to update the plan by:
1. [Specific modification]

Does this align with your intent?
```

Get confirmation before editing.

## Step 4: Update the Plan

- Make focused, surgical edits — preserve good content; no wholesale rewrites.
- Maintain the existing structure and the template's conventions: new phases follow the established pattern, scope changes update "What We're NOT Doing", approach changes update "Implementation Approach".
- Keep `file:line` references accurate; keep success criteria measurable and split into Automated vs Manual Verification (see conventions file).

## Step 5: Review

Present what changed and why, then iterate further on feedback:

```
I've updated the plan at `thoughts/shared/plans/[filename].md`

Changes made:
- [Specific change]

Would you like any further adjustments?
```

## Guidelines

- **Be skeptical**: don't blindly accept change requests that seem problematic — question vague feedback, verify technical feasibility, and point out conflicts with existing phases.
- **Be surgical**: precise edits only; research only what's necessary for the specific changes.
- **No open questions**: if a requested change raises questions, ASK or research immediately — never write unresolved questions into the plan.
- Track complex updates with the task tools (TaskCreate/TaskUpdate).
