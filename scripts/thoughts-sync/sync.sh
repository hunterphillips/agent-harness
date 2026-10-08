#!/usr/bin/env bash
# Keeps every project's thoughts/ in one private git repo. Each project's
# thoughts/ is a symlink to $THOUGHTS_DIR/<project>/; this script adopts real
# thoughts/ folders into the repo and syncs the repo with its remote.
# Design: thoughts/shared/plans/2026-10-08-thoughts-in-git-design.md.
#
#   sync            commit any changes, pull --rebase, push (under a lock)
#   start           SessionStart hook: sync, wait up to 5 s, print one line if a sync failed
#   stop            Stop hook: adopt the session's project, sync in the background if needed
#   adopt <dir>     move <dir>/thoughts into the repo and leave a symlink
#   link <dir>      create the symlink when the project's folder already exists
#   migrate [--apply]  list every thoughts/ folder under $WORKSPACE; adopt them with --apply
#
# Every hook path exits 0 and prints nothing except start's warning line, so a
# hook never blocks a turn or adds to a session's context. Without a thoughts
# clone, every subcommand except migrate is a silent no-op.
set -euo pipefail

SELF="$(cd "$(dirname "$0")" && pwd -P)/$(basename "$0")"
WS="$(cd "${WORKSPACE:-$HOME/workspace}" 2>/dev/null && pwd -P || echo "${WORKSPACE:-$HOME/workspace}")"
T="${THOUGHTS_DIR:-$WS/thoughts}"
[ -d "$T" ] && T="$(cd "$T" && pwd -P)"
SYNC_LOG="${SYNC_LOG:-$HOME/.claude/logs/thoughts-sync.log}"
SYNC_ERR="$T/.git/thoughts-sync-error"
ADOPT_ERR="$T/.git/thoughts-adopt-error"
LOCK="$T/.git/thoughts-sync.lock"

log() {
  mkdir -p "$(dirname "$SYNC_LOG")"
  printf '%s %s\n' "$(date +%Y-%m-%dT%H:%M:%S)" "$*" >> "$SYNC_LOG"
  if [ -t 2 ]; then printf '%s\n' "$*" >&2; fi
}
ready() { [ -d "$T/.git" ]; }
abs() { (cd "$1" 2>/dev/null && pwd -P); }

project_dir() { git -C "$1" rev-parse --show-toplevel 2>/dev/null || abs "$1"; }

project_name() {
  local common
  if common="$(git -C "$1" rev-parse --path-format=absolute --git-common-dir 2>/dev/null)"; then
    basename "$(dirname "$common")"
  else
    basename "$1"
  fi
}

skipped() {
  local rel="${1#"$WS"/}" entry
  [ -f "$T/.skip" ] || return 1
  while IFS= read -r entry || [ -n "$entry" ]; do
    entry="${entry%%#*}"; entry="${entry%"${entry##*[![:space:]]}"}"; entry="${entry%/}"
    [ -n "$entry" ] || continue
    case "$rel/" in "$entry/"*) return 0 ;; esac
  done < "$T/.skip"
  return 1
}

