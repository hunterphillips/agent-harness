#!/usr/bin/env bash
# The factory's self-hosted runners on hub: two per private repo, both under
# the repo's own user factory-<repo> with no sudo and a 750 home, so a job in
# one repo cannot read another repo's checkout, token, or Claude state. Each is
# a systemd service (svc.sh) that survives reboots.
#   hub-<repo>         label `factory`: the factory's own jobs (factory.yml)
#   hub-<repo>-checks  label `checks`:  the repo's own workflows (CI, suites)
# Two runners because one runner runs one job at a time: the implement job
# holds the factory runner while its gate waits for the PR's checks, so those
# checks need a runner of their own or they never start. The two share the
# user's home (npm and Playwright caches); the factory job wipes ~/.claude when
# it starts, so a checks workflow must never run Claude.
#
# Run on hub as a sudoer (ubuntu) with gh logged in as the repo owner:
#   scripts/factory/runner.sh add owner/repo      # idempotent; adds what is missing
#   scripts/factory/runner.sh remove owner/repo
#   scripts/factory/runner.sh list
# Shared prerequisites a repo's tests need from the system (browser libraries
# for Playwright) are installed once by hand, not here.
set -euo pipefail

cmd=${1:?usage: runner.sh add|remove|list [owner/repo]}
slug=${2:-}
case "$cmd" in
  add|remove) [ -n "$slug" ] || { echo "usage: runner.sh $cmd owner/repo" >&2; exit 2; } ;;
  list) ;;
  *) echo "usage: runner.sh add|remove|list [owner/repo]" >&2; exit 2 ;;
esac
[ "$(id -u)" -ne 0 ] || { echo "run as a sudoer, not as root (config.sh refuses root)" >&2; exit 2; }

if [ -n "$slug" ]; then
  repo=${slug##*/}
  user="factory-$repo"
  home="/home/$user"
fi
# Directory under the home and label, per runner kind; the name is hub-<repo>[-checks].
kinds="runner:factory checks:checks"
dir_of() { echo "$home/$1"; }
name_of() { if [ "$1" = runner ]; then echo "hub-$repo"; else echo "hub-$repo-$1"; fi; }

# The service name svc.sh chose (actions.runner.<owner>-<repo>.<name>.service),
# from the file it writes in the runner directory.
service_of() { sudo cat "$1/.service" 2> /dev/null || true; }

# install_runner <kind> <label>: download when the directory has no runner,
# register unless it already is, install the service unless it exists, start.
install_runner() {
  local kind=$1 label=$2 dir name
  dir=$(dir_of "$kind"); name=$(name_of "$kind")
  sudo -u "$user" mkdir -p "$dir"

  if ! sudo test -x "$dir/config.sh"; then
    release=$(gh api repos/actions/runner/releases/latest --jq '{tag: .tag_name, body: .body}')
    ver=$(jq -r .tag <<< "$release"); ver=${ver#v}
    sum=$(jq -r .body <<< "$release" | grep -o 'BEGIN SHA linux-x64 -->[0-9a-f]\{64\}' | head -1 | grep -o '[0-9a-f]\{64\}$' || true)
    [ -n "$sum" ] || { echo "no linux-x64 checksum in the v$ver release notes" >&2; exit 1; }
    tarball="actions-runner-linux-x64-$ver.tar.gz"
    tmp=$(mktemp -d)
    curl -fsSL -o "$tmp/$tarball" "https://github.com/actions/runner/releases/download/v$ver/$tarball"
    echo "$sum  $tmp/$tarball" | sha256sum -c - > /dev/null
    chmod 644 "$tmp/$tarball"; chmod 755 "$tmp"
    sudo -u "$user" tar -xzf "$tmp/$tarball" -C "$dir"
    rm -rf "$tmp"
    echo "installed runner v$ver in $dir"
  fi

  # config.sh refuses to run twice; an existing registration is kept (remove
  # first to re-register). --replace covers a stale runner of the same name on
  # GitHub's side.
  if sudo test -f "$dir/.runner"; then
    echo "$name already configured; keeping its registration"
  else
    token=$(gh api -X POST "repos/$slug/actions/runners/registration-token" --jq .token)
    sudo -u "$user" env -C "$dir" ./config.sh --unattended --replace \
      --url "https://github.com/$slug" --token "$token" \
      --name "$name" --labels "$label" --work _work
  fi

  # svc.sh runs as root from the runner directory; the home is 750, so enter it as root.
  if [ -z "$(service_of "$dir")" ]; then
    sudo env -C "$dir" ./svc.sh install "$user"
  fi
  sudo env -C "$dir" ./svc.sh start
  echo "runner $name for $slug: $(systemctl is-active "$(service_of "$dir")")"
}

# remove_runner <kind>: stop and uninstall the service, unregister on GitHub.
remove_runner() {
  local kind=$1 dir
  dir=$(dir_of "$kind")
  sudo test -d "$dir" || return 0
  if [ -n "$(service_of "$dir")" ]; then
    sudo env -C "$dir" ./svc.sh stop || true
    sudo env -C "$dir" ./svc.sh uninstall
  fi
  if sudo test -f "$dir/.runner"; then
    token=$(gh api -X POST "repos/$slug/actions/runners/remove-token" --jq .token)
    sudo -u "$user" env -C "$dir" ./config.sh remove --token "$token"
  fi
}

add() {
  case "$(gh repo view "$slug" --json visibility --jq .visibility)" in
    PRIVATE|INTERNAL) ;;
    *) echo "refusing: $slug is public, and a self-hosted runner on a public repo runs forks' code" >&2; exit 2 ;;
  esac

  if ! id "$user" > /dev/null 2>&1; then
    sudo useradd -m -s /bin/bash "$user"
    echo "created user $user"
  fi
  sudo chmod 750 "$home"

  local k
  for k in $kinds; do install_runner "${k%%:*}" "${k##*:}"; done
}

remove() {
  local k
  for k in $kinds; do remove_runner "${k%%:*}"; done
  if id "$user" > /dev/null 2>&1; then
    sudo pkill -u "$user" || true   # a stopped service can leave the listener behind
    sleep 2
    sudo userdel -r "$user"
    echo "removed user $user and $home"
  fi
  echo "runners for $slug removed"
}

list() {
  local h k d u svc url
  for h in /home/factory-*; do
    u=$(basename "$h")
    for k in $kinds; do
      d="$h/${k%%:*}"
      sudo test -f "$d/.runner" || continue
      svc=$(service_of "$d")
      url=$(sudo jq -r .gitHubUrl "$d/.runner")
      printf '%s\t%s\t%s\t%s\n' "$u" "$(sudo jq -r .agentName "$d/.runner")" "${svc:-no service}" \
        "$(gh api "repos/${url#https://github.com/}/actions/runners" --jq ".runners[] | select(.name == \"$(sudo jq -r .agentName "$d/.runner")\") | \"\(.status) \([.labels[].name] | join(\",\"))\"" 2> /dev/null)"
    done
  done
}

"$cmd"
