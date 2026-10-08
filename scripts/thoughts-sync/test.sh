#!/usr/bin/env bash
# shellcheck disable=SC2034 # variables are read inside check's eval strings
# Integration test for sync.sh: builds a throwaway workspace with a bare
# remote, a thoughts clone, and fixture projects, then checks the paths that
# can lose or leak data. Case numbers and B-numbers match
# thoughts/shared/plans/2026-10-08-thoughts-in-git.md.
set -euo pipefail

S="$(cd "$(dirname "$0")" && pwd -P)/sync.sh"
TMP="$(mktemp -d)"; TMP="$(cd "$TMP" && pwd -P)"
trap '[ -n "${KEEP:-}" ] && echo "kept $TMP" || rm -rf "$TMP"' EXIT
export WORKSPACE="$TMP/ws" THOUGHTS_DIR="$TMP/ws/thoughts" SYNC_LOG="$TMP/sync.log"
export GIT_CONFIG_GLOBAL="$TMP/gitconfig" GIT_CONFIG_NOSYSTEM=1
git config --global user.name test
git config --global user.email test@example.com
git config --global init.defaultBranch main
git config --global core.excludesFile "$TMP/ignore"
echo /thoughts > "$TMP/ignore"
W="$WORKSPACE"; T="$THOUGHTS_DIR"; R="$TMP/remote.git"
fail=0

check() { if eval "$2"; then echo "ok   $1"; else echo "FAIL $1"; fail=1; fi; }
put() { mkdir -p "$(dirname "$1")"; printf '%s\n' "$2" > "$1"; }
mkrepo() { git init -q "$1"; put "$1/README" x; git -C "$1" add README; git -C "$1" commit -qm init; }
on_remote() { local names; names="$(git --git-dir="$R" log --name-only --format= main 2>/dev/null)" || return 1; grep -qx "$1" <<< "$names"; }
stop_at() { printf '{"cwd":"%s","hook_event_name":"Stop"}' "$1" | "$S" stop; }
wait_synced() { local i=0; while [ "$i" -lt 50 ]; do on_remote "$1" && return 0; sleep 0.2; i=$((i + 1)); done; return 1; }

mkdir -p "$W"
git init -q --bare "$R"
git clone -q "$R" "$T" 2>/dev/null
printf 'client\n# comment\n' > "$T/.skip"
git -C "$T" add .skip && git -C "$T" commit -qm init && git -C "$T" push -q -u origin HEAD

# 1. adopt a repo with an ignored thoughts/
mkrepo "$W/proj1"; put "$W/proj1/thoughts/shared/plans/a.md" plan
"$S" adopt "$W/proj1"
check "1 repo adopted as a symlink (B10)" '[ -L "$W/proj1/thoughts" ] && [ -f "$T/proj1/shared/plans/a.md" ]'
check "1 old path still reads (B8)" '[ "$(cat "$W/proj1/thoughts/shared/plans/a.md")" = plan ]'
check "1 code repo stays clean (B9)" '[ -z "$(git -C "$W/proj1" status --porcelain)" ]'

# 2. tracked, skipped, and plain folders
mkrepo "$W/proj2"; put "$W/proj2/thoughts/x.md" x
git -C "$W/proj2" add -f thoughts && git -C "$W/proj2" commit -qm thoughts
"$S" adopt "$W/proj2"
put "$W/client/thoughts/c.md" secret; put "$W/client/sub/thoughts/c.md" secret
"$S" adopt "$W/client"; "$S" adopt "$W/client/sub"
put "$W/plain/thoughts/y.md" y
"$S" adopt "$W/plain"
check "2 tracked thoughts/ untouched (B10)" '[ -d "$W/proj2/thoughts" ] && [ ! -L "$W/proj2/thoughts" ]'
check "2 skipped folder and its subfolder untouched (B10)" '[ ! -L "$W/client/thoughts" ] && [ ! -L "$W/client/sub/thoughts" ] && [ ! -e "$T/client" ] && [ ! -e "$T/sub" ]'
check "2 plain folder adopted (B10)" '[ -L "$W/plain/thoughts" ] && [ -f "$T/plain/y.md" ]'

# 3. a worktree shares its main clone's folder
git -C "$W/proj1" worktree add -q -b wt "$W/proj1-wt"
put "$W/proj1-wt/thoughts/shared/b.md" b
"$S" adopt "$W/proj1-wt"
check "3 worktree maps to main clone (B11)" '[ -L "$W/proj1-wt/thoughts" ] && [ -f "$T/proj1/shared/b.md" ] && [ ! -e "$T/proj1-wt" ]'