# Why <dir>/thoughts may not be adopted, or "ok".
adopt_status() {
  local dir="$1" real top
  case "$dir" in "$WS"/*) ;; *) echo "outside workspace"; return ;; esac
  case "$dir/" in "$T/"*) echo "inside thoughts repo"; return ;; esac
  if [ -L "$dir/thoughts" ]; then echo "already linked"; return; fi
  if [ ! -d "$dir/thoughts" ]; then echo "none"; return; fi
  real="$(abs "$dir/thoughts")"
  case "$real/" in "$T/"*) echo "is the thoughts repo"; return ;; esac
  if skipped "$dir"; then echo "skip"; return; fi
  if top="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)"; then
    [ "$(abs "$top")" = "$dir" ] || { echo "not at repo root"; return; }
    [ -z "$(git -C "$dir" ls-files -- thoughts)" ] || { echo "tracked"; return; }
    git -C "$dir" check-ignore -q thoughts || { echo "not ignored"; return; }
  fi
  echo "ok"
}

cmd_adopt() {
  ready || return 0
  local dir status name src dest f rel kept=0
  dir="$(abs "$1")" || return 0
  status="$(adopt_status "$dir")"
  [ "$status" = "ok" ] || return 0
  name="$(project_name "$dir")"
  src="$dir/thoughts"; dest="$T/$name"
  while IFS= read -r f; do
    rel="${f#"$src"/}"
    if [ -e "$dest/$rel" ] || [ -L "$dest/$rel" ]; then
      log "adopt: kept $f, $dest/$rel already exists"
      kept=1
    else
      mkdir -p "$(dirname "$dest/$rel")"
      mv "$f" "$dest/$rel"
    fi
  done < <(find "$src" \( -type f -o -type l \))
  find "$src" -depth -type d -empty -delete
  if [ "$kept" = 1 ] || [ -e "$src" ]; then
    echo "collision: $src" > "$ADOPT_ERR"
    log "adopt: $src left as a folder; move or delete the kept files, then run: $SELF adopt $dir"
    return 0
  fi
  mkdir -p "$dest"
  ln -s "$dest" "$src"
  log "adopt: $src -> $dest"
}

cmd_link() {
  ready || return 0
  local dir name
  dir="$(abs "$1")" || return 0
  name="$(project_name "$dir")"
  if [ -d "$T/$name" ] && [ ! -e "$dir/thoughts" ] && [ ! -L "$dir/thoughts" ]; then
    ln -s "$T/$name" "$dir/thoughts"
    log "link: $dir/thoughts -> $T/$name"
  fi
}

lock() {
  local i=0
  until mkdir "$LOCK" 2>/dev/null; do
    if [ -n "$(find "$LOCK" -maxdepth 0 -mmin +5 2>/dev/null)" ]; then
      log "sync: removing stale lock"; rmdir "$LOCK" 2>/dev/null || true; continue
    fi
    i=$((i + 1)); [ "$i" -lt 240 ] || { log "sync: gave up waiting for the lock"; return 1; }
    sleep 0.5
  done
  trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
}

needs_push() {
  local head
  [ -n "$(git -C "$T" remote)" ] || return 1
  head="$(git -C "$T" status --porcelain --branch | head -1)"
  case "$head" in *"[ahead"*) return 0 ;; *...*) return 1 ;; *) return 0 ;; esac
}

cmd_sync() {
  ready || return 0
  lock || return 0
  cd "$T"
  local folders out files
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    folders="$(git diff --cached --name-only | cut -d/ -f1 | sort -u | tr '\n' ' ')"
    git commit -qm "sync: $(hostname -s) ${folders% }"
  fi
  [ -n "$(git remote)" ] || return 0
  if git rev-parse -q --verify '@{u}' >/dev/null 2>&1; then
    if ! out="$(git pull -q --rebase --no-autostash 2>&1)"; then
      if [ -d .git/rebase-merge ] || [ -d .git/rebase-apply ]; then
        files="$(git diff --name-only --diff-filter=U | tr '\n' ' ')"
        git rebase --abort
        echo "conflict: ${files% }" > "$SYNC_ERR"
        log "sync: rebase conflict in ${files% }; local commits kept, nothing pushed"
      else
        log "sync: pull failed: $out"
      fi
      return 0
    fi
  fi
  if needs_push; then
    out="$(git push -q -u origin HEAD 2>&1)" || { log "sync: push failed: $out"; return 0; }
  fi
  rm -f "$SYNC_ERR"
}

detach_sync() {
  mkdir -p "$(dirname "$SYNC_LOG")"
  nohup "$SELF" sync < /dev/null >> "$SYNC_LOG" 2>&1 &
  echo $!
}

cmd_stop() {
  ready || return 0
  local input="" cwd="" status
  [ -t 0 ] || input="$(cat)"
  if [ -n "$input" ] && command -v jq >/dev/null; then cwd="$(jq -r '.cwd // empty' <<< "$input" 2>/dev/null || true)"; fi
  [ -n "$cwd" ] || cwd="$PWD"
  if [ -d "$cwd" ]; then cmd_adopt "$(project_dir "$cwd")" || true; fi
  status="$(git -C "$T" status --porcelain)"
  if [ -n "$status" ] || needs_push; then
    log "stop: syncing"
    detach_sync > /dev/null
  fi
}

cmd_start() {
  ready || return 0
  [ -t 0 ] || cat > /dev/null
  local pid i=0 dir
  pid="$(detach_sync)"
  while kill -0 "$pid" 2>/dev/null && [ "$i" -lt 25 ]; do sleep 0.2; i=$((i + 1)); done
  if [ -f "$ADOPT_ERR" ]; then
    dir="$(sed -n 's/^collision: //p' "$ADOPT_ERR")"
    if [ -L "$dir" ] || [ ! -d "$dir" ]; then rm -f "$ADOPT_ERR"; fi
  fi
  if [ -f "$SYNC_ERR" ] || [ -f "$ADOPT_ERR" ]; then
    echo "thoughts sync failed ($(cat "$SYNC_ERR" "$ADOPT_ERR" 2>/dev/null | tr '\n' ';' | sed 's/;$//')); see $SYNC_LOG"
  fi
}

cmd_migrate() {
  if ! ready; then
    echo "No thoughts repo at $T. Clone it there first (or set THOUGHTS_DIR), then rerun." >&2
    return 1
  fi
  local apply=0 path dir status name seen=""
  [ "${1:-}" = "--apply" ] && apply=1
  while IFS= read -r path; do
    dir="$(dirname "$path")"
    status="$(adopt_status "$dir")"
    name="$(project_name "$dir")"
    case " $seen " in *" $name "*) [ "$status" = ok ] && status="ok (shares $name with another folder)" ;; esac
    case "$status" in ok*) seen="$seen $name" ;; esac
    printf '%-60s -> %-20s %s\n' "${path#"$WS"/}" "$name" "$status"
    if [ "$apply" = 1 ]; then case "$status" in ok*) cmd_adopt "$dir" ;; esac; fi
  done < <(find "$WS" \( -name node_modules -o -name .git -o -path "$T" \) -prune -o -name thoughts \( -type d -o -type l \) -print | sort)
}

case "${1:-}" in
  sync) cmd_sync ;;
  start) cmd_start || true ;;
  stop) cmd_stop || true ;;
  adopt) cmd_adopt "${2:?adopt <dir>}" ;;
  link) cmd_link "${2:?link <dir>}" ;;
  migrate) cmd_migrate "${2:-}" ;;
  *) sed -n '2,15p' "$0" >&2; exit 2 ;;
esac
