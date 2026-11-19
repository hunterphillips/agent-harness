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
    changed = changed_paths(repo)
    # The task fixes only two locations: the export and the named test file.
    # Where the implementation lives inside the package is the agent's choice.
    def allowed(path: str) -> bool:
        return path == "tests/test_merge_layers.py" or (
            path.startswith("kvconfig/") and path.endswith(".py")
        )

    unexpected = sorted(path for path in changed if not allowed(path))
    required = {"kvconfig/__init__.py", "tests/test_merge_layers.py"}
    if unexpected or not required.issubset(changed):
        print(
            "FAIL touched files: expected kvconfig/*.py plus tests/test_merge_layers.py "
            f"(kvconfig/__init__.py and the test file required), got {changed}"
        )
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
        print("FAIL repository test suite")
        return 1

    probe = """
from kvconfig import merge_layers

first = {"Deploy-Env": "dev", "workers": 2, "keep": "yes"}
second = {"deploy env": "prod", "workers": None, "new-key": False}
actual = merge_layers((first, second))
assert actual == {"deploy_env": "prod", "keep": "yes", "new_key": False}, actual
assert first == {"Deploy-Env": "dev", "workers": 2, "keep": "yes"}
assert second == {"deploy env": "prod", "workers": None, "new-key": False}
for bad in ([{"ok": 1}, []], [{1: "no"}]):
    try:
        merge_layers(bad)
    except TypeError:
        pass
    else:
        raise AssertionError(f"expected TypeError for {bad!r}")
"""
    held_out = subprocess.run(
        [sys.executable, "-c", probe],
        cwd=repo,
        text=True,
        capture_output=True,
        env=env,
    )
    print(held_out.stdout, end="")
    print(held_out.stderr, end="")
    if held_out.returncode:
        print("FAIL held-out merge behavior")
        return 1
    print("PASS repository tests, held-out behavior, and touched-file allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
