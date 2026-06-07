# agent-harness

Reusable agent configuration — skills, subagents, and per-stack presets — deployed into a project's `.claude/` directory.

A skill is a process written down: planning, debugging discipline, code review, getting a design grilled before committing to it. Small files, plain markdown, easy to adapt.

Built for [Claude Code](https://claude.com/claude-code), but portable. Skills follow the open [Agent Skills](https://agentskills.io) format and the bodies are just prompts — any harness that reads the spec can use them. The Claude-specific parts are `agents/` (subagent definitions) and the `.claude/` deploy target; swap those for your tool's equivalents.

- `skills/` — one folder per skill, `SKILL.md` plus any sub-files it needs
- `agents/` — dispatchable subagents (codebase search, analysis, web research)
- `presets/` — overlays for specific stacks, e.g. `sn` for ServiceNow

To use: copy the contents into your project's `.claude/` directory, overlaying any preset you need.
