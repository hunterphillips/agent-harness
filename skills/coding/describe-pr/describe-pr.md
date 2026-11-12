# Generate PR Description

Write the pull request description, following the repository's template, for a reader deciding whether to merge.

## Steps to follow:

1. **Read the PR description template:**
   - First, check if `thoughts/shared/pr_description.md` exists
   - If it doesn't exist, check for a repo-standard template (`.github/PULL_REQUEST_TEMPLATE.md`); otherwise inform the user and offer to create a template at `thoughts/shared/pr_description.md`
   - Read the template carefully to understand all sections and requirements


2. **Identify the PR to describe:**
   - Check if the current branch has an associated PR: `gh pr view --json url,number,title,state 2>/dev/null`
   - If no PR exists for the current branch, or if on main/master, list open PRs: `gh pr list --limit 10 --json number,title,headRefName,author`
   - Ask the user which PR they want to describe

3. **Check for existing description:**
   - Check if `thoughts/shared/prs/{number}_description.md` already exists
   - If it exists, read it and inform the user you'll be updating it
   - Consider what has changed since the last description was written

4. **Gather comprehensive PR information:**
   - Get the full PR diff: `gh pr diff {number}`
   - If you get an error about no default remote repository, instruct the user to run `gh repo set-default` and select the appropriate repository
   - Get commit history: `gh pr view {number} --json commits`
   - Review the base branch: `gh pr view {number} --json baseRefName`
   - Get PR metadata: `gh pr view {number} --json url,title,number,state`

5. **Read the diff**, and the files it references that it doesn't show. The description needs: what changed and why, what a user sees differently, and any breaking change or migration step.

6. **Handle verification requirements:**
   - Look for any checklist items in the "How to verify it" section of the template
   - For each verification step:
     - If it's a command you can run (like `make check test`, `npm test`, etc.), run it
     - If it passes, mark the checkbox as checked: `- [x]`
     - If it fails, keep it unchecked and note what failed: `- [ ]` with explanation
     - If it requires manual testing (UI interactions, external services), leave unchecked and note for user
   - Document any verification steps you couldn't complete

7. **Write the description** section by section from the template: the problem solved, the change made, user impact where there is any, technical detail where the template asks, a changelog entry. Every checklist item is checked or explained.

8. **Save the description:**
   - Write the completed description to `thoughts/shared/prs/{number}_description.md`
   - Show the user the generated description

9. **Update the PR:**
   - Update the PR description directly: `gh pr edit {number} --body-file thoughts/shared/prs/{number}_description.md`
   - Confirm the update was successful
   - If any verification steps remain unchecked, remind the user to complete them before merging

## Notes
- Always read the local template; repositories differ.
- Breaking changes and migration notes go near the top.
- Say which verification steps still need manual testing.
