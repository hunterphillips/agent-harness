# agent-harness

Reusable agent configuration — skills, subagents, and per-stack presets — deployed into other projects' `.claude/` directories. There is no application code; the config files are the product.

Built for [Claude Code](https://claude.com/claude-code), but most of it is portable:

- **Skills** (`skills/`) follow the open [Agent Skills](https://agentskills.io) `SKILL.md` format and are plain-markdown process prompts — usable by any harness that reads the spec, or adaptable to Cursor rules / similar with little work.
- **Claude Code-specific plumbing**: `agents/` (subagent definitions), `settings.json` (permissions schema), and the `.claude/` deployment target. Porting to another provider means swapping these for that tool's equivalents.

## Layout

- `skills/` — one folder per skill (`SKILL.md` + optional sub-files)
- `agents/` — dispatchable subagent definitions
- `presets/` — per-stack overlays applied by name (e.g. `init_claude sn` for ServiceNow)
- `settings.json` — template/reference only; not deployed
- `communication_guidelines.md` — deployed alongside the config

## Deployment

`init_claude [preset...]` (a zsh function) rsyncs this repo into the target project's `./.claude/`, excluding `settings.json`, `presets`, `.notes`, and `CLAUDE.md`, then overlays any named presets. Re-running it is the update path; rsync has no `--delete`, so files removed here must be pruned in deployed projects manually.

See `CLAUDE.md` for full conventions (skill authoring rules, artifact regimes, verification checklist).
