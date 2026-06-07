# agent-harness

Reusable agent configuration — skills and subagents — deployed into a project's `.claude/` directory.

Built for [Claude Code](https://claude.com/claude-code), but portable. Skills follow the open [Agent Skills](https://agentskills.io) format and the bodies are just prompts — any harness that reads the spec can use them. The Claude-specific parts are `agents/` (subagent definitions) and the `.claude/` deploy target; swap those for your tool's equivalents.

- `skills/` — one folder per skill, `SKILL.md` plus any sub-files it needs
- `agents/` — dispatchable subagents (codebase search, analysis, web research)

To use: copy the contents into your project's `.claude/` directory.
