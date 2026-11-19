#!/usr/bin/env python3
"""Run the architecture audit headless on a fresh seeded fixture and score it.

    run_audit.py [--ref REF] [--model MODEL] OUT_DIR

The config comes from this working tree, or from git ref REF through a
temporary worktree; settings.json always comes from this working tree. The
agent runs as eval/run.py runs a configured arm. OUT_DIR receives the raw
events, the reply, thoughts/shared/audits/ (report and metrics history),
audit-findings.json and summary.json. Exits with check_report.py's status.
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "seeded"), str(HERE.parents[1])]
import build  # noqa: E402
import check_report  # noqa: E402
from run import (ARM_MODEL, ROOT, claude_arm_args, deploy_configuration, parse_claude_json,  # noqa: E402
                 parse_events, run_command, summarize_trace)

SEEDS = HERE / "seeded" / "seeds.json"
TURNS = 80
BUDGET = 8.00
TIMEOUT = 3600
PROMPT = (
    "/coding Run an architecture audit of this repository. This is an unattended run: make the calls the "
    "workflow supports and do not ask questions. When the audit is done, also write every finding to "
    "audit-findings.json in the repository root as a JSON list of objects with fields path, kind, severity, "
    "evidence, where kind is one of: {kinds}."
)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


def prepare(workspace, ref, tmp):
    build.build(workspace)
    with open(workspace / ".git" / "info" / "exclude", "a", encoding="utf-8") as handle:
        handle.write("\n.claude/\nthoughts/\n")
    (workspace / "thoughts" / "shared").mkdir(parents=True)
    if ref is None:
        deploy_configuration(workspace)
    else:
        config = Path(tmp) / "config"
        git(ROOT, "worktree", "add", "--detach", "--quiet", str(config), ref)
        try:
            deploy_configuration(workspace, source=config)
        finally:
            git(ROOT, "worktree", "remove", "--force", str(config))
    status = git(workspace, "status", "--porcelain")
    if status:
        raise RuntimeError(f"fixture not clean before the run:\n{status}")


def mentions(events, name):
    """Whether any tool call names the file; catches a path held in a shell variable, which summarize_trace misses."""
    return any(name in json.dumps(block.get("input", {}))
               for event in events if event.get("type") == "assistant"
               for block in event.get("message", {}).get("content", []) if block.get("type") == "tool_use")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", help="deploy the config from this git ref instead of the working tree")
    parser.add_argument("--model", default=ARM_MODEL)
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    kinds = ", ".join(json.loads(SEEDS.read_text())["kinds"])

    with tempfile.TemporaryDirectory(prefix="audit-run-") as tmp:
        workspace = Path(tmp) / "fixture"
        prepare(workspace, args.ref, tmp)
        try:
            completed, _ = run_command(claude_arm_args(args.model, TURNS, BUDGET), cwd=workspace,
                                       input_text=PROMPT.format(kinds=kinds), timeout=TIMEOUT)
            stdout, exit_code = completed.stdout, completed.returncode
        except subprocess.TimeoutExpired as error:
            stdout, exit_code = error.stdout or "", f"timed out after {TIMEOUT} s"
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
        # Keep the artifacts before anything can fail on a broken or partial run.
        (args.out_dir / "events.jsonl").write_text(stdout, encoding="utf-8")
        audits = workspace / "thoughts" / "shared" / "audits"
        if audits.is_dir():
            shutil.copytree(audits, args.out_dir / "audits", dirs_exist_ok=True)
        if (workspace / "audit-findings.json").is_file():
            shutil.copy(workspace / "audit-findings.json", args.out_dir)

    try:
        envelope = parse_claude_json(stdout)
    except ValueError:
        envelope = {}
    (args.out_dir / "reply.md").write_text(str(envelope.get("result", "")), encoding="utf-8")
    events = parse_events(stdout)
    trace = summarize_trace(events)
    summary = {"ref": args.ref or "working tree", "model": args.model, "exit_code": exit_code,
               "turns": envelope.get("num_turns"), "cost_usd": envelope.get("total_cost_usd"),
               "skill_calls": trace["skill_calls"], "skill_files_read": trace["skill_files_read"],
               "workflow_used": mentions(events, "architecture-audit.md"), "metrics_used": mentions(events, "metrics.py")}
    (args.out_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"turns: {summary['turns']}, cost: ${summary['cost_usd']}")
    print(f"workflow used: {summary['workflow_used']}, metrics.py used: {summary['metrics_used']}")
    findings = args.out_dir / "audit-findings.json"
    if not findings.is_file():
        print("no audit-findings.json written: fail")
        return 1
    return check_report.main(findings, SEEDS)


if __name__ == "__main__":
    sys.exit(main())
