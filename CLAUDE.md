# Claude Code Harness Template

Source repo for reusable Claude Code configuration — skills, subagents, and presets deployed into other projects' `.claude/` directories. This is a meta-harness: there is no application code, build, or test suite. The config files ARE the product; sessions here edit the harness itself.

## Structure

- `skills/` — one folder per skill (`skills/<name>/SKILL.md` + optional sub-files). The only behavior unit: commands and skills are unified; there is no `commands/` folder.
- `agents/` — dispatchable subagent definitions (codebase-locator/-analyzer/-pattern-finder, thoughts-locator/-analyzer, dependency-analyzer, web-search-researcher)
- `presets/` — per-stack overlays applied by name (e.g. `init_claude sn`)
- `settings.json` — template/reference only; NOT deployed and not auto-loaded. Active permissions live in `~/.claude/settings.json`.
- `communication_guidelines.md` — deployed alongside the config
- `.notes/` — local-only: reading material and parked/unported skills. Never deployed.

## Deployment

`init_claude [preset...]` (zsh function in `~/.zshrc`) rsyncs this repo into the target project's `./.claude/`, excluding `settings.json`, `presets`, `.notes`, `.claude`, `.DS_Store`, and `CLAUDE.md`, then overlays any named presets.

- **Re-running `init_claude` is the update path.** rsync has no `--delete`: project-specific additions survive, but deletions/renames made here are NOT pruned in deployed projects — remove stale files there manually.
- This `CLAUDE.md` describes the harness repo and must never land in target projects (they get their own via `/write-claude-md`).

## Skill Conventions

- Kebab-case names. Frontmatter: `name` + `description` required; `model`, `argument-hint`, `disable-model-invocation` (user-only invocation) as needed.
- **Descriptions are trigger-first ("Use when …") and must be disjoint across skills** — overlapping trigger surfaces cause routing coin flips. Sibling skills cross-route in their descriptions (see grill-me ↔ grill-with-docs, architecture-audit ↔ architecture-improvement).
- Keep SKILL.md lean: state each rule once, one excellent example, bulk templates and shared rules in sub-files (progressive disclosure). Authoring authority: `skills/writing-skills/`.
- Cross-reference sibling skills via relative paths (`../<skill>/<file>.md`). Only the main-session controller can resolve these — dispatched subagents cannot, so controllers read/fill/inline templates before dispatching (see `subagent-driven-development`, `requesting-code-review`).
- Agent tool: parallel work = multiple Agent calls in one message; `isolation: "worktree"` for isolated workspaces.

## Artifact Regimes (two, intentional)

| Artifact | Location | Committed? |
| --- | --- | --- |
| Designs, plans, research, tickets, PR docs | `thoughts/shared/{plans,research,tickets,prs}/` | No (synced, never committed) |
| Domain glossary + architecture decisions | `CONTEXT.md` (repo root) + `docs/adr/` | Yes |

The thoughts pipeline is HumanLayer-derived; the CONTEXT/ADR layer is mattpocock-derived (produced by `grill-with-docs`, consumed by `architecture-improvement`, `diagnose`, `tdd`, `zoom-out`).

## Philosophy

- **Conservative testing**: high-value/essential coverage over extensive; no brittle exact-message assertions, no enumeration. Baked into `tdd` and the SDD/code-review prompts.
- **No Claude attribution in commits** (`commit` skill).
- **Backlog over single-session when work needs async/parallel pickup**: `to-prd`/`to-issues` auto-detect GitHub Issues vs local markdown (`skills/to-issues/tracker-conventions.md`).

## Skill Map

- **Design**: brainstorming (fuzzy idea → design) · grill-me (stress-test, no writes) · grill-with-docs (stress-test + CONTEXT/ADR updates) · prototype (throwaway code answers a question)
- **Planning**: create-plan · iterate-plan · compare-plans · validate-plan (shared: `create-plan/research-conventions.md`, `create-plan/plan-template.md`)
- **Execution**: implement-plan · subagent-driven-development · dispatching-parallel-agents · tdd
- **Review**: requesting-code-review · architecture-audit (diagnostic) · architecture-improvement (deepening)
- **Debugging**: diagnose (feedback-loop-first discipline)
- **Backlog**: to-prd → to-issues (GitHub or local)
- **Session continuity**: handoff → pickup
- **Codebase understanding**: onboard (first contact) · research-codebase (deep, parallel) · zoom-out (quick reorient)
- **Docs**: write-claude-md · update-claude-md
- **Utilities**: commit (`auto` arg = no confirmation) · describe-pr · search-domains · teach · deep-reading-synthesizer · pdf-extract · writing-skills

## Verifying Changes

No build or tests. After editing:

1. Frontmatter check: every `skills/*/SKILL.md` has `name` + `description`.
2. After any rename/removal, grep the old name across `skills/ agents/ presets/` — cross-references are the main breakage class.
3. Relic check: no references to nonexistent tools or directories (e.g. `TodoWrite` is not a real tool — task tracking is TaskCreate/TaskUpdate).
4. To propagate: re-run `init_claude` in target projects (and delete files there that were removed here).
