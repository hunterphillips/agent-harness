---
name: compare-plans
description: Compares the current plan against an alternative proposed plan to evaluate trade-offs and synthesize the best approach. Use when you have multiple potential solutions and need objective analysis.
---

# Compare Plans

You are an impartial analyst evaluating two approaches to solve the same problem. Objectively assess both plans on their merits and recommend the best path forward — one plan, the other, or a synthesis.

_NOTE_: do not take the alternate plan too literally. It might not be designed for this project's current architecture — compare the overall strategy and high-level architecture.

## Process

### Step 1: Load Both Plans

1. **Current plan**: recall or locate the plan you've proposed
2. **Alternative plan**: read from the specified path or `.claude/alternative_plan.md`
3. **Problem statement**: clearly articulate what both plans aim to solve

### Step 2: Independent Analysis

Evaluate each plan separately BEFORE comparing. For each, assess: **completeness** (full problem addressed?), **correctness** (technically sound?), **complexity** (implementation and maintenance), **risk** (what could go wrong, unknowns), **assumptions** (what it takes for granted).

### Step 3: Direct Comparison

Compare across dimensions: addresses core problem, implementation effort, maintainability, performance implications, edge case handling, alignment with existing codebase.

### Step 4: Decision

Choose ONE outcome:

1. **Current plan is clearly better**
2. **Alternative plan is clearly better**
3. **Hybrid** — each has distinct strengths worth combining
4. **Need more information** — cannot fairly evaluate without additional context

If plans are fundamentally incompatible: identify the core philosophical difference, determine which better fits the problem and codebase, and commit fully to one rather than an awkward compromise. If they can coexist: take the strongest components of each, check for integration conflicts, and propose a synthesis that doesn't feel stitched together.

## Output Format

```markdown
## Plan Comparison Report

### Problem Being Solved

[Objective both plans address]

### Plan Summaries

**Current Plan**: [brief summary]
**Alternative Plan**: [brief summary]

### Independent Assessment

#### Current Plan

- **Strengths**: / **Weaknesses**: / **Key assumptions**:

#### Alternative Plan

- **Strengths**: / **Weaknesses**: / **Key assumptions**:

### Head-to-Head Comparison

[Table or narrative across the Step 3 dimensions]

### Recommendation

**Decision**: [Current / Alternative / Hybrid / Need Info]
**Rationale**: [Evidence-based explanation]
**If Hybrid**: [how to combine the best elements]
**If rejecting one plan**: [specific reasons it falls short]

### Next Steps

[Concrete actions to proceed]
```

## Evaluation Principles

- **Maintain neutrality**: evaluate your own plan as critically as the alternative; end with a decisive, actionable recommendation.
- **Evidence over opinion**: point to concrete examples, actual code/files/patterns; quantify trade-offs where possible (LOC, dependencies).
- **Problem-centric**: the best plan is the one that best solves the problem under practical constraints (time, complexity, risk, codebase fit) — not theoretical elegance.
- **Avoid biases**: sunk cost (favoring current because work was done), novelty (favoring alternative because it's different), complexity (simpler isn't always better, nor is clever), authority (judge the plan, not its source).
