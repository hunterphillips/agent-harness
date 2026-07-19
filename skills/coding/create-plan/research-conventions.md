# Research & Sub-agent Conventions

Shared conventions for the plan/research skill family (`create-plan`, `iterate-plan`, `research-codebase`).

## Reading files

- Read any user-mentioned file FULLY (no limit/offset) in the main context **before** spawning sub-tasks. Never read mentioned files partially.
- After research sub-tasks complete, read all files they identified as relevant fully into the main context before synthesizing.

## Agent roster

| Agent | Use for |
| --- | --- |
| **codebase-locator** | finding WHERE files and components live |
| **codebase-analyzer** | understanding HOW specific code works |
| **codebase-pattern-finder** | finding similar existing patterns to model after |
| **thoughts-locator** | finding related research, plans, or decisions in `thoughts/` |
| **thoughts-analyzer** | extracting insights from specific thoughts documents |
| **web-search-researcher** | external docs — only if the user explicitly asks; have it return links and include them in the final output |

Agents are **documentarians, not critics** — they describe what exists without critiquing it or suggesting improvements.

## Spawning sub-tasks

- Spawn independent tasks in parallel (one message), each focused on a single area.
- Be EXTREMELY specific about directories — include full path context in prompts.
- Request specific `file:line` references in responses; sub-tasks are read-only.
- Wait for ALL sub-tasks to complete before synthesizing.
- Verify results: if findings seem off, spawn follow-ups and cross-check against the actual codebase.
- For multi-task research, track progress with the task tools (TaskCreate/TaskUpdate).

## Success criteria (plans)

Always separate into two categories:

1. **Automated Verification** — runnable by execution agents: test/lint/typecheck commands (prefer `make` targets when available), files that should exist, compilation.
2. **Manual Verification** — requires human testing: UI/UX functionality, performance under real conditions, hard-to-automate edge cases, user acceptance.

Format example lives in [plan-template.md](./plan-template.md).
