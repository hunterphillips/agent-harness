# Capability A/B eval

This runner compares the final artifacts from the repository configuration and a customization-free control. It uses blind pairwise Codex reviews in both A/B orders. Both arms run with `--setting-sources project`, so they load project settings only and a user-level hook, setting, or output style in `~/.claude` cannot contaminate an A/B result. Coding tasks run deterministic checks before qualitative review.

The configured arm gets the repository's `skills/`, `agents/`, `output-styles/`, and `settings.json` in the workspace's `.claude/`; control runs with `--safe-mode`. The configured arm's prompt starts with `/writing` for writing tasks and `/coding` for coding and UI tasks; control's prompt has no prefix. Both arms get the same turn and budget ceilings.

Both arms get the CLI's default tool set with `--disallowedTools` removing web access and every tool that acts on the owner's account or reaches other sessions: `WebFetch`, `WebSearch`, `RemoteTrigger`, `CronCreate`, `CronDelete`, `CronList`, `PushNotification`, `ScheduleWakeup`, `DesignSync`, `Workflow`, `SendMessage`, `ListAgents`, `Monitor`, `EnterWorktree`, and `ExitWorktree`. With CLI 2.1.327 that leaves `Task` (the subagent tool), `Bash`, `Read`, `Edit`, `Write`, `NotebookEdit`, `Skill`, `ToolSearch`, `TaskStop`, and `ReportFindings`. The runs use `--dangerously-skip-permissions`, so these tools act without prompts.

The arms differ in more than skills:

- The configured arm deploys every skill in the repository, and some act on absolute paths outside the workspace, such as a note-capture skill that writes to a vault in the home directory. Nothing sandboxes that.
- The deployed `settings.json` sets `env.MAX_THINKING_TOKENS`, so only the configured arm runs with that setting.
- Both arms carry the CLI's bundled skills (`debug`, `verify`, `simplify`, `code-review`, and others) and the Skill tool, so a control record can show a `skill_calls` entry for a bundled skill.

Requires Python 3.12, `git`, an authenticated `claude` CLI, and an authenticated `codex` CLI.

```sh
# List tasks and every planned invocation; spends no tokens
python eval/run.py --battery writing --dry-run

# Smoke-test one task with one replicate
python eval/run.py --battery writing --task writing-01-rewrite-ai-draft --replicates 1

# Run a full battery (default: three replicates)
python eval/run.py --battery writing
python eval/run.py --battery coding

# Run both arms on another model (default: claude-opus-5)
python eval/run.py --battery coding --model claude-sonnet-5
```

Interrupted runs leave a fsynced journal. Continue one with `python eval/run.py --battery writing --resume YYYYMMDD-HHMMSS` using the original task selection, replicate count, and `--model`. Resume refuses a run whose fingerprint (below) differs from the current one, and names the part that changed: config tree, a task's prompt, fixture, or checks, model, CLI version, tool flags, or ceilings. It also refuses a run started before fingerprints existed, because its arms ran under other tools and prompts. A `--rejudge` run copies the model and fingerprint from its source run and resumes without the fingerprint check, because its arms are fixed and only judging resumes.

Results land in `eval/results/<timestamp>.json` and `.md`; `.meta.json` and `.records.jsonl` are recovery/audit files. The directory is gitignored. `.meta.json` holds a fingerprint of the run: hashes of the deployed `.claude/` tree and of each task's rendered prompt per arm, fixture, and checks (ignoring `.DS_Store`, `__pycache__`, and `.pyc` files), plus the model, `claude --version`, tool flags, and ceilings.

Each arm runs with `--output-format stream-json`, and its raw events are kept at `eval/results/<run-id>/<task>/<replicate>/<arm>/events.jsonl`. Each arm's journal record lists what it loaded: `slash_command`, `skill_calls` (Skill tool invocations), `skill_files_read` (paths under `.claude/skills/` in Read calls and Bash commands), `subagents` (subagent tool calls), and `tools_available` (from the session's init event). The `.md` summary shows these per arm, with each arm's tool count and the tools offered to one arm but not the other. A slash command expands into the prompt, so `/coding` alone produces no Skill call.

A replicate's verdict needs both judge orders to agree. When both agree there is no winner, the replicate is a `tie`. When a judge result is missing or the two orders disagree, it is `no_verdict`. When a coding gate decides a replicate, judging is skipped, so `correctness_scope` goes to the passing arm and every other dimension is `no_verdict`. A task's verdict is the outcome of more than half its replicates; with no majority, or no completed replicates, it is `no_verdict`.

Coding gates compare the workspace with the fixture commit, which the runner records as `refs/eval/baseline`, so unstaged, staged, committed, and amended work are judged alike. The judge's patch is taken against the same commit after `git add --intent-to-add`, so new files appear in it whether or not the arm committed them. Coding gates reject any changed file outside the task's expected set, so a `/coding` workflow that writes a planning file fails the configured arm's gate.

