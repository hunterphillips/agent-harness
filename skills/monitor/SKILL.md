---
name: monitor
description: Headless only. Runs as /harness:monitor inside the factory's monitor job when an enrolled repo's workflow run fails; never invoke in an interactive session.
disable-model-invocation: true
---

# Monitor

One failed workflow run in. One deduplicated issue out, plus a reviewed fix PR when the gate passes, merged when the PR proves the fix. Runs unattended on a GitHub Actions runner with the repo checked out at the default branch, `gh` authenticated, and these inputs in the prompt: repository, workflow name, run id and URL, a JSON file of run metadata, and a text file with the failed jobs' logs.

Run everything in the foreground: the session ends when you end your turn, and backgrounded work dies with it. Never read, print, or write secrets: no `env`, no `cat` of credential files, no token values in issues or PRs. A failure whose cause is a token, credential, or permission always ends as an issue naming the single human action.

## Steps

1. **Normalize.** Read the run metadata and the failed logs. Write a five-line failure report for yourself: workflow, failed job and step, the first error line (the first line that names an error, exception, non-zero exit, or assertion; skip GitHub's own `##[error]Process completed` line if a better one exists above it), the head branch and SHA, the run URL.
2. **Signature.** `<workflow name> :: <first error line>` with every run of digits, every timestamp, every hex hash, and every absolute path prefix removed, lowercased, trimmed to 120 characters. Compute it with `sed`; do not paraphrase.
3. **Dedupe.** `gh issue list --label monitor --state open --limit 100 --json number,body`. Every monitor issue carries `<!-- monitor-signature: ... -->` in its body. If one matches this signature exactly: `gh issue comment <n> --body "Occurred again: <run url> (<date>, <head sha>)"` and stop. Nothing else.
4. **Diagnose, read-only and bounded.** The failed step is the feedback loop and the logs are the reproduction; do not build another one. Rank three hypotheses, each with the prediction it makes, and check the top two against the code with Grep and Read. If one command reproduces the failure locally in under two minutes (a test file, a lint), run it once; otherwise do not run the project. No instrumentation, no edits during diagnosis. Stop after ten minutes of effort with the best hypothesis you have and say the confidence.
5. **Gate.** Pass only if every check holds; any doubt fails.
   1. The cause is in this repository's code or config, not in a secret, token, permission, quota, external service, or runner.
   2. The behavior is objectively wrong (test contradicts code, build breaks, lint rule violated), not a flaky or environmental failure.
   3. The root cause is located with at least medium confidence: file and mechanism.
   4. One definition of done a reviewer would accept without discussion.
   5. Nothing in auth, billing, payments, migrations, deletes, or data integrity.
   6. Localized: a few files in one module, no interface change.
   7. Small: fixable in this run with a regression test.
6. **Open the issue** (always, pass or fail, so later occurrences have an anchor). Title `[monitor] <workflow>: <cause in six words>`. Label `monitor`. Body: the cause in one sentence; the run URL; the failed job and first error line in a code block; the single human action if the gate failed (rotate which credential where, bump which quota, re-run after which outage), on a line that starts with an @-mention of the repo owner (`gh repo view --json owner --jq .owner.login`) — the owner reads mentions and nothing else; the ranked hypotheses when confidence is below high; and `<!-- monitor-signature: <signature> -->` on its own line at the end. `gh issue create --label monitor --title ... --body-file -`.
7. **Gate passed: fix it.** Branch `claude/fix-<issue number>` from the default branch. If that branch already exists on the remote, another run owns it: comment on the issue and stop. Make the smallest change that fixes the cause, add or extend a test that fails before and passes after, run that test plus the repo's lint if one is declared. Then review it: read `../coding/requesting-code-review/code-reviewer.md` (relative to this skill directory), fill its placeholders (description = the cause and fix; requirements = the issue; base = the default branch SHA; head = current SHA), dispatch it with the Agent tool on `opus`, and fix every Critical and Important finding. Commit with a message that names the cause, push, then `gh pr create --draft --title "<cause>" --body "Closes #<issue>. <two sentences: cause, fix, how verified>. Review: <one line>"`. Comment on the issue with the PR link.
8. **Merge when the PR proves the fix.** The job prompt says whether auto-merge is allowed. If it is, merge only when all hold: the review left no unresolved Critical or Important findings; `gh pr checks <pr> --watch --fail-fast` passed; and the workflow that failed ran on this PR and passed. If that workflow does not run on pull requests (a schedule, a deploy, a push-only job), the PR cannot prove the fix: leave the draft and say so in an issue comment that @-mentions the repo owner. No other monitor comment mentions anyone, including "Occurred again". To merge: `gh pr ready <pr>` and `gh pr merge <pr> --squash --delete-branch`, then comment on the issue. Never push to the default branch directly.
9. **Gate failed: stop** after the issue. Do not push, do not open a PR.

## Report

Final message: the signature, whether it deduplicated, the issue or PR URL, and the gate result with the failing check number. Nothing else.
