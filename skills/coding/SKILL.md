---
name: coding
description: Software and development work of any kind — designing, planning, implementing, debugging, testing, reviewing, or shipping code changes. ALWAYS invoke at the start of any dev-work request — building or modifying features, weighing an implementation approach, fixing bugs or regressions, writing tests, executing plans, reviewing code or architecture, writing PR descriptions, or converting work into PRDs/tickets. Routes to the right workflow; do not start development work without invoking this skill first. Not for non-dev tasks (prose, general research, session management).
---

# Coding

Router for all software-delivery work. Pick the workflow, load it, follow it.

## Protocol (mandatory)

1. **Match**: state in one line which routing row below fits the current request.
2. **Load**: Read that workflow file NOW — before any other action, including clarifying questions.
3. **Follow**: execute the loaded workflow exactly; consult its support files as it directs.

If a workflow applies, this is not optional — do not "just do the task" from general knowledge. If the state changes mid-task (a bug surfaces during implementation, a plan turns out wrong), return here and re-route. When multiple rows apply, process comes first: design → plan → implement → review. If genuinely no row applies, say so in one line and proceed normally.

Match process weight to stakes: the delivery workflows exist for software that people depend on. Code whose whole audience is its author — one-off scripts or tooling — consider the scratch row. Judge by the code's lifespan and audience, not by which project directory you happen to be in (a research paper repo can contain a real maintained tool; an app repo can contain scratch).

## Routing table

| Conversation state                                                                                                      | Workflow                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Scratch code** — one-off scripts, data collection, throwaway UIs; only the author depends on it and its life is short | No workflow file. Write it directly: the bar is _works and is readable_, verified by running it. No tickets, tests, reviews, or formal docs unless asked or warranted. If it graduates into something maintained or user-facing, re-route below. |
| Fuzzy idea, no design yet — "I'm thinking about…", requirements unclear                                                 | [brainstorming/brainstorming.md](brainstorming/brainstorming.md)                                                                                                                                                                                 |
| Formed plan/design/decision the user wants challenged — "poke holes", "grill me", "does this make sense"                | [grill-me/grill-me.md](grill-me/grill-me.md)                                                                                                                                                                                                     |
| Design question a throwaway prototype could answer — "mock it up", "let me play with it"                                | [prototype/prototype.md](prototype/prototype.md)                                                                                                                                                                                                 |
| "How does X work" / "where is Y handled" across multiple subsystems                                                     | [research-codebase/research-codebase.md](research-codebase/research-codebase.md) †                                                                                                                                                               |
| Clear requirements, nontrivial change — needs an implementation plan before code                                        | [create-plan/create-plan.md](create-plan/create-plan.md) †                                                                                                                                                                                       |
| Existing plan needs revision (feedback, changed requirements, reality diverged)                                         | [iterate-plan/iterate-plan.md](iterate-plan/iterate-plan.md) †                                                                                                                                                                                   |
| Capture requirements for async/parallel pickup — "write a PRD", "put it on the backlog"                                 | [to-prd/to-prd.md](to-prd/to-prd.md)                                                                                                                                                                                                             |
| Break a plan/spec/PRD into independently-grabbable tickets                                                              | [to-issues/to-issues.md](to-issues/to-issues.md)                                                                                                                                                                                                 |
| Execute a plan in this session, subagent per task with two-stage review                                                 | [subagent-driven-development/subagent-driven-development.md](subagent-driven-development/subagent-driven-development.md)                                                                                                                         |
| Execute a plan directly (fresh/parallel session, phase-by-phase)                                                        | [implement-plan/implement-plan.md](implement-plan/implement-plan.md)                                                                                                                                                                             |
| Building behavior test-first — TDD, red-green-refactor, integration tests                                               | [tdd/tdd.md](tdd/tdd.md)                                                                                                                                                                                                                         |
| Something is broken/throwing/failing/flaky/slow — any bug or regression report                                          | [diagnose/diagnose.md](diagnose/diagnose.md)                                                                                                                                                                                                     |
| Work wraps up / pre-merge — structured code review                                                                      | [requesting-code-review/requesting-code-review.md](requesting-code-review/requesting-code-review.md)                                                                                                                                             |
| Planned work claims "done" — verify against the plan's success criteria                                                 | [validate-plan/validate-plan.md](validate-plan/validate-plan.md)                                                                                                                                                                                 |
| Architecture health audit — **only on explicit user request**                                                           | [architecture-audit/architecture-audit.md](architecture-audit/architecture-audit.md)                                                                                                                                                             |
| Deepening refactors, module interfaces, consolidating coupled modules                                                   | [architecture-improvement/architecture-improvement.md](architecture-improvement/architecture-improvement.md)                                                                                                                                     |
| PR being opened/updated — write the description                                                                         | [describe-pr/describe-pr.md](describe-pr/describe-pr.md)                                                                                                                                                                                         |

† High-reasoning workflow (formerly `model: opus`): prefer the most capable available model/effort for this work.

## Support files (loaded on demand by the workflows above)

- brainstorming/ — (none)
- grill-me/ — [CONTEXT-FORMAT.md](grill-me/CONTEXT-FORMAT.md), [ADR-FORMAT.md](grill-me/ADR-FORMAT.md)
- prototype/ — [LOGIC.md](prototype/LOGIC.md), [UI.md](prototype/UI.md)
- create-plan/ — [research-conventions.md](create-plan/research-conventions.md), [plan-template.md](create-plan/plan-template.md) (shared by iterate-plan, validate-plan, research-codebase)
- subagent-driven-development/ — [implementer-prompt.md](subagent-driven-development/implementer-prompt.md), [spec-reviewer-prompt.md](subagent-driven-development/spec-reviewer-prompt.md), [code-quality-reviewer-prompt.md](subagent-driven-development/code-quality-reviewer-prompt.md)
- tdd/ — [tests.md](tdd/tests.md), [mocking.md](tdd/mocking.md), [interface-design.md](tdd/interface-design.md), [refactoring.md](tdd/refactoring.md)
- diagnose/ — [scripts/hitl-loop.template.sh](diagnose/scripts/hitl-loop.template.sh)
- requesting-code-review/ — [code-reviewer.md](requesting-code-review/code-reviewer.md) (also used by subagent-driven-development's quality stage)
- to-issues/ — [tracker-conventions.md](to-issues/tracker-conventions.md) (shared by to-prd)
- architecture-improvement/ — [LANGUAGE.md](architecture-improvement/LANGUAGE.md), [DEEPENING.md](architecture-improvement/DEEPENING.md), [INTERFACE-DESIGN.md](architecture-improvement/INTERFACE-DESIGN.md), [HTML-REPORT.md](architecture-improvement/HTML-REPORT.md)

Cross-references between workflow folders use relative paths (e.g. `create-plan/plan-template.md` from this router) and resolve within this skill directory.

## Interfaces to standalone skills

These remain separate skills — invoke them as skills, not files: `commit` (finishing a branch), `dispatching-parallel-agents` (2+ independent concurrent tasks), `onboard`/`handoff`/`pickup` (session lifecycle), `write-claude-md` (after architecture-relevant changes).
