# Architecture Audit

Find the structural problems in a project whose owner does not read its code. Agent-written code erodes through duplication, rising complexity, swallowed errors, weak tests and import cycles, and this audit is how that gets noticed. `metrics.py` measures; you read what the measurements point at and judge. The audit covers the project root unless the user names a directory.

A finding names each file a fix would change, the evidence (a number, command output, or the code itself), and what goes wrong because of it. Anything short of that is not reported. A healthy codebase gets a short report.

## Measure

`metrics.py` sits in the same directory as this file. Run it with `python3` by its absolute path, built from the path you read this file from, because a skill-relative path does not resolve from the project. Run it from the project root. It needs git, `uvx` and `npx`, runs pinned tool versions, and writes nothing into the project. The audit changes no project file outside the test probe, because the owner may have uncommitted work and the probe is the only edit with a restore step; a gap the script reports is reported, not filled by installing anything. Snapshot output and scratch files go in a directory made with `mktemp -d`, not a fixed path, so one audit cannot read or overwrite another's files.

With a `thoughts/shared/` directory, the history lives in `thoughts/shared/audits/metrics.jsonl`:

1. If the history file does not exist, create `thoughts/shared/audits/` and run `metrics.py --backfill 90 --append thoughts/shared/audits/metrics.jsonl`. It measures three past commits, so the first audit has something to compare with.
2. Run `metrics.py --append thoughts/shared/audits/metrics.jsonl` for this audit's snapshot.
3. Run `metrics.py --compare thoughts/shared/audits/metrics.jsonl` for the change since the previous snapshot.

Without `thoughts/shared/`, run `metrics.py` alone and say the report has no comparison.

Reading the snapshot:

- `metrics` holds the counts and `details` the locations behind them. The candidate lists (`empty_catch_candidates`, `skipped_tests`, `test_files_without_assertions`, `hotspots`, `clones`) are places to read, not findings: they come from lexical matches and rankings, and only the code says whether a match is a defect.
- `hotspots` ranks production files by commits in the 90 days before the snapshot times summed cyclomatic complexity.
- A null metric was not measured, which is different from zero. Report it as not measured, with the tool's `skipped` reason in the coverage part of the report.
- `tools.<tool>.skipped` names partial coverage: source files outside every package, and the packages where a tool was incomplete. `packages[].<tool>.skipped` gives each package's reason; for madge that includes imports it could not resolve, whose edges are missing, so a cycle through them goes unseen.
- knip runs only in a package whose `node_modules` exists, and its counts include files the script treats as generated. It loads and executes the project's own configuration files, so ask before auditing a repository the user does not trust.
- On a repository younger than 90 days, backfill compresses its points into the repository's history; `backfill.span_days` is the real span, and the change column may cover days rather than months.
- History snapshots carry no cycle or unused-code fields, and a metric is not comparable across a change of tool version or `metrics_version`. `--compare` lists these under `not_comparable`; the report says the metric is not comparable instead of reporting a change.

## Investigate

Start with the hotspots, then the clones, the catch and test candidates, and the cycles. Generated files are outside the audit (`details.generated_files` lists the first 50, and the rest match the same directories and header comments), because their content belongs to the generator.

Then read past the numbers: the entry points, and anything `CONTEXT.md` or `docs/adr/` says the code must do. The metrics miss problems no tool counts, such as a module nothing reaches, a module everything imports, or UI code that queries the database directly. Use `codebase-analyzer` when a data flow needs tracing.

Code that contradicts an ADR is a finding. A finding whose fix would reverse an ADR says so, so the owner decides with the decision in view.

## Test probe

A probe checks whether a hotspot's tests notice a broken behaviour. Run it only on a clean working tree, so restoring the file cannot discard anyone's work, and on at most three hotspots that have tests:

1. Run the module's tests. Continue only if they pass.
2. Change one line so that behaviour the module's callers rely on is different.
3. Run the same command. Record the mutation, the command, and both results.
4. Restore the file with `git checkout -- <file>`.

Tests that still pass mark a place where coverage may be missing; report it with the mutation shown. A probe that could not run is reported as not run, with the reason: no clean tree, no runnable tests, or a failing baseline.

## Severity

A metric's size does not set severity; consequence and reach do, and a history of forced changes is evidence of reach.

| Severity | Criteria |
| --- | --- |
| Critical | Wrong behaviour now, or an error swallowed where data is written or identity is checked |
| High | A defect or design problem on a path many features pass through, or one that has already forced repeated changes |
| Medium | A real problem confined to one area; a surviving test probe on a hotspot |
| Low | A real problem in code that rarely changes and few things depend on |

## Report

Write the report to `thoughts/shared/audits/YYYY-MM-DD-audit.md`, or give it as your reply when there is no `thoughts/shared/`. Omit any section with nothing in it.

```markdown
# Architecture audit: <project>, YYYY-MM-DD

<Overall health in one line.>

## Metrics

| Metric | Value | Change since <previous snapshot date> |
| --- | --- | --- |
| functions_over_ccn_15 | 4 | +1 |
| unused_files | not measured | not comparable: knip did not run |

## Coverage

- <tool>: <files analyzed>; skipped: <reason from the snapshot>

## Findings

### Critical

1. `<path>:<line>`: <evidence>. <What goes wrong because of it.>

### High

### Medium

### Low

## Test probes

- `<path>`: <mutation>; `<command>`; before: <result>; after: <result>.

## Recommendations

- <An action, such as "extract X from Y into Z".>
```

## Restructuring

Recommend restructuring only for a concrete symptom the findings show, such as simple changes touching many files or a cycle that blocks testing, and only where tests exist to verify each move, because a structure that causes no problem is not worth the churn of moving it. Migrate one module at a time, with the tests run after each move.
