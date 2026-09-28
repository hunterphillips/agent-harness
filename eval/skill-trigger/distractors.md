# Distractor skill set — coding-trigger-eval-distractors

Wrapper plugin `harness-skills-d` used to measure whether the `coding` router
still auto-fires under realistic skill-listing competition (~50 skills, not
just the harness's own 13). `skills/` is a real directory (not a symlink),
built by `cp -RL`/manual copy (SKILL.md + sibling files only; no
node_modules/.git) from the sources below. Landed at 40 total skill
directories (13 harness + 27 distractors) — short of the 45-55 soft target
because the explicitly enumerated source list below sums to 27 distractors;
no additional undocumented sources were added.

## Harness skills (13) — from `/Users/hunterphillips/workspace/Claude/skills/`

| Directory | Source |
|---|---|
| brain | /Users/hunterphillips/workspace/Claude/skills/brain |
| brainstorming | /Users/hunterphillips/workspace/Claude/skills/brainstorming |
| coding | /Users/hunterphillips/workspace/Claude/skills/coding |
| commit | /Users/hunterphillips/workspace/Claude/skills/commit |
| creating-skills | /Users/hunterphillips/workspace/Claude/skills/creating-skills |
| dispatching-parallel-agents | /Users/hunterphillips/workspace/Claude/skills/dispatching-parallel-agents |
| handoff | /Users/hunterphillips/workspace/Claude/skills/handoff |
| onboard | /Users/hunterphillips/workspace/Claude/skills/onboard |
| pdf-extract | /Users/hunterphillips/workspace/Claude/skills/pdf-extract |
| pickup | /Users/hunterphillips/workspace/Claude/skills/pickup |
| video-transcript | /Users/hunterphillips/workspace/Claude/skills/video-transcript |
| write-claude-md | /Users/hunterphillips/workspace/Claude/skills/write-claude-md |
| writing | /Users/hunterphillips/workspace/Claude/skills/writing |

Set as of the 2026-09-22 run. `pdf-extract` was removed from the harness on 2026-09-27; a rebuild starts from 12 harness skills.

## Distractors (27)

### claude.ai-synced Anthropic skills (9) — from `~/.claude/skills/synced/2cba75ad-d6e9-4d45-829f-34cade2f6695_edf59a0e-fd30-4c9b-b3c8-8b73aa406971/`

| Directory | Source |
|---|---|
| docx | .../synced/2cba75ad.../docx |
| docs | .../synced/2cba75ad.../docs |
| pptx | .../synced/2cba75ad.../pptx |
| xlsx | .../synced/2cba75ad.../xlsx |
| pdf | .../synced/2cba75ad.../pdf |
| morning | .../synced/2cba75ad.../morning |
| skill-creator | .../synced/2cba75ad.../skill-creator |
| import-memory | .../synced/2cba75ad.../import-memory |
| brainstorming-anthropic | .../synced/2cba75ad.../brainstorming (renamed: collides with the harness's own `brainstorming` dir; frontmatter `name:` left as `brainstorming` unchanged — `claude plugin validate` did not refuse the duplicate frontmatter name, only the directory/tool-identifier needed to be unique, matching Hunter's real sessions where the harness skill is bare `brainstorming` and this one is namespaced `anthropic-skills:brainstorming`) |

### Codex plugin skills (3) — from `~/.claude/plugins/cache/openai-codex/codex/1.0.6/skills/`

| Directory | Source |
|---|---|
| codex-cli-runtime | .../codex/1.0.6/skills/codex-cli-runtime |
| codex-result-handling | .../codex/1.0.6/skills/codex-result-handling |
| gpt-5-4-prompting | .../codex/1.0.6/skills/gpt-5-4-prompting |

### Productivity plugin skills (4) — from `~/.claude/plugins/synced/2cba75ad-d6e9-4d45-829f-34cade2f6695_edf59a0e-fd30-4c9b-b3c8-8b73aa406971/productivity~g2/skills/`
(not under `~/.claude/plugins/cache/` as first guessed — the active copy lives under `~/.claude/plugins/synced/`)

| Directory | Source |
|---|---|
| start | .../productivity~g2/skills/start |
| update | .../productivity~g2/skills/update |
| memory-management | .../productivity~g2/skills/memory-management |
| task-management | .../productivity~g2/skills/task-management |

### frontend-design + exa plugin skills (3) — from `~/.claude/plugins/cache/claude-plugins-official/`

| Directory | Source |
|---|---|
| frontend-design | .../claude-plugins-official/frontend-design/4a667a85cf17/skills/frontend-design (newest-mtime hash dir; content verified identical across all cached hash dirs via diff) |
| exa-agent | .../claude-plugins-official/exa/3.4.1/skills/exa-agent |
| search | .../claude-plugins-official/exa/3.4.1/skills/search |

### Nowgentic project skills (8) — from `~/workspace/work/nowgentic/execops-servicenow/.claude/skills/`

| Directory | Source |
|---|---|
| catchup | .../nowgentic/execops-servicenow/.claude/skills/catchup |
| extract-lessons | .../nowgentic/execops-servicenow/.claude/skills/extract-lessons |
| legacy-parity-scan | .../nowgentic/execops-servicenow/.claude/skills/legacy-parity-scan |
| next-work | .../nowgentic/execops-servicenow/.claude/skills/next-work |
| now-sdk | .../nowgentic/execops-servicenow/.claude/skills/now-sdk |
| process-gardener | .../nowgentic/execops-servicenow/.claude/skills/process-gardener |
| servicenow-expert | .../nowgentic/execops-servicenow/.claude/skills/servicenow-expert |
| write-linear-issue | .../nowgentic/execops-servicenow/.claude/skills/write-linear-issue |
