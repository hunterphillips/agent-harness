# Capability A/B eval

This runner compares the final artifacts from the repository configuration and a customization-free control. It uses blind pairwise Codex reviews in both A/B orders. Both arms run with `--setting-sources project`, so they load project settings only and a user-level hook, setting, or output style in `~/.claude` cannot contaminate an A/B result. Coding tasks run deterministic checks before qualitative review.

Requires Python 3.12, `git`, an authenticated `claude` CLI, and an authenticated `codex` CLI.

```sh
# List tasks and every planned invocation; spends no tokens
python eval/run.py --battery writing --dry-run

# Smoke-test one task with one replicate
python eval/run.py --battery writing --task writing-01-rewrite-ai-draft --replicates 1

# Run a full battery (default: three replicates)
python eval/run.py --battery writing
python eval/run.py --battery coding
```

Interrupted runs leave a fsynced journal. Continue one with `python eval/run.py --battery writing --resume YYYYMMDD-HHMMSS` using the original task selection and replicate count.

Results land in `eval/results/<timestamp>.json` and `.md`; `.meta.json` and `.records.jsonl` are recovery/audit files. The directory is gitignored.

Each replicate can make two Claude calls and two Codex judge calls. Coding cases with one passing deterministic gate skip both judge calls. The runner caps Claude calls at $1/$2 per writing control/configured run and $3/$6 per coding control/configured run; these are ceilings, not estimates. A default writing battery plans 60 Claude calls and 60 judge calls, so use a one-replicate, one-task smoke test before a full run. Efficiency metrics are reported separately and never affect quality verdicts.

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

Per task per replicate, budget for two Claude calls plus two judge calls with four images per judge call. UI uses the coding Claude limits ($3 control / $6 configured); judge image tokens cost extra. Both label orders are judged even when only one UI gate passes. A screenshot render failure aborts the run before the arm is journaled, so `--resume` reruns that arm.

axe reports a 1:1 contrast ratio (white on white) as "incomplete", not a violation, so a passing gate does not prove readable contrast. Incomplete contrast findings are printed in the gate details for the judge to weigh.

Results are directional. Published judge-versus-human agreement on web UI quality is about 70% ([WebDevJudge](https://arxiv.org/abs/2510.18560)); that is context, not a calibration of this judge. Use three replicates and document concrete failure instances with screenshots and the corresponding verdict, rather than relying on single-run win rates.
