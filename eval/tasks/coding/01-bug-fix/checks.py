#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# Set by the runner's initialize_repo at the fixture commit.
BASELINE_REF = "refs/eval/baseline"


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True).stdout


def changed_paths(repo: Path) -> list[str]:
    # Against the fixture baseline, so unstaged, staged and committed work count alike.
    tracked = git(repo, "diff", "--name-only", "--no-renames", BASELINE_REF)
    untracked = git(repo, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked.splitlines()) | set(untracked.splitlines()))


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    allowed = ["slugify.py"]
    changed = changed_paths(repo)
    if changed != allowed:
        print(f"FAIL touched files: expected {allowed}, got {changed}")
        return 1
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    tests = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=repo,
        text=True,
        capture_output=True,
        env=env,
    )
    print(tests.stdout, end="")
    print(tests.stderr, end="")
    if tests.returncode:
        print("FAIL regression suite")
        return 1
    print("PASS regression suite and touched-file allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
