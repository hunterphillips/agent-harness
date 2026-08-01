#!/usr/bin/env python3
from __future__ import annotations

import ast
import hashlib
import os
import subprocess
import sys
from pathlib import Path


EXPECTED_PUBLIC = {
    "add_item": ["self", "description", "quantity", "unit_price"],
    "subtotal": ["self"],
    "tax": ["self"],
    "total": ["self"],
    "render": ["self"],
}
EXPECTED_INIT_ARGS = ["self", "customer", "tax_rate", "discount_rate"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def status_paths(repo: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=repo,
        text=True,
        capture_output=True,
        check=True,
    )
    return sorted(line[3:].split(" -> ")[-1] for line in result.stdout.splitlines())


def main() -> int:
    repo = Path(sys.argv[1]).resolve()
    changed = status_paths(repo)
    if changed != ["invoice/report.py"]:
        print(f"FAIL touched files: expected ['invoice/report.py'], got {changed}")
        return 1

    baseline_test = subprocess.run(
        ["git", "show", "HEAD:tests/test_report.py"],
        cwd=repo,
        capture_output=True,
        check=True,
    ).stdout
    if hashlib.sha256(baseline_test).hexdigest() != digest(repo / "tests" / "test_report.py"):
        print("FAIL test file changed")
        return 1

    tree = ast.parse((repo / "invoice" / "report.py").read_text(encoding="utf-8"))
    class_node = next((node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "InvoiceReport"), None)
    if class_node is None:
        print("FAIL InvoiceReport class missing")
        return 1
    methods = {node.name: node for node in class_node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
    public = {name for name in methods if not name.startswith("_")}
    if public != set(EXPECTED_PUBLIC):
        print(f"FAIL public API changed: {sorted(public)}")
        return 1
    for name, expected_args in EXPECTED_PUBLIC.items():
        actual_args = [argument.arg for argument in methods[name].args.args]
        if actual_args != expected_args:
            print(f"FAIL signature changed for {name}: {actual_args}")
            return 1
    if "__init__" not in methods or [argument.arg for argument in methods["__init__"].args.args] != EXPECTED_INIT_ARGS:
        print("FAIL constructor signature changed")
        return 1
    if "_totals" not in methods:
        print("FAIL private _totals helper missing")
        return 1
    for name in ("subtotal", "tax", "total", "render"):
        calls_helper = any(
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "self"
            and node.func.attr == "_totals"
            for node in ast.walk(methods[name])
        )
        if not calls_helper:
            print(f"FAIL {name} does not use _totals")
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
    print("PASS regression suite, public API invariant, shared helper, and untouched tests")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
