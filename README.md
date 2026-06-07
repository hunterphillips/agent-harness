# agent-harness

The skills, subagents, and presets I drop into every project I work on. There's no application code here — the config is the product.

A skill is a process worth repeating, written down: planning, debugging discipline, code review, getting a design grilled before you commit to it. Small files, plain markdown. Take the ones you want, rewrite the ones that don't fit how you work.

Built for [Claude Code](https://claude.com/claude-code), but not married to it. Skills follow the open [Agent Skills](https://agentskills.io) format and the bodies are just prompts — any harness that reads the spec can use them. The plumbing is the Claude-specific part: `agents/` holds subagent definitions, and deployment targets a `.claude/` directory. Swap those for your tool's equivalents and the rest travels.

- `skills/` — one folder per skill, `SKILL.md` plus any sub-files it needs
- `agents/` — dispatchable subagents (codebase search, analysis, web research)
- `presets/` — overlays for specific stacks, e.g. `sn` for ServiceNow

To use: copy the contents into your project's `.claude/` directory, overlay a preset if you need one, done.
