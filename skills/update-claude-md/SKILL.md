---
name: update-claude-md
description: Updates the CLAUDE.md file (if needed) for the current project based codebase analysis of recent changes and architecture implications.
---

# Update CLAUDE.md

1. Assess recent changes to the codebase.

2. Adopt the principles in `.claude/skills/write-claude-md/SKILL.md` and determine if updates are needed. Update the CLAUDE.md file as needed.

3. Check whether those same changes invalidated overlapping prose in other top-level docs — primarily `README.md`, plus any `docs/`, `CONTRIBUTING.md`, or architecture notes. Update any that drifted so they stay consistent with CLAUDE.md. For a curated/human-owned doc where the right wording is unclear, flag the stale section instead of silently rewriting it.