Each replicate can make two Claude calls and two Codex judge calls. Coding cases with one passing deterministic gate skip both judge calls. Every arm is capped at 12 turns and $2 per writing run and 40 turns and $6 per coding or UI run (writing tasks that ship a repository get the coding ceilings); these are ceilings, not estimates. A default writing battery plans 60 Claude calls and 60 judge calls, so use a one-replicate, one-task smoke test before a full run. Efficiency metrics are reported separately and never affect quality verdicts.

## UI

The `ui` battery measures fit to a product brief, visual hierarchy, distinctiveness, responsive layout, and code simplicity across a landing page, settings screen, and small data table. Each task produces one `index.html` with no installed page dependencies; Tailwind via CDN and web fonts are allowed. The judge sees the patch and file contents plus four full-page screenshots: both candidates at 1280×800 and 390×844. The PNGs are kept under `eval/results/<run-id>/<task>/<replicate>/<arm>/`; their paths are recorded in each arm's journal record.

Requires Node.js, Playwright Chromium, and the pinned eval-only packages:

```sh
npm install --prefix eval --package-lock=false
npx --prefix eval playwright-core install chromium
python3 eval/run.py --battery ui --dry-run
python3 eval/run.py --battery ui --task ui-01-landing-page --replicates 1
python3 eval/run.py --battery ui --replicates 3
```

The gate loads `index.html` directly through `file://` in headless Chromium at both widths. It requires an edited file and no console or uncaught JavaScript errors. Local axe-core 4.11.1 checks `color-contrast`, `button-name`, `link-name`, `label`, and `image-alt`; serious or critical violations fail. The local package avoids a CDN fetch for axe. Pages using Tailwind CDN or remote fonts still need network access. These checks establish floors, not aesthetics or full accessibility coverage.

Per task per replicate, budget for two Claude calls plus two judge calls with four images per judge call. UI uses the coding Claude limits; judge image tokens cost extra. A `/coding` workflow may write planning files into the workspace, and the UI gate does not restrict which files change, so those files reach the judge; `redact_leaks` removes only `.claude`, the output style's name, `skills/writing` or `skills/coding`, and the repository path. Both label orders are judged even when only one UI gate passes. A screenshot render failure aborts the run before the arm is journaled, so `--resume` reruns that arm.

axe reports a 1:1 contrast ratio (white on white) as "incomplete", not a violation, so a passing gate does not prove readable contrast. Incomplete contrast findings are printed in the gate details for the judge to weigh.

Results are directional. Published judge-versus-human agreement on web UI quality is about 70% ([WebDevJudge](https://arxiv.org/abs/2510.18560)); that is context, not a calibration of this judge. Use three replicates and document concrete failure instances with screenshots and the corresponding verdict, rather than relying on single-run win rates.

## Audit

`eval/tasks/audit/` checks the `architecture-audit` workflow on a seeded fixture, outside the three batteries. `seeded/build.py` writes a two-package TypeScript repository with eight planted defects and three clean controls. `seeded/seeds.json` names each by path and kind.

`run_audit.py` builds the fixture in a temp directory, deploys the config into its `.claude/` from the working tree or from `--ref`, and runs `claude -p` with the configured arm's flags, 80 turns and $8. `settings.json` always comes from the working tree. The prompt runs the audit through `/coding` and asks for every finding in `audit-findings.json`. `check_report.py` passes a run that finds at least 7 of the 8 seeds by path and kind and puts no finding on a clean control or a directory that holds one. It does not score severity.

```sh
python3 eval/tasks/audit/test_metrics.py
python3 eval/tasks/audit/test_check_report.py
python3 eval/tasks/audit/run_audit.py eval/results/audit/new-1
python3 eval/tasks/audit/run_audit.py --ref 9d7777c eval/results/audit/old-1
python3 eval/tasks/audit/check_report.py eval/results/audit/new-1/audit-findings.json eval/tasks/audit/seeded/seeds.json
```

The output directory gets `events.jsonl`, `reply.md`, `audits/` (the report and `metrics.jsonl`), `audit-findings.json`, and `summary.json` with turns, cost, and whether the workflow file and `metrics.py` were used. A run costs about $1.50.

Seed recall does not separate workflow versions. The prompt gives the agent the kind list the seeds were drawn from, and the workflow at `9d7777c` also found 8 of 8 in three runs; the two differed only in findings on clean controls (none in four runs of the current text, one to four per run at `9d7777c`). knip does not run in the fixture, which has no `node_modules`, and the fixture's tests cannot load, so the unused-code metrics and the test probe go unexercised.
