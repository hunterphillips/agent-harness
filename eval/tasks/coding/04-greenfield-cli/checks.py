#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


def status_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return sorted(line[3:].split(" -> ")[-1] for line in result.stdout.splitlines())


def invoke(repo: Path, args: list[str], stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "csv2json.py", *args],
        cwd=repo,
        input=stdin,
        text=True,
        capture_output=True,
        env=env,
    )


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    changed = status_paths(repo)
    if not changed or set(changed) - {"csv2json.py", "test_csv2json.py"} or "csv2json.py" not in changed:
        print(f"FAIL touched files: expected csv2json.py and optional test_csv2json.py, got {changed}")
        return 1

    with tempfile.TemporaryDirectory(prefix="csv-cases-") as temp:
        cases = Path(temp)
        standard = cases / "people.csv"
        standard.write_text('name,city,note\nAda,London,"likes tea"\nMina,Seoul,"a,b"\n', encoding="utf-8")
        semicolon = cases / "stock.csv"
        semicolon.write_text("sku;count;zone\nA1;04;east\nB2;0;west\n", encoding="utf-8")

        first = invoke(repo, [str(standard)])
        if first.returncode != 0 or json.loads(first.stdout) != [
            {"name": "Ada", "city": "London", "note": "likes tea"},
            {"name": "Mina", "city": "Seoul", "note": "a,b"},
        ]:
            print("FAIL held-out default array invocation")
            print(first.stderr)
            return 1

        second = invoke(repo, ["--delimiter", ";", "--select", "zone,sku", str(semicolon)])
        if second.returncode != 0 or json.loads(second.stdout) != [
            {"zone": "east", "sku": "A1"},
            {"zone": "west", "sku": "B2"},
        ]:
            print("FAIL held-out delimiter/select invocation")
            print(second.stderr)
            return 1

        third = invoke(repo, ["--ndjson", "-"], standard.read_text(encoding="utf-8"))
        try:
            lines = [json.loads(line) for line in third.stdout.splitlines()]
        except json.JSONDecodeError:
            lines = []
        if third.returncode != 0 or lines != [
            {"name": "Ada", "city": "London", "note": "likes tea"},
            {"name": "Mina", "city": "Seoul", "note": "a,b"},
        ]:
            print("FAIL held-out ndjson invocation")
            print(third.stderr)
            return 1

        fourth = invoke(repo, ["--select", "absent", str(standard)])
        if fourth.returncode != 2 or "absent" not in fourth.stderr:
            print("FAIL missing-column error behavior")
            return 1

    if (repo / "test_csv2json.py").exists():
        tests = subprocess.run(
            [sys.executable, "-m", "unittest", "-v", "test_csv2json.py"],
            cwd=repo,
            text=True,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        print(tests.stdout, end="")
        print(tests.stderr, end="")
        if tests.returncode:
            print("FAIL agent-written tests")
            return 1
    print("PASS four held-out invocations, error behavior, and touched-file allowlist")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
