# Triage

Classify one issue and decide whether an agent may implement it unattended. Input: an issue number (GitHub mode) or a ticket path (local mode). Output: exactly one status label and one comment. Triage never fixes anything, never pushes, never opens a PR.

Runs locally when the user asks for an issue to be triaged, and headless as the cloud triage job (`/harness:coding` with "route to triage" and the issue number). Both follow the same steps; the headless run has only the repo and the issue.

## Steps

1. **Read the issue and every comment.** Separate what was *observed* (error text, steps, screenshots, versions) from what the reporter *concluded* (where the bug is, what the fix is). The hypothesis is a lead, not a finding. If the issue already carries a triage label and nothing was added since the last triage comment, stop: it is done.
2. **Classify** as one of: `bug` (existing behavior is wrong), `feature` (new behavior), `question` (needs an answer, not a change), `chore` (dependency, config, docs).
3. **Inspect only the relevant code.** Grep for the error text, the command, or the component named; read the files it lands in; for a wide search, dispatch `codebase-locator`. Stop as soon as the classification and the gate can be answered. Do not attempt a fix, do not run the whole test suite, do not read the codebase for its own sake.
4. **Run the gate** (every kind except `question`). Every check must pass:
   1. The issue asks for a definite change: a bug fix, a chore (docs, README, CLAUDE.md, config, a dependency bump), or a feature whose behavior the issue spells out. Not a preference to explore or an open design choice.
   2. What "right" means is settled: for a bug, current behavior contradicts the docs, a spec, an error message, or crashes; for anything else, the issue states the outcome, not leaves it to taste.
   3. Where the change goes is known with at least medium confidence: for a bug, the root cause (file and mechanism); for anything else, the files or module that change.
   4. There is one reasonable definition of done that a reviewer would accept without discussion.
   5. It touches nothing in secrets, auth, billing or payments, or data integrity (migrations, deletes, money).
   6. It is localized: a few files in one module, no cross-cutting refactor, no public interface change.
   7. It is small: one agent run can do it, with a test when the change is behavior (docs and config need none).
   Any doubt on any check is a fail. The default is not `ready-for-agent`.
5. **Label and comment**, per `../to-issues/tracker-conventions.md`:
   - Gate passed → `ready-for-agent`. Comment: the root cause (bug) or the change and where it goes (anything else) in one sentence with the file, the definition of done, and the test that should prove it, if any. This is what the implementing run reads first.
   - Failed the gate → `ready-for-human`. Comment: classification and the one sentence that says why it needs a person (which check failed, or what decision is required).
   - Missing a reproduction, version, or the expected behavior → `needs-info`. Comment: at most three questions, each answerable in a line.
   - Blocked on an external event → `wait`. Comment: what it waits on.
   - Question → answer it in the comment if the code answers it, then `ready-for-human` so the reporter closes it or turns it into a request.
   Remove `needs-triage` and any other status label; one status label per issue. GitHub mode: `gh issue edit <n> --add-label <x> --remove-label needs-triage` and `gh issue comment <n> --body-file -`. Local mode: set the `Status:` line and append under `## Comments`.

## Comment shape

```
**Triage:** bug · ready-for-agent
Root cause: `src/sync/retry.ts` retries on HTTP 401, so an expired token loops until the job's timeout.
Done when: a 401 aborts the run with the token error surfaced once; regression test covers the 401 path.
```

Keep it to that shape and length. No restatement of the issue, no options, no hedging paragraphs.
