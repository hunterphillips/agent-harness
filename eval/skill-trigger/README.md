# Skill-trigger eval

Measures whether the `coding` router auto-fires on realistic dev requests and
stays quiet on non-dev ones, using Claude Code's built-in `claude plugin eval`
(docs: https://code.claude.com/docs/en/plugin-evals.md). Complements the
Codex-judged A/B runner in `../run.py`, which measures output quality; this
measures triggering only.

Cases: 10 should-trigger dev prompts, 3 should-not controls. Graders are the
free `tool_used` type only (no judge model), so a run costs ~$4 and ~2 min.

## Run

The harness repo is not a plugin, so build a throwaway wrapper that points at
`skills/` and this suite:

```sh
W=$(mktemp -d)/harness-skills
mkdir -p $W/.claude-plugin
cp eval/skill-trigger/plugin.json $W/.claude-plugin/
ln -s "$PWD/skills" $W/skills
cp -R eval/skill-trigger/evals $W/evals
(cd $W && claude plugin eval . --ablation none --max-cost-usd 15 --trust-plugin -j 4 --model opus)
```

Pin `--model` so runs are comparable over time; the tool otherwise uses your
settings default. Note the eval also loads ~13 Claude Code built-in skills
(dataviz, code-review, update-config, …) in every run, so the "13-skill"
listing is really ~26.

```sh
# (that's the whole recipe)
```

Results print as a table and land under `$W/evals/results/<timestamp>/`
(`report.html`, `aggregate-result.json`). Copy anything worth keeping into
`eval/results/` (gitignored).

## Distractor mode

The wrapper loads only the 13 harness skills, so the listing has far less
competition than a real session (~50 skills). To measure under realistic
competition, copy other skill directories into `$W/skills/` before running —
e.g. the bundled `anthropic-skills`, `codex`, `productivity`, and
nowgentic project skills. See `distractors.md` for the set used on 2026-09-22.

## History

- 2026-09-22, harness-only (~26 listed incl. built-ins): 30/30 should-trigger
  fired, 0/9 controls fired. $3.94, 112 s.
- 2026-09-22, distractor mode (53 listed: 13 harness + 27 distractors + 13
  built-ins; see `distractors.md`): 30/30 fired, 0/9 controls. $6.16, 121 s.
  Listing was not truncated (20,006 chars; longest entry 1,447 < 1,536 cap).
  No degradation from competition at n=3 runs/case. Model: settings default
  (opus[1m]) — not pinned; pin `--model` next time.