# 4. a destination collision keeps both files
put "$T/plain2/c.md" old; put "$W/plain2/thoughts/c.md" new; put "$W/plain2/thoughts/d.md" d
"$S" adopt "$W/plain2"
check "4 collision keeps both and a real folder" '[ "$(cat "$T/plain2/c.md")" = old ] && [ "$(cat "$W/plain2/thoughts/c.md")" = new ] && [ ! -L "$W/plain2/thoughts" ] && [ -f "$T/plain2/d.md" ]'
check "4 collision writes the marker" '[ -f "$T/.git/thoughts-adopt-error" ]'
rm -rf "$W/plain2" "$T/.git/thoughts-adopt-error"

# 5. sync pushes; start commits another session's work instead of stashing it
"$S" sync
git clone -q "$R" "$TMP/other" 2>/dev/null
check "5 second clone sees the file (B1)" '[ -f "$TMP/other/proj1/shared/plans/a.md" ]'
put "$T/proj1/shared/wip.md" wip
out="$("$S" start < /dev/null)"
check "5 start prints nothing on success (B4)" '[ -z "$out" ]'
check "5 open session file intact, nothing stashed (B13)" '[ "$(cat "$T/proj1/shared/wip.md")" = wip ] && [ -z "$(git -C "$T" stash list)" ]'
check "5 start pushed it (B3)" 'wait_synced proj1/shared/wip.md'

# 6. a rebase conflict keeps the local commit and rewrites nothing
git -C "$TMP/other" pull -q
put "$TMP/other/proj1/shared/plans/a.md" remote
git -C "$TMP/other" commit -qam remote && git -C "$TMP/other" push -q
remote_head="$(git --git-dir="$R" rev-parse main)"
put "$T/proj1/shared/plans/a.md" local
"$S" sync
check "6 conflict writes the marker (B5)" 'grep -q "proj1/shared/plans/a.md" "$T/.git/thoughts-sync-error"'
check "6 local commit kept, no rebase left open (B5)" '[ "$(cat "$T/proj1/shared/plans/a.md")" = local ] && [ ! -d "$T/.git/rebase-merge" ]'
check "6 remote history not rewritten (B5)" '[ "$(git --git-dir="$R" rev-parse main)" = "$remote_head" ]'
out="$("$S" start < /dev/null)"
check "6 next start reports it in one line (B4)" '[ "$(printf "%s\n" "$out" | wc -l | tr -d " ")" = 1 ] && printf "%s" "$out" | grep -q conflict'
git -C "$T" fetch -q && git -C "$T" reset -q --hard origin/main && rm -f "$T/.git/thoughts-sync-error"

# 7. offline commits push on the next stop
mv "$R" "$R.off"
put "$T/proj1/shared/off.md" off
"$S" sync
check "7 offline sync commits locally (B7)" '[ -z "$(git -C "$T" status --porcelain)" ] && git -C "$T" log -1 --name-only | grep -q off.md && [ ! -f "$T/.git/thoughts-sync-error" ]'
mv "$R.off" "$R"
stop_at "$TMP"
check "7 stop on a clean tree pushes leftover commits (B7)" 'wait_synced proj1/shared/off.md'

# 8. two syncs at once
put "$T/proj1/shared/c1.md" 1; put "$T/proj1/shared/c2.md" 2
"$S" sync & "$S" sync & wait
check "8 concurrent syncs both land (B6)" 'on_remote proj1/shared/c1.md && on_remote proj1/shared/c2.md'
check "8 repo intact (B6)" 'git -C "$T" fsck --no-progress --no-dangling 2>/dev/null'
check "8 lock released (B6)" '[ ! -d "$T/.git/thoughts-sync.lock" ]'

# 9. a quiet turn starts no sync
sleep 0.5; mv "$R" "$R.off"; lines="$(wc -l < "$SYNC_LOG")"
stop_at "$TMP"; sleep 0.5
check "9 clean, up-to-date stop does nothing (B2)" '[ "$(wc -l < "$SYNC_LOG")" = "$lines" ]'
mv "$R.off" "$R"

# 10. never adopt the workspace root or the thoughts repo
stop_at "$W"; stop_at "$T"
check "10 thoughts repo stays put (B10)" '[ -d "$T/.git" ] && [ ! -L "$T" ] && [ ! -e "$T/ws" ] && [ ! -e "$T/thoughts" ]'

exit "$fail"
