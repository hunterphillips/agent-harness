# Implementation Plan Template

Write plans to `thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`:

- `YYYY-MM-DD` — today's date
- `ENG-XXXX` — ticket number (omit if no ticket)
- `description` — brief kebab-case description

Examples: `2025-01-08-ENG-1478-parent-child-tracking.md`, `2025-01-08-improve-error-handling.md`

## Template

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:

- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep]

## Implementation Approach

[High-level strategy and reasoning]

## Phase 1: [Descriptive Name]

### Overview

[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]

**Files**: `path/to/file.ext`, `path/to/other.ext` (every file this group creates or modifies, as far as research shows)
**Depends on**: none | 1.2, Phase 1 (groups or phases whose output this one consumes)
**Changes**: [Summary of changes]

```[language]
// Specific code to add/modify
```

### Success Criteria:

#### Automated Verification:

- [ ] B1, B2: empty and error states covered: `make test-component`
- [ ] Migration applies cleanly: `make migrate`
- [ ] Unit tests pass: `make test-component`
- [ ] Type checking passes: `npm run typecheck`
- [ ] Linting passes: `make lint`
- [ ] Integration tests pass: `make test-integration`

#### Manual Verification:

- [ ] B3: loading state visible on a slow connection
- [ ] Feature works as expected when tested via UI
- [ ] Performance is acceptable under load
- [ ] Edge case handling verified manually
- [ ] No regressions in related features

`Files` and `Depends on` let the executor see which groups can run at the same time (`subagent-driven-development` groups ready, non-overlapping tasks into waves). List what research found; a shared file nobody thought of surfaces as a merge conflict at execution, not as a bug, so a best-effort list is enough. The list schedules work; it is not a fence around the implementer.

Cite the behavior invariants (`B<n>`) from the design doc or PRD on the criteria that prove them; every invariant the plan touches should appear on at least one criterion. Plans for trivial fixes have no invariants to cite.

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: [Descriptive Name]

[Similar structure with both automated and manual success criteria...]

---

## Testing Strategy

### Unit Tests:

- [What to test]
- [Key edge cases]

### Integration Tests:

- [End-to-end scenarios]

### Manual Testing Steps:

1. [Specific step to verify feature]
2. [Another verification step]
3. [Edge case to test manually]

## Performance Considerations

[Any performance implications or optimizations needed]

## Migration Notes

[If applicable, how to handle existing data/systems]

## References

- Original ticket: `thoughts/shared/tickets/eng_XXXX.md`
- Related research: `thoughts/shared/research/[relevant].md`
- Similar implementation: `[file:line]`
````
