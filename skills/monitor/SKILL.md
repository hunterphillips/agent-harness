---
name: monitor
description: Headless only. Runs as /harness:monitor inside the factory's monitor job when an enrolled repo's workflow run fails on its default branch, a schedule, or a dispatch (never a pull request); diagnoses the failure and files one deduplicated issue, which the implement job fixes when the gate passes. Never invoke in an interactive session.
disable-model-invocation: true
---

# Monitor

One failed workflow run in, one deduplicated issue out. Diagnosis only: when the gate passes on a new issue, the workflow hands that issue to the implement job, which builds, reviews, checks, and merges the fix. Runs unattended on a GitHub Actions runner with the repo checked out at the default branch, `gh` authenticated, and these inputs in the prompt: repository, workflow name, run id and URL, a JSON file of run metadata, and a text file with the failed jobs' logs.

Run everything in the foreground: the session ends when you end your turn, and backgrounded work dies with it. Never read, print, or write secrets: no `env`, no `cat` of credential files, no token values in issues. Never edit files, commit, push, open a pull request, or change labels; the workflow owns every status label. A failure whose cause is a token, credential, or permission always ends as an issue naming the single human action.

## Steps

1. **Normalize.** Read the run metadata and the failed logs. Write a six-line failure report for yourself: workflow, failed job and step, the failing test file (the repo-relative path of the test file the first failure names, or `none` when no test file is named), the first error line (the first line that names an error, exception, non-zero exit, or assertion; skip GitHub's own `##[error]Process completed` line if a better one exists above it), the head branch and SHA, the run URL.
2. **Signature.** `<workflow name> :: <test file> :: <first error line>`. In the first error line, remove every run of digits, every timestamp, every hex hash, and every absolute path prefix; then lowercase the whole signature and trim it to 160 characters. Compute it with `sed`; do not paraphrase.
3. **Dedupe.** `gh issue list --label monitor --state open --limit 100 --json number,body`. Every monitor issue carries `<!-- monitor-signature: ... -->` in its body. If one matches this signature exactly: `gh issue comment <n> --body "Occurred again: <run url> (<date>, <head sha>)"` and stop. Nothing else.
4. **Diagnose, read-only and bounded.** The failed step is the feedback loop and the logs are the reproduction; do not build another one. Form the hypotheses the evidence supports, each with the prediction it makes, and check the strongest against the code with Grep and Read. If one command reproduces the failure locally in under two minutes (a test file, a lint), run it once; otherwise do not run the project. No instrumentation, no edits. The diagnosis is bounded: a handful of reads and at most that one command; then report the best hypothesis you have and say the confidence.
5. **Gate.** Pass only if every check holds; any doubt fails.
   1. The cause is in this repository's code or config, not in a secret, token, permission, quota, external service, or runner.
   2. The behavior is objectively wrong (test contradicts code, build breaks, lint rule violated), not a flaky or environmental failure.
   3. The root cause is located with at least medium confidence: file and mechanism.
   4. One definition of done a reviewer would accept without discussion.
   5. Nothing in auth, billing, payments, migrations, deletes, or data integrity.
   6. Localized: a few files in one module, no interface change.
   7. Small: one implement run can fix it, with a regression test.
6. **Open the issue** (always, pass or fail, so later occurrences have an anchor). Title `[monitor] <workflow>: <cause in six words>`. Label `monitor`. When the gate passed, the issue is the implementing run's whole specification, so its body leads with this block:

   ```
   **Monitor:** gate passed
   Root cause: `app/test/browser/hub.spec.mjs:483` expects the one-line export the client build no longer writes; the build's output is correct.
   Failing command: `npx playwright test test/browser/hub.spec.mjs` (from `app/`)
   Done when: the test matches the export the build writes; regression test: that test, failing before the fix and passing after.
   ```

   Then, pass or fail: the run URL; the failed job and first error line in a code block; when the gate failed, `**Monitor:** gate failed (check <n>)` and the single human action (rotate which credential where, bump which quota, re-run after which outage) on a line that starts with an @-mention of the repo owner (`gh repo view --json owner --jq .owner.login`), since the owner reads mentions and nothing else; the ranked hypotheses when confidence is below high; and `<!-- monitor-signature: <signature> -->` on its own line at the end. No other monitor text mentions anyone, including "Occurred again". `gh issue create --label monitor --title ... --body-file -`.

## Report

Return the structured output the job asks for: `issue` is the number of the issue opened, or the one deduplicated against; `deduplicated` says which; `fix` is true only when the gate passed and the issue is new; `reason` is one sentence naming the signature and the gate result, with the failing check number when it failed.
