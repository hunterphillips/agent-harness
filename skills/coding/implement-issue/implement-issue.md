# Implement Issue

Turn one `ready-for-agent` issue into a reviewed PR, merged when the owner asked for the work and the review and checks pass, without a human in the loop. Headless by default (the factory's implement job runs `/harness:coding` with "route to implement-issue" and the issue number); a local session can run it the same way when told to work an issue end to end.

The issue is the whole specification. Cloud runs never see `thoughts/`, plans, or handoffs. If the issue is not self-contained, stop at step 2 and say what is missing.

## Steps

1. **Back-pressure.** `gh pr list --state open --json headRefName --jq '[.[] | select(.headRefName | startswith("claude/"))] | length'`. If 3 or more, comment on the issue ("queue full: N open claude/ PRs; will retry when one merges") and stop.
2. **Read the issue and every comment**, the triage comment first: it names the root cause, the definition of done, and the test that should prove it. Write a five-line plan (what changes, where, the test, what stays untouched, how you will verify) and a numbered acceptance list. These become the PR body; keep them in a scratch file outside the repo (`$RUNNER_TEMP` or `/tmp`).
3. **Claim.** Branch `claude/issue-<n>` from the default branch and push it immediately. If the push is rejected because the branch exists, another run owns it: stop without comment. Then `gh issue edit <n> --add-label in-progress --remove-label ready-for-agent`.
4. **Implement under the tdd rules.** Read `../tdd/tdd.md` (relative to this skill directory; you are the controller and can resolve it) and apply its core rules: failing test first, minimal change, no speculative generality. Conservative coverage: the regression test the triage comment asked for, plus what the change makes essential. Commit in small steps with messages that name the behavior.
5. **Run the repo's checks.** Whatever the repo declares (`package.json` scripts, `Makefile`, `pyproject`, CI config): the test command, then the lint command. Fix what fails. If a check cannot run on the runner, say so in the PR body rather than skipping silently.
6. **Review before opening.** Read `../requesting-code-review/code-reviewer.md`, fill its placeholders (description = the plan; requirements = the issue and triage comment; base = the default branch SHA; head = current SHA), and dispatch it with the Agent tool on `opus`. Fix every Critical and Important finding, re-run the checks, commit. Minor findings go in the PR body.
7. **Open the draft PR.** `gh pr create --draft --base <default> --head claude/issue-<n>`. Title: the change in one line. Body: `Closes #<n>`, the five-line plan, the acceptance list with each item checked or explained, a "Review" section with the reviewer's summary and what was fixed, and how the checks were run. Then `gh issue edit <n> --remove-label in-progress` and comment on the issue with the PR link.
8. **Merge, when allowed.** The job prompt says whether auto-merge is allowed; that line is decided by the workflow from who wrote the issue, never by you. If it is not allowed, stop here with the draft. If it is allowed, merge only when all three hold: the review left no unresolved Critical or Important findings; `gh pr checks <pr> --watch --fail-fast` passed (a repo with no checks configured counts as passing, since step 5 already ran its checks); and nothing in this run hit the stop rule below. Then `gh pr ready <pr>` and `gh pr merge <pr> --squash --delete-branch`, and comment on the issue that it merged. If any condition fails, leave the draft, comment on the issue with which one, and relabel `ready-for-human`.
9. **Never push to the default branch directly.** Never touch secrets, auth, billing, or migrations; if the work turns out to need them, stop, comment on the issue with why, and relabel `ready-for-human`. A run that stops here never merges.

## Report

Final message: the PR URL, the acceptance list with results, the reviewer's Critical/Important count before and after fixes, and any check that could not run.
