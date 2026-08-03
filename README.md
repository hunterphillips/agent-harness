# agent-harness

Reusable agent configuration — skills and subagents — deployed into a project's `.claude/` directory.

Built for [Claude Code](https://claude.com/claude-code), but portable. Skills follow the open [Agent Skills](https://agentskills.io) format and the bodies are just prompts — any harness that reads the spec can use them. The Claude-specific parts are `agents/` (subagent definitions) and the `.claude/` deploy target; swap those for your tool's equivalents.

- `skills/` — one folder per skill, `SKILL.md` plus any sub-files it needs
- `agents/` — dispatchable subagents (codebase search, analysis, web research)
- `output-styles/` — the `Human Writer` output style: an always-on, system-prompt-level rule set that keeps Claude's replies direct and concise and its prose free of common AI-writing tells. The `writing` skill is its on-demand counterpart for deliberate prose work (humanizer deep-clean, drafting craft, per-project style guides).
- `eval/` — a blind pairwise A/B eval harness that measures whether this config actually beats a bare agent (and whether an edit helped or hurt). Repo tooling — not part of the deployable config. See `eval/README.md`.

To use: copy `skills/`, `agents/`, and `output-styles/` into your project's `.claude/` directory. To turn on the `Human Writer` default, set `outputStyle` to `"Human Writer"` in your global `~/.claude/settings.json` (applies everywhere) or run `/config` and select it per project.

Inspired by [humanlayer](https://github.com/humanlayer/humanlayer) and [mattpocock/skills](https://github.com/mattpocock/skills).
