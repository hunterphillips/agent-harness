---
name: onboard
description: Get familiar with the codebase by exploring structure, patterns, and documentation. Use when starting fresh on a project without prior context.
argument-hint: [focus area (optional)]
---

# Onboard

Build a working model of a project you have not seen before, then report it so the user can hand you work. The project's `CLAUDE.md` is already loaded; treat its claims as the first thing to verify, not the last.

## What to learn

1. **Purpose**: what the project does and for whom.
2. **Shape**: the directories that matter, entry points, where the core logic and the tests live, how configuration works.
3. **Conventions**: naming, module layout, error handling, test style, lint and format config. Let the code show you; don't assume from the stack.
4. **Workflow**: how to install, run, build, test, and what CI runs (`.github/workflows/`, `Makefile`, `package.json` scripts, `justfile`, or their equivalents).
5. **State**: `git status`, the current branch, and the last ten commits. If `thoughts/shared/lanes/` exists, read each lane's `handoff.md`; that is where in-flight work is recorded.

Read documentation first (`README.md`, `CONTRIBUTING.md`, `docs/`, architecture notes, the dependency manifest). It usually answers half of the above and tells you which claims to check.

## How much to explore

Scale to the repo. A small project is a few `ls` and file reads done in the main session. For a large one, use the `codebase-locator`, `codebase-analyzer`, and `codebase-pattern-finder` agents in parallel to map structure and conventions, then verify what they report by reading the key files yourself. Don't spawn agents for a repo you can read directly.

If a focus area was given (`backend`, `frontend`, `tests`, or a directory), go deeper there and lighter elsewhere.

## Report

Write the summary for someone who will give you a task next: purpose and stack; the structure, as a short list of directories with what each holds; the conventions to follow; how to run and verify; and anything that looked wrong or out of date (a doc claim the tree contradicts, a stale handoff, uncommitted work). End by asking what to work on.

Business context, undocumented history, and planned direction are things only the user knows; ask rather than guess.
