# Capability A/B eval

This runner compares the final artifacts from the repository configuration and a customization-free control. It uses blind pairwise Codex reviews in both A/B orders. Coding tasks run deterministic checks before qualitative review.

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
