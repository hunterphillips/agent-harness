---
name: research-codebase
description: Research codebase comprehensively using parallel sub-agents
model: opus
---

# Research Codebase

You are tasked with conducting comprehensive research across the codebase to answer user questions by spawning parallel sub-agents and synthesizing their findings.

Shared conventions: [../create-plan/research-conventions.md](../create-plan/research-conventions.md) (file reading, agent roster, sub-task spawning).

## Initial Setup

If no research question was provided, ask for one and wait.

## Process

1. **Read any directly mentioned files first** — fully, in the main context, before spawning sub-tasks.

2. **Decompose the research question**: break it into composable research areas; think deeply about the underlying patterns, connections, and architectural implications the user might be seeking. Track sub-tasks with the task tools (TaskCreate/TaskUpdate).

3. **Spawn parallel sub-agents** per the conventions file: **codebase-locator** (WHERE), **codebase-analyzer** (HOW), **codebase-pattern-finder** (existing examples); **thoughts-locator/analyzer** for historical context; **web-search-researcher** only if explicitly requested. All agents are documentarians, not critics.

4. **Synthesize** after ALL sub-agents complete:
   - Prioritize live codebase findings as the primary source of truth; `thoughts/` is supplementary historical context.
   - Connect findings across components; include specific `file:line` references.
   - Answer the user's question with concrete evidence.

5. **Write the research document** to `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md` (date, ticket number if any, kebab-case topic — e.g. `2025-01-08-authentication-flow.md`). Gather real metadata first (commit hash, branch, repo) — never write placeholder values:

   ```markdown
   ---
   date: [ISO date/time with timezone]
   researcher: [name]
   git_commit: [hash]
   branch: [branch]
   repository: [repo]
   topic: "[User's question]"
   tags: [research, codebase, relevant-component-names]
   status: complete
   last_updated: [YYYY-MM-DD]
   last_updated_by: [name]
   ---

   # Research: [User's Question]

   ## Research Question
   [Original query]

   ## Summary
   [High-level findings answering the question]

   ## Detailed Findings
   ### [Component/Area]
   - Finding with reference ([file.ext:line](link))
   - Connections and implementation details

   ## Code References
   - `path/to/file.py:123` — what's there

   ## Architecture Insights
   [Patterns, conventions, design decisions discovered]

   ## Historical Context (from thoughts/)
   [Relevant insights with thoughts/ references]

   ## Related Research
   [Links to other docs in thoughts/shared/research/]

   ## Open Questions
   [Areas needing further investigation]
   ```

6. **GitHub permalinks (if applicable)**: if on a pushed branch/main (`git branch --show-current`, `git status`), get repo info via `gh repo view --json owner,name` and replace local references with `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.

7. **Present** a concise summary with key file references; ask about follow-ups.

8. **Follow-ups**: append to the same document under `## Follow-up Research [timestamp]`; update `last_updated`, `last_updated_by`, and add `last_updated_note`; spawn new sub-agents as needed.

## Important Notes

- Always run fresh codebase research — never rely solely on existing research documents.
- Keep the main agent focused on synthesis, not deep file reading; encourage sub-agents to find usage examples, not just definitions.
- Research documents should be self-contained, with temporal context and consistent snake_case frontmatter.
- Explore all of `thoughts/`, not just the research subdirectory.
- **Path handling**: `thoughts/searchable/` contains hard links for searching — when documenting, strip ONLY the `searchable/` segment and preserve everything else (e.g. `thoughts/searchable/shared/prs/123.md` → `thoughts/shared/prs/123.md`). Never swap personal vs shared subdirectories.
