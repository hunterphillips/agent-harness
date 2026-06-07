---
name: validate-plan
description: Validate implementation against plan, verify success criteria, identify issues
---

# Validate Plan

You are tasked with validating that an implementation plan was correctly executed — verifying all success criteria and identifying deviations or issues.

Shared conventions: [../create-plan/research-conventions.md](../create-plan/research-conventions.md) (agent roster, sub-task spawning, success-criteria categories).

## Setup

1. **Determine context**: if you were part of the implementation, review this session's work and task list, focus validation there, and be honest about shortcuts or incomplete items. If starting fresh, discover what was done through git and codebase analysis.
2. **Locate the plan**: use the provided path, or search recent commits for plan references, or ask.
3. **Gather evidence**:

   ```bash
   git log --oneline -n 20
   git diff HEAD~N..HEAD   # N covers the implementation commits
   cd $(git rev-parse --show-toplevel) && make check test
   ```

## Validation Process

### Step 1: Context Discovery (fresh sessions)

Read the plan completely, then list what should have changed: files to modify, all success criteria (automated and manual), key functionality. Spawn parallel sub-tasks per the conventions file to compare planned vs actual — e.g. schema/migration changes, code changes per affected area, test coverage and results.

### Step 2: Systematic Validation

For each phase in the plan:

1. **Completion status**: are checkmarks (`- [x]`) backed by actual code?
2. **Automated verification**: run every command from the phase's "Automated Verification" section; document pass/fail; investigate root cause of failures.
3. **Manual criteria**: list what needs human testing with clear steps.
4. **Edge cases**: were error conditions handled? Missing validations? Could this break existing functionality?

### Step 3: Validation Report

```markdown
## Validation Report: [Plan Name]

### Implementation Status

✓ Phase 1: [Name] — fully implemented
⚠️ Phase 2: [Name] — partially implemented (see issues)

### Automated Verification Results

✓ Tests pass: `make test`
✗ Linting: `make lint` (3 warnings)

### Code Review Findings

#### Matches Plan:

[What was implemented as specified]

#### Deviations from Plan:

[Differences — note which are improvements vs concerns]

#### Potential Issues:

[Bugs, missing handling, performance/regression risks]

### Manual Testing Required:

1. [Feature/integration steps for the user, as checkboxes]

### Recommendations:

[Actions before merge; missing tests; documentation]
```

## Guidelines

- **Be thorough but practical** — focus on what matters; run ALL automated checks, never skip verification commands.
- **Think critically** — question whether the implementation truly solves the problem, and whether it's maintainable long-term. Document successes as well as issues.
- Always verify: phases marked complete are actually done, tests pass, code follows existing patterns, no regressions, error handling is robust, documentation updated if needed.

## Workflow Position

`/implement-plan` → `/commit` → `/validate-plan` → `/describe-pr`

Validation works best after commits are made, so git history can show what was implemented.
