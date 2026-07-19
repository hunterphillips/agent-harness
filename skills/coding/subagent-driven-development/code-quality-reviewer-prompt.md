# Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

**Controller steps** (do these yourself — do not ask the subagent to open files):

1. Read the reviewer template at `../requesting-code-review/code-reviewer.md` (path is relative
   to *this skill's* directory — you, the controller, resolve it; a dispatched subagent has no
   notion of the skill dir and cannot).
2. Fill its placeholders:
   - `{DESCRIPTION}` — task summary, from the implementer's report
   - `{PLAN_OR_REQUIREMENTS}` — Task N from [plan-file]
   - `{BASE_SHA}` — commit before the task
   - `{HEAD_SHA}` — current commit
3. Dispatch with the **Agent** tool (`subagent_type: general-purpose`), pasting the filled-in
   template as the `prompt`. The subagent receives the full reviewer instructions inline and
   never needs the template path itself.

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment
