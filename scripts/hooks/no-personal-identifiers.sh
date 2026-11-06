#!/usr/bin/env bash
# PreToolUse hook: refuse a tool call whose input carries one of the user's
# own identifiers (email addresses, phone numbers), so a session never puts
# them in a shell command, a web request, or a subagent's brief. Claude Code
# injects the account email into every conversation, and models have used it
# as a User-Agent or a scraper contact unasked (claude-code issues 81138,
# 104774).
#
# The identifiers live outside this repo in ~/.config/harness/identifiers
# (or $HARNESS_IDENTIFIERS), one per line, matched case-insensitively as
# plain text; blank lines and # comments are ignored. No file, no check.
# Wired in ~/.claude/settings.json for Bash, WebFetch, WebSearch, and Agent.
# Exit 2 blocks the call and the line on stderr reaches the model.
set -u
list="${HARNESS_IDENTIFIERS:-$HOME/.config/harness/identifiers}"
[ -s "$list" ] || exit 0
patterns=$(grep -v -E '^[[:space:]]*(#|$)' "$list") || exit 0
[ -n "$patterns" ] || exit 0
input=$(cat)
hit=$(grep -i -o -F -f <(printf '%s\n' "$patterns") <<< "$input" | head -1)
[ -n "$hit" ] || exit 0
tool=$(printf '%s' "$input" | sed -n 's/.*"tool_name":[[:space:]]*"\([^"]*\)".*/\1/p' | head -1)
echo "Blocked: this ${tool:-tool} call contains one of the user's personal identifiers (${hit}). Never put it in a command, request, header, or prompt for an outside service; use a generic client name, or ask the user if it is really needed." >&2
exit 2
