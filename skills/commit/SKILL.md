---
name: commit
description: Create git commits for session changes with clear, atomic messages and no Claude attribution. Default mode presents the plan and asks approval first; pass "auto" to commit without confirmation (CI/automated runs).
argument-hint: [auto (optional) — skip confirmation for automated runs]
---

# Commit Changes

You are tasked with creating git commits for the changes made during this session.

**Mode:** If the user passed `auto`, run autonomously — skip the confirmation step and never stop to ask for feedback. Otherwise, present your plan and wait for approval before committing.

## Process:

1. **Think about what changed:**
   - Review the conversation history and understand what was accomplished
   - Run `git status` to see current changes
   - Run `git diff` to understand the modifications
   - Consider whether changes should be one commit or multiple logical commits

2. **Plan your commit(s):**
   - Identify which files belong together
   - Draft clear, descriptive commit messages
   - Use imperative mood in commit messages
   - Focus on why the changes were made, not just what

3. **Present your plan to the user** _(default mode only — skip in `auto` mode)_:
   - List the files you plan to add for each commit
   - Show the commit message(s) you'll use
   - Ask: "I plan to create [N] commit(s) with these changes. Shall I proceed?"

4. **Execute:**
   - Use `git add` with specific files (never use `-A` or `.`)
   - Never commit the `thoughts/` directory or anything inside it!
   - Never commit dummy files, test scripts, or other files which you created or which appear to have been created but which were not part of your changes or directly caused by them (e.g. generated code)
   - Create commits with your planned messages until all changes are committed with `git commit -m`
   - Show the result with `git log --oneline -n [number]`

## Important:

- **NEVER add co-author information or Claude attribution**
- Commits should be authored solely by the user
- Do not include any "Generated with Claude" messages
- Do not add "Co-Authored-By" lines
- Write commit messages as if the user wrote them

## Remember:

- You have the full context of what was done in this session
- Group related changes together
- Keep commits focused and atomic when possible
- The user trusts your judgment - they asked you to commit
