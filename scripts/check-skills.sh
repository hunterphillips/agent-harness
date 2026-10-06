#!/usr/bin/env bash
# Static checks for the harness, the "Verifying Changes" list in CLAUDE.md:
# every listed skill has frontmatter with name and description, coding's
# router sub-files have none, and every relative markdown link under
# skills/coding resolves.
set -euo pipefail
cd "$(dirname "$0")/.."
fail=0

for f in skills/*/SKILL.md; do
  if [ "$(head -1 "$f")" != "---" ]; then echo "no frontmatter: $f"; fail=1; continue; fi
  fm=$(awk 'NR == 1 { next } /^---$/ { exit } { print }' "$f")
  grep -q '^name:' <<< "$fm" || { echo "no name: $f"; fail=1; }
  grep -q '^description:' <<< "$fm" || { echo "no description: $f"; fail=1; }
done

for f in skills/coding/*/*.md; do
  [ "$(head -1 "$f")" = "---" ] && { echo "frontmatter on a router sub-file: $f"; fail=1; }
done

# Relative links, with inline code stripped first so examples inside backticks don't count.
# shellcheck disable=SC2016
links_in() { sed 's/`[^`]*`//g' "$1" | grep -oE '\]\([^)]+\)' | sed -E 's/^\]\((.*)\)$/\1/' | grep -vE '^(https?:|mailto:|#)' || true; }
while IFS= read -r f; do
  dir=$(dirname "$f")
  while IFS= read -r link; do
    [ -n "$link" ] || continue
    target=${link%%#*}
    [ -n "$target" ] || continue
    [ -e "$dir/$target" ] || { echo "dead link in $f: $link"; fail=1; }
  done < <(links_in "$f")
done < <(find skills/coding -name '*.md')

[ "$fail" = 0 ] && echo "skills ok"
exit "$fail"
