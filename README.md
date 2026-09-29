# agent-harness

Reusable agent configuration — skills, subagents, and an output style — served to every project from one clone via symlinks into the global config.

Built for [Claude Code](https://claude.com/claude-code), but portable. Skills follow the open [Agent Skills](https://agentskills.io) format and the bodies are just prompts — any harness that reads the spec can use them. The Claude-specific parts are `agents/` (subagent definitions) and the `.claude/` deploy target; swap those for your tool's equivalents.

- `skills/` — one folder per skill, `SKILL.md` plus any sub-files it needs
- `agents/` — dispatchable subagents (codebase search, analysis, web research)
- `output-styles/` — the `Human Writer` output style: an always-on, system-prompt-level rule set that keeps Claude's replies direct and concise and its prose free of common AI-writing tells. The `writing` skill is its on-demand counterpart for deliberate prose work (humanizer deep-clean, drafting craft, per-project style guides).
- `eval/` — a blind pairwise A/B eval harness that measures whether this config actually beats a bare agent (and whether an edit helped or hurt). Repo tooling — not part of the deployable config. See `eval/README.md`. `eval/skill-trigger/` is a second, cheaper suite: does the `coding` router fire on realistic dev requests and stay quiet otherwise (Claude Code's built-in `claude plugin eval`).

To use: symlink the pieces into your global config so one clone serves every project — each skill folder into `~/.claude/skills/`, `agents/` as `~/.claude/agents`, and `output-styles/human-writer.md` into `~/.claude/output-styles/` (edits to the clone propagate instantly; a project-level `.claude/` copy of a skill overrides the global one on name collision). Codex and other runtimes that read the Agent Skills spec pick up the same skills via `ln -s <repo>/skills ~/.agents/skills`. Prefer per-project isolation? Copying the same folders into a project's `.claude/` works too. To turn on the `Human Writer` default, set `outputStyle` to `"Human Writer"` in `~/.claude/settings.json` (applies everywhere) or run `/config` and select it per project.

The repo is also a Claude Code plugin marketplace. `claude plugin marketplace add hunterphillips/agent-harness` followed by `claude plugin install harness@agent-harness` installs the same skills and agents as the `harness` plugin. Cloud runners that never see `~/.claude` load it the same way: a Claude Code routine attaches the repo and its committed `.claude/` symlinks self-load; a GitHub Actions job passes the repo URL to `claude-code-action`'s `plugin_marketplaces` input.

Inspired by [humanlayer](https://github.com/humanlayer/humanlayer) and [mattpocock/skills](https://github.com/mattpocock/skills).
