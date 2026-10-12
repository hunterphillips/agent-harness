#!/usr/bin/env bash
# Before triage or implement: run only for work the owner asked for. The issue's
# author must be the repo owner; a part of a split issue is judged by its
# parent's author. Anything else is skipped without a label or a comment, so a
# stranger's issue gets no reaction and starts no agent.
# Env: N REPO OWNER GH_TOKEN. Output: ok (true|false).
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

parent=$(part_parent "$N")
author=$(issue_author "${parent:-$N}")
if [ "$author" = "$OWNER" ]; then
  log "issue #$N${parent:+ (part of #$parent)} is owner-authored; proceeding"
  output ok true
else
  log "issue #$N${parent:+ (part of #$parent)} author is '$author', not $OWNER; nothing to do"
  output ok false
fi
