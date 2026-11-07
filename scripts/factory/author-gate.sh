#!/usr/bin/env bash
# Before triage or implement: run only for work the owner asked for. The issue's
# author must be the repo owner, or the factory itself on an issue the monitor
# job opened (its body carries the monitor-signature marker); a part of a split
# issue is judged by its parent. Anything else is skipped. An issue that arrived
# by label or by opening gets no reaction, so a stranger's issue starts no agent;
# a dispatched run (EVENT=workflow_dispatch) was started on purpose, so its
# refusal goes to the owner as a hand-off.
# Env: N REPO OWNER GH_TOKEN; optional EVENT. Output: ok (true|false).
set -euo pipefail
# shellcheck source=lib.sh
source "$(dirname "$0")/lib.sh"

parent=$(part_parent "$N")
subject=${parent:-$N}
author=$(issue_author "$subject")
of="issue #$N${parent:+ (part of #$parent)}"
if [ "$author" = "$OWNER" ]; then
  log "$of is owner-authored; proceeding"
  output ok true
  exit 0
fi
case "$author" in
  claude|app/claude|"claude[bot]")
    if [ -n "$(monitor_signature_of "$subject")" ]; then
      log "$of was opened by the monitor job; proceeding"
      output ok true
      exit 0
    fi ;;
esac
log "$of author is '$author', not $OWNER or the monitor job; nothing to do"
output ok false
if [ "${EVENT:-}" = workflow_dispatch ]; then
  set_status "$N" ready-for-human
  mention_owner "$N" "This issue was dispatched to the implement job but not admitted: its author is '$author', not $OWNER, and it is not an issue the monitor job opened."
fi
