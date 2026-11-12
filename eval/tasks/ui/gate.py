"""Common UI floor checks; aesthetics belong to the screenshot judge."""
from __future__ import annotations

import subprocess
from pathlib import Path


def check(workspace: Path, fixture: Path) -> int:
    page = workspace / "index.html"
    if not page.is_file():
        print("FAIL index.html does not exist")
        return 1
    if page.read_bytes() == (fixture / "index.html").read_bytes():
        print("FAIL index.html was not changed from the fixture")
        return 1
    print("PASS index.html exists and was changed", flush=True)
    try:
        result = subprocess.run(
            ["node", str(Path(__file__).with_name("browser.cjs")), "check", str(workspace)],
            text=True,
            capture_output=True,
            timeout=100,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL browser check: {error}")
        return 1
    print(result.stdout, end="")
    print(result.stderr, end="")
    return 0 if result.returncode == 0 else 1
