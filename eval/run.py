#!/usr/bin/env python3
"""Blind pairwise capability evaluation harness.

Python 3.12+, standard library only. External programs are limited to the
agents under evaluation, the judge, git, and fixture check programs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import copy
import dataclasses
import datetime as dt
import hashlib
import json
import math
import os
import posixpath
import re
import shlex
import shutil
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = ROOT / "eval"
RESULTS_DIR = EVAL_DIR / "results"
ARM_NAMES = ("configured", "control")
POSITIONS = (("configured", "control"), ("control", "configured"))
# The fixture commit, kept as a ref so an arm amending that commit cannot move it.
BASELINE_REF = "refs/eval/baseline"
# Withheld from both arms: web access, and every tool that acts on the owner's
# account or reaches other sessions (schedules, triggers, notifications,
# messaging, worktrees, workflows, design sync).
WITHHELD_TOOLS = (
    "WebFetch",
    "WebSearch",
    "RemoteTrigger",
    "CronCreate",
    "CronDelete",
    "CronList",
    "PushNotification",
    "ScheduleWakeup",
    "DesignSync",
    "Workflow",
    "SendMessage",
    "ListAgents",
    "Monitor",
    "EnterWorktree",
    "ExitWorktree",
)
TOOL_FLAGS = ("--tools", "default", "--disallowedTools", ",".join(WITHHELD_TOOLS))
ARM_MODEL = "claude-opus-5"
JUDGE_MODEL = "gpt-5.6-sol"
JUDGE_REASONING_EFFORT = "high"
# Both arms share one ceiling per battery.
CLAUDE_LIMITS = {
    "writing": {"turns": 12, "budget": 2.00},
    "coding": {"turns": 40, "budget": 6.00},
}
# Every UI task's checks.py delegates to these.
UI_GATE_FILES = (EVAL_DIR / "tasks" / "ui" / "gate.py", EVAL_DIR / "tasks" / "ui" / "browser.cjs")
SKILL_PATH = re.compile(r"\.claude/skills/[^\s'\"`;|&()<>]+")
SKILL_DIRECTORY = re.compile(r"\.claude/skills(?:/\S*)?$")
SKILL_FILE_EXTENSIONS = (".md", ".py", ".sh", ".csv", ".json", ".cjs")
# This CLI names the subagent tool Task and accepts Agent as an alias.
SUBAGENT_TOOLS = {"Agent", "Task"}
# Identifying strings that must never reach the judge. Responses get them
# redacted (candidates may innocently use words like "bare" or "test harness",
# so those generic words are only banned in our own template text below).
RESPONSE_LEAK_PATTERNS = (
    re.compile(r"\.claude", re.IGNORECASE),
    re.compile(r"human writer", re.IGNORECASE),
    re.compile(r"skills[/\\](?:writing|coding)", re.IGNORECASE),
    re.compile(re.escape(str(ROOT)), re.IGNORECASE),
)
TEMPLATE_BLINDING_PATTERNS = RESPONSE_LEAK_PATTERNS + (
    re.compile(r"\bharness\b", re.IGNORECASE),
    re.compile(r"\bbare\b", re.IGNORECASE),
    re.compile(r"\bconfigured\b", re.IGNORECASE),
)


@dataclasses.dataclass(frozen=True)
class Task:
    id: str
    battery: str
    kind: str
    weight: float
    path: Path
    prompt: str
    source: str = ""
    fixture_repo: Path | None = None
    check_script: Path | None = None


class Journal:
    """Append-only, fsynced result journal used for interruption recovery."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.lock = threading.Lock()
        self.records: dict[str, dict[str, Any]] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                self.records[record["key"]] = record

    def get(self, key: str) -> dict[str, Any] | None:
        return self.records.get(key)

    def append(self, record: dict[str, Any]) -> None:
        payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
        with self.lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(payload + "\n")
                handle.flush()
                os.fsync(handle.fileno())
            self.records[record["key"]] = record


def parse_frontmatter(text: str, path: Path) -> tuple[dict[str, str], str]:
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"missing frontmatter: {path}")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if not separator:
            raise ValueError(f"invalid frontmatter line in {path}: {line!r}")
        fields[key.strip()] = value.strip()
    for required in ("id", "type", "weight"):
        if required not in fields:
            raise ValueError(f"missing {required!r} in {path}")
    return fields, text[match.end() :].strip()


def split_writing_body(body: str, path: Path) -> tuple[str, str]:
    marker = "## Fixed Source Input"
    if marker not in body:
        raise ValueError(f"missing {marker!r}: {path}")
    prompt_part, source = body.split(marker, 1)
    prompt = re.sub(r"\A## Task Prompt\s*", "", prompt_part).strip()
    source = source.strip()
    if source.lower().startswith("none") or source.lower() in {"n/a", "(none)"}:
        source = ""
    return prompt, source


def discover_tasks(battery: str) -> list[Task]:
    tasks: list[Task] = []
    if battery == "writing":
        base = EVAL_DIR / "tasks" / "writing"
        paths = list(base.glob("*.md")) + [
            entry / "task.md" for entry in base.iterdir() if entry.is_dir() and (entry / "task.md").is_file()
        ]
        for path in sorted(paths):
            fields, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
            prompt, source = split_writing_body(body, path)
            fixture = path.parent / "repo" if path.name == "task.md" else None
            tasks.append(
                Task(
                    id=fields["id"],
                    battery=battery,
                    kind=fields["type"],
                    weight=float(fields["weight"]),
                    path=path,
                    prompt=prompt,
                    source=source,
                    fixture_repo=fixture if fixture is not None and fixture.is_dir() else None,
                )
            )
    else:
        for task_dir in sorted(path for path in (EVAL_DIR / "tasks" / battery).iterdir() if path.is_dir()):
            if task_dir.name == "__pycache__":
                continue
            task_path = task_dir / "task.md"
            check_script = task_dir / "checks.py"
            fixture_repo = task_dir / "repo"
            if not (task_path.is_file() and check_script.is_file() and fixture_repo.is_dir()):
                raise ValueError(f"incomplete {battery} fixture: {task_dir}")
            fields, body = parse_frontmatter(task_path.read_text(encoding="utf-8"), task_path)
            prompt = re.sub(r"\A## Task Prompt\s*", "", body).strip()
            tasks.append(
                Task(
                    id=fields["id"],
                    battery=battery,
                    kind=fields["type"],
                    weight=float(fields["weight"]),
                    path=task_path,
                    prompt=prompt,
                    fixture_repo=fixture_repo,
                    check_script=check_script,
                )
            )
    if not tasks:
        raise ValueError(f"no {battery} tasks found")
    ids = [task.id for task in tasks]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate task id in {battery} battery")
    return tasks


def run_command(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    timeout: int = 900,
) -> tuple[subprocess.CompletedProcess[str], float]:
    started = time.monotonic()
    completed = subprocess.run(
        args,
        cwd=cwd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return completed, (time.monotonic() - started) * 1000


def git(workspace: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=workspace,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {completed.stderr.strip()}")
    return completed.stdout


def initialize_repo(workspace: Path) -> None:
    git(workspace, "init", "-q")
    git(workspace, "config", "user.name", "Eval Fixture")
    git(workspace, "config", "user.email", "eval@example.invalid")
    git(workspace, "add", ".")
    git(workspace, "commit", "-qm", "fixture baseline", "--allow-empty")
    git(workspace, "update-ref", BASELINE_REF, "HEAD")
    exclude = workspace / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write("\n.claude/\n__pycache__/\n*.pyc\n.pytest_cache/\n.coverage\n")


def deploy_configuration(workspace: Path, source: Path = ROOT) -> None:
    """Copy the config from source (a checkout of this repo) into workspace/.claude.
    settings.json is gitignored, so it always comes from this working tree."""
    target = workspace / ".claude"
    target.mkdir()
    for directory in ("agents", "skills", "output-styles"):
        shutil.copytree(source / directory, target / directory)
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    settings["outputStyle"] = "Human Writer"
    (target / "settings.json").write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def limits_for(task: Task) -> dict[str, float]:
    # Writing tasks that ship a codebase need coding-scale turn/budget room
    # for the exploration phase; the artifact is still the response text.
    return CLAUDE_LIMITS["coding" if task.fixture_repo is not None else task.battery]


def slash_command(task: Task, arm: str) -> str | None:
    # The configured arm invokes its skill explicitly, mirroring how the user
    # actually works (/writing …, /coding …). Control has no skills to invoke.
    if arm != "configured":
        return None
    return "/writing" if task.battery == "writing" else "/coding"


def make_agent_prompt(task: Task, arm: str) -> str:
    command = slash_command(task, arm)
    prefix = f"{command}\n" if command else ""
    if task.battery == "writing":
        source = f"\n\nSOURCE MATERIAL\n{task.source}" if task.source else ""
        return (
            f"{prefix}Complete the writing task below. Return only the requested final deliverable; "
            "do not describe your process.\n\n"
            f"TASK\n{task.prompt}{source}"
        )
    return (
        f"{prefix}Work directly in the current repository and complete the task below. "
        "Run relevant tests or checks available in the repository. Do not only explain a solution; "
        "make the requested file changes.\n\n"
        f"TASK\n{task.prompt}"
    )


def parse_claude_json(stdout: str) -> dict[str, Any]:
    candidates = [line for line in stdout.splitlines() if line.strip()]
    for candidate in reversed(candidates):
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and value.get("type") == "result":
            return value
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as error:
        raise ValueError("Claude output contained no result JSON object") from error
    if not isinstance(value, dict):
        raise ValueError("Claude output was not a JSON object")
    return value


def token_total(usage: dict[str, Any] | None) -> int | None:
    if not usage:
        return None
    if isinstance(usage.get("total_tokens"), (int, float)):
        return int(usage["total_tokens"])
    if "cached_input_tokens" in usage:
        values = [usage.get("input_tokens"), usage.get("output_tokens")]
        if any(isinstance(value, (int, float)) for value in values):
            return int(sum(value for value in values if isinstance(value, (int, float))))
    fields = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    values = [usage.get(field) for field in fields]
    if not any(isinstance(value, (int, float)) for value in values):
        return None
    return int(sum(value for value in values if isinstance(value, (int, float))))


def changed_paths(workspace: Path) -> list[str]:
    # Against the baseline rather than HEAD, so unstaged, staged and committed
    # work are judged alike.
    tracked = git(workspace, "diff", "--name-only", "--no-renames", BASELINE_REF, "--", ".")
    untracked = git(workspace, "ls-files", "--others", "--exclude-standard")
    paths = set(tracked.splitlines()) | set(untracked.splitlines())
    return sorted(path for path in paths if path and not path.startswith(".claude/"))


def collect_code_artifact(workspace: Path, gate: dict[str, Any], *, ui: bool = False) -> str:
    # Intent-to-add puts new files in the patch whether or not the arm committed them.
    git(workspace, "add", "--intent-to-add", ".")
    patch = git(workspace, "diff", "--no-ext-diff", "--no-color", BASELINE_REF, "--", ".")
    files = set(git(workspace, "ls-files").splitlines())
    files.update(changed_paths(workspace))
    sections: list[str] = []
    for relative in sorted(files):
        if relative.startswith((".git/", ".claude/")):
            continue
        path = workspace / relative
        if not path.is_file() or path.stat().st_size > 100_000:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        sections.append(f"### {relative}\n{content.rstrip()}")
    return (
        "DETERMINISTIC CHECK\n"
        f"passed: {str(gate['passed']).lower()}\n"
        f"details:\n{gate['details'].strip()}\n\n"
        + ("SCREENSHOTS\nDesktop (1280x800) and phone (390x844), full page, attached separately.\n\n" if ui else "")
        + f"PATCH\n{patch.strip() or '(no patch)'}\n\n"
        "CURRENT FILE CONTENTS\n"
        + "\n\n".join(sections)
    )


def run_gate(task: Task, workspace: Path) -> dict[str, Any]:
    assert task.check_script is not None
    completed, duration_ms = run_command(
        [sys.executable, str(task.check_script), str(workspace)],
        cwd=workspace,
        timeout=120,
    )
    details = (completed.stdout + completed.stderr).replace(str(workspace), "<workspace>")
    return {
        "passed": completed.returncode == 0,
        "exit_code": completed.returncode,
        "duration_ms": round(duration_ms, 3),
        "details": details.strip(),
        "changed_paths": changed_paths(workspace),
    }


def render_ui(workspace: Path, result_dir: Path) -> dict[str, str]:
    result_dir.mkdir(parents=True, exist_ok=True)
    completed, _ = run_command(
        ["node", str(EVAL_DIR / "tasks" / "ui" / "browser.cjs"), "render", str(workspace), str(result_dir)],
        cwd=EVAL_DIR,
        timeout=120,
    )
    if completed.returncode:
        raise RuntimeError(f"UI render failed: {completed.stdout}{completed.stderr}")
    return {size: str((result_dir / f"{size}.png").resolve()) for size in ("desktop", "phone")}


def parse_events(stdout: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def bash_skill_paths(command: str, directory: str | None) -> tuple[list[str], str | None]:
    """Skill paths a Bash command names, and the skill directory it leaves as cwd.

    Agents read workflow files as `cd .claude/skills/coding && cat tdd/tdd.md`,
    so a file argument after a `cd` into a skill directory resolves against it.
    Two known over-counts after such a `cd`: heredoc body lines are parsed as
    commands, and a redirect target (`> notes.md`) counts as a read.
    """
    paths: list[str] = []
    for segment in re.split(r"&&|\|\||[;|\n]", command):
        try:
            words = shlex.split(segment)
        except ValueError:
            words = segment.split()
        if not words:
            continue
        if words[0] == "cd":
            target = words[1] if len(words) > 1 else ""
            match = SKILL_DIRECTORY.search(target)
            if match:
                directory = posixpath.normpath(match.group(0))
            elif directory and target and not target.startswith(("/", "~", "-")):
                directory = path_if_in_skills_tree(posixpath.normpath(posixpath.join(directory, target)))
            else:
                directory = None
            continue
        for word in words[1:]:
            match = SKILL_PATH.search(word)
            if match:
                path = posixpath.normpath(match.group(0))
            elif directory and not word.startswith("-"):
                path = posixpath.normpath(posixpath.join(directory, word))
            else:
                continue
            # Only file arguments count; directories and search patterns do not.
            if path_if_in_skills_tree(path) and path.endswith(SKILL_FILE_EXTENSIONS):
                paths.append(path)
    return paths, directory


def path_if_in_skills_tree(path: str) -> str | None:
    return path if path == ".claude/skills" or path.startswith(".claude/skills/") else None


def summarize_trace(events: list[dict[str, Any]]) -> dict[str, Any]:
    """What an arm loaded, from its stream-json events (subagent events included)."""
    tools_available: list[str] = []
    skill_calls: list[str] = []
    skill_files_read: list[str] = []
    subagents = 0
    # A cd carries to the next Bash call in the main session only; a subagent's
    # shell resets on every call.
    main_directory: str | None = None
    for event in events:
        if event.get("type") == "system" and event.get("subtype") == "init":
            tools_available = event.get("tools", [])
        if event.get("type") != "assistant":
            continue
        in_subagent = event.get("parent_tool_use_id") is not None
        for block in event.get("message", {}).get("content", []):
            if block.get("type") != "tool_use":
                continue
            tool_input = block.get("input", {})
            if block["name"] == "Skill":
                skill_calls.append(tool_input.get("skill"))
            elif block["name"] in SUBAGENT_TOOLS:
                subagents += 1
            elif block["name"] == "Read":
                match = SKILL_PATH.search(tool_input.get("file_path", ""))
                if match:
                    skill_files_read.append(posixpath.normpath(match.group(0)))
            elif block["name"] == "Bash":
                paths, directory = bash_skill_paths(
                    tool_input.get("command", ""), None if in_subagent else main_directory
                )
                if not in_subagent:
                    main_directory = directory
                skill_files_read.extend(paths)
    return {
        "skill_calls": skill_calls,
        "skill_files_read": skill_files_read,
        "subagents": subagents,
        "tools_available": tools_available,
    }


def run_arm(task: Task, replicate: int, arm: str, result_dir: Path, model: str) -> dict[str, Any]:
    key = f"arm:{task.id}:{replicate}:{arm}"
    with tempfile.TemporaryDirectory(prefix="eval-candidate-") as temp:
        workspace = Path(temp)
        if task.fixture_repo is not None:
            shutil.copytree(task.fixture_repo, workspace, dirs_exist_ok=True)
        initialize_repo(workspace)
        if arm == "configured":
            deploy_configuration(workspace)

        limit = limits_for(task)
        args = [
            "claude",
            "-p",
            "--model",
            model,
            "--output-format",
            "stream-json",
            "--verbose",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--setting-sources",
            "project",
            "--strict-mcp-config",
            "--no-chrome",
            *TOOL_FLAGS,
            "--max-turns",
            str(limit["turns"]),
            "--max-budget-usd",
            f"{limit['budget']:.2f}",
        ]
        if arm == "control":
            args.append("--safe-mode")
        completed, wall_duration_ms = run_command(
            args, cwd=workspace, input_text=make_agent_prompt(task, arm)
        )
        result_dir.mkdir(parents=True, exist_ok=True)
        events_path = result_dir / "events.jsonl"
        events_path.write_text(completed.stdout, encoding="utf-8")
        parse_error: str | None = None
        try:
            envelope = parse_claude_json(completed.stdout)
        except ValueError as error:
            parse_error = str(error)
            envelope = {}

        gate: dict[str, Any] | None = None
        screenshots: dict[str, str] = {}
        if task.battery in ("coding", "ui"):
            gate = run_gate(task, workspace)
            if task.battery == "ui":
                # A render failure raises and aborts the run before the arm is
                # journaled, so --resume reruns the arm instead of keeping an
                # unjudgeable record.
                screenshots = render_ui(workspace, result_dir)
            artifact = collect_code_artifact(workspace, gate, ui=bool(screenshots))
        else:
            artifact = str(envelope.get("result", "")).strip()

        usage = envelope.get("usage") if isinstance(envelope.get("usage"), dict) else {}
        return {
            "key": key,
            "kind": "arm",
            "task_id": task.id,
            "replicate": replicate,
            "arm": arm,
            "exit_code": completed.returncode,
            "is_error": bool(envelope.get("is_error", completed.returncode != 0)),
            "parse_error": parse_error,
            "slash_command": slash_command(task, arm),
            **summarize_trace(parse_events(completed.stdout)),
            "events_path": str(events_path.resolve()),
            "result": artifact,
            "response_chars": len(artifact),
            "response_words": len(artifact.split()),
            "metrics": {
                "wall_duration_ms": round(wall_duration_ms, 3),
                "duration_ms": envelope.get("duration_ms"),
                "duration_api_ms": envelope.get("duration_api_ms"),
                "num_turns": envelope.get("num_turns"),
                "total_cost_usd": envelope.get("total_cost_usd"),
                "tokens": token_total(usage),
                "usage": usage,
                "model_usage": envelope.get("modelUsage"),
            },
            "gate": gate,
            "screenshots": screenshots,
            "stderr_tail": completed.stderr[-2000:],
            "captured_at": dt.datetime.now(dt.UTC).isoformat(),
        }


WRITING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "dims": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "winner": {"type": "string", "enum": ["A", "B", "Tie"]},
                        "evidence_a": {"type": "string"},
                        "evidence_b": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["winner", "evidence_a", "evidence_b", "reason"],
                }
                for name in (
                    "naturalness",
                    "answer_first",
                    "calibration",
                    "clarity_concision",
                    "faithfulness",
                )
            },
            "required": [
                "naturalness",
                "answer_first",
                "calibration",
                "clarity_concision",
                "faithfulness",
            ],
        },
        "overall": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "winner": {"type": "string", "enum": ["A", "B", "Tie"]},
                "reason": {"type": "string"},
            },
            "required": ["winner", "reason"],
        },
    },
    "required": ["dims", "overall"],
}

CODING_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "criteria": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                name: {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "a_score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "b_score": {"type": "integer", "minimum": 1, "maximum": 5},
                        "winner": {"type": "string", "enum": ["A", "B", "Tie"]},
                        "evidence_a": {"type": "string"},
                        "evidence_b": {"type": "string"},
                        "reason": {"type": "string"},
                    },
                    "required": ["a_score", "b_score", "winner", "evidence_a", "evidence_b", "reason"],
                }
                for name in ("correctness_scope", "simplicity", "style_consistency", "test_quality")
            },
            "required": ["correctness_scope", "simplicity", "style_consistency", "test_quality"],
        },
        "overall": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "winner": {"type": "string", "enum": ["A", "B", "Tie"]},
                "reason": {"type": "string"},
                "flip_condition": {"type": "string"},
            },
            "required": ["winner", "reason", "flip_condition"],
        },
    },
    "required": ["criteria", "overall"],
}

UI_DIMENSIONS = ("fit", "hierarchy", "distinctiveness", "responsive", "code")
UI_SCHEMA = copy.deepcopy(CODING_SCHEMA)
UI_SCHEMA["properties"]["criteria"]["properties"] = {
    name: copy.deepcopy(CODING_SCHEMA["properties"]["criteria"]["properties"]["simplicity"])
    for name in UI_DIMENSIONS
}
UI_SCHEMA["properties"]["criteria"]["required"] = list(UI_DIMENSIONS)


def judge_prompt(task: Task, response_a: str, response_b: str) -> str:
    rubric_path = EVAL_DIR / "judge" / f"{task.battery}-rubric.md"
    rubric = rubric_path.read_text(encoding="utf-8")
    source = task.source if task.source else "(No separate source material.)"
    template = rubric.replace("{{TASK_PROMPT}}", task.prompt).replace("{{SOURCE_INPUT}}", source)
    assert_blinded(template)
    return template.replace("{{RESPONSE_A}}", redact_leaks(response_a)).replace(
        "{{RESPONSE_B}}", redact_leaks(response_b)
    )


def redact_leaks(text: str) -> str:
    for pattern in RESPONSE_LEAK_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def assert_blinded(template: str) -> None:
    for pattern in TEMPLATE_BLINDING_PATTERNS:
        if pattern.search(template):
            raise ValueError(f"judge template failed blinding check: {pattern.pattern}")


def parse_codex_events(stdout: str) -> tuple[dict[str, Any], str | None]:
    usage: dict[str, Any] = {}
    last_message: str | None = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "turn.completed" and isinstance(event.get("usage"), dict):
            usage = event["usage"]
        item = event.get("item")
        if (
            event.get("type") == "item.completed"
            and isinstance(item, dict)
            and item.get("type") == "agent_message"
        ):
            last_message = item.get("text")
    return usage, last_message


def run_judge(
    task: Task,
    replicate: int,
    order_index: int,
    first_arm: str,
    second_arm: str,
    first_result: dict[str, Any],
    second_result: dict[str, Any],
) -> dict[str, Any]:
    key = f"judge:{task.id}:{replicate}:{order_index}"
    prompt = judge_prompt(task, first_result["result"], second_result["result"])
    schema = {"writing": WRITING_SCHEMA, "coding": CODING_SCHEMA, "ui": UI_SCHEMA}[task.battery]
    images: list[str] = []
    if task.battery == "ui":
        for result in (first_result, second_result):
            for size in ("desktop", "phone"):
                path = result.get("screenshots", {}).get(size)
                if not path or not Path(path).is_file():
                    raise ValueError("UI judging requires desktop and phone screenshots for both artifacts")
                images.append(path)
        prompt += (
            "\n\nAttached images in order: image 1 = A desktop (1280x800); "
            "image 2 = A phone (390x844); image 3 = B desktop (1280x800); "
            "image 4 = B phone (390x844). All are full-page screenshots."
        )
    with tempfile.TemporaryDirectory(prefix="eval-review-") as temp:
        workspace = Path(temp)
        schema_path = workspace / "response-schema.json"
        message_path = workspace / "verdict.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
        # Keep arm names out of attachment filenames as well as the prompt.
        attachments: list[Path] = []
        for source, name in zip(images, ("A-desktop", "A-phone", "B-desktop", "B-phone")):
            target = workspace / f"{name}.png"
            shutil.copyfile(source, target)
            attachments.append(target)
        args = [
            "codex",
            "exec",
            "--json",
            "--model",
            JUDGE_MODEL,
            "-c",
            f'model_reasoning_effort="{JUDGE_REASONING_EFFORT}"',
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--sandbox",
            "read-only",
            "--skip-git-repo-check",
            "-C",
            str(workspace),
            "--output-schema",
            str(schema_path),
            "--output-last-message",
            str(message_path),
        ]
        # The prompt positional goes before the image flags: `-i` is variadic
        # and would swallow a trailing `-` as a fifth image path.
        args.append("-")
        for path in attachments:
            args.extend(["-i", str(path)])
        completed, wall_duration_ms = run_command(args, cwd=workspace, input_text=prompt)
        usage, event_message = parse_codex_events(completed.stdout)
        raw_message = message_path.read_text(encoding="utf-8") if message_path.exists() else event_message
        verdict: dict[str, Any] | None = None
        parse_error: str | None = None
        if raw_message:
            try:
                candidate = json.loads(raw_message)
                if isinstance(candidate, dict):
                    verdict = candidate
                else:
                    parse_error = "judge response was not a JSON object"
            except json.JSONDecodeError as error:
                parse_error = f"invalid judge JSON: {error}"
        else:
            parse_error = "judge produced no final message"
        return {
            "key": key,
            "kind": "judge",
            "task_id": task.id,
            "replicate": replicate,
            "order_index": order_index,
            "label_map": {"A": first_arm, "B": second_arm},
            "exit_code": completed.returncode,
            "verdict": verdict,
            "parse_error": parse_error,
            "metrics": {
                "wall_duration_ms": round(wall_duration_ms, 3),
                "tokens": token_total(usage),
                "usage": usage,
                "total_cost_usd": None,
            },
            "stderr_tail": completed.stderr[-2000:],
            "captured_at": dt.datetime.now(dt.UTC).isoformat(),
        }


def mapped_winner(winner: str, label_map: dict[str, str]) -> str:
    if winner == "Tie":
        return "tie"
    return label_map[winner]


def agreed_winner(first: str, second: str) -> str:
    """Both label orders must agree. Agreeing on no winner is a tie; disagreeing is no verdict."""
    return first if first == second else "no_verdict"


def dimensions_for(battery: str) -> list[str]:
    if battery == "writing":
        return ["naturalness", "answer_first", "calibration", "clarity_concision", "faithfulness"]
    if battery == "ui":
        return list(UI_DIMENSIONS)
    return ["correctness_scope", "simplicity", "style_consistency", "test_quality"]


def reconcile_replicate(
    task: Task,
    replicate: int,
    arms: dict[str, dict[str, Any]],
    judges: list[dict[str, Any]],
) -> dict[str, Any]:
    dimensions = dimensions_for(task.battery)
    if task.battery == "coding":
        first_pass = bool(arms["configured"].get("gate", {}).get("passed"))
        second_pass = bool(arms["control"].get("gate", {}).get("passed"))
        if first_pass != second_pass:
            winner = "configured" if first_pass else "control"
            # Judging is skipped, so no other dimension has a verdict.
            per_dimension = {dimension: "no_verdict" for dimension in dimensions}
            per_dimension["correctness_scope"] = winner
            return {
                "replicate": replicate,
                "overall": winner,
                "dimensions": per_dimension,
                "basis": "deterministic_gate",
            }

    if len(judges) != 2 or any(not record.get("verdict") for record in judges):
        return {
            "replicate": replicate,
            "overall": "no_verdict",
            "dimensions": {dimension: "no_verdict" for dimension in dimensions},
            "basis": "incomplete_judging",
        }

    mapped: list[dict[str, str]] = []
    for record in sorted(judges, key=lambda item: item["order_index"]):
        verdict = record["verdict"]
        dim_key = "dims" if task.battery == "writing" else "criteria"
        per_dimension = {
            name: mapped_winner(verdict[dim_key][name]["winner"], record["label_map"])
            for name in dimensions
        }
        mapped.append(
            {
                "overall": mapped_winner(verdict["overall"]["winner"], record["label_map"]),
                **per_dimension,
            }
        )
    return {
        "replicate": replicate,
        "overall": agreed_winner(mapped[0]["overall"], mapped[1]["overall"]),
        "dimensions": {
            name: agreed_winner(mapped[0][name], mapped[1][name]) for name in dimensions
        },
        "basis": "position_swap_agreement",
    }


def majority(values: Iterable[str]) -> str:
    """The outcome of more than half the replicates; no majority, or no replicates, is no verdict."""
    values = list(values)
    for outcome in ("configured", "control", "tie"):
        if values.count(outcome) > len(values) / 2:
            return outcome
    return "no_verdict"


def metric_stats(records: list[dict[str, Any]], field: str) -> dict[str, float | int | None]:
    values = [record["metrics"].get(field) for record in records]
    numeric = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    if not numeric:
        return {"n": 0, "mean": None, "stddev": None, "min": None, "max": None}
    return {
        "n": len(numeric),
        "mean": statistics.fmean(numeric),
        "stddev": statistics.pstdev(numeric),
        "min": min(numeric),
        "max": max(numeric),
    }


def aggregate(tasks: list[Task], records: list[dict[str, Any]], replicates: int) -> dict[str, Any]:
    arm_records = [record for record in records if record["kind"] == "arm"]
    judge_records = [record for record in records if record["kind"] == "judge"]
    task_results: list[dict[str, Any]] = []
    for task in tasks:
        replicate_results: list[dict[str, Any]] = []
        for replicate in range(1, replicates + 1):
            arms = {
                record["arm"]: record
                for record in arm_records
                if record["task_id"] == task.id and record["replicate"] == replicate
            }
            judges = [
                record
                for record in judge_records
                if record["task_id"] == task.id and record["replicate"] == replicate
            ]
            if set(arms) == set(ARM_NAMES):
                replicate_results.append(reconcile_replicate(task, replicate, arms, judges))
        dimension_results = {
            dimension: majority(result["dimensions"][dimension] for result in replicate_results)
            for dimension in dimensions_for(task.battery)
        }
        task_results.append(
            {
                "task_id": task.id,
                "weight": task.weight,
                "winner": majority(result["overall"] for result in replicate_results),
                "dimensions": dimension_results,
                "replicates": replicate_results,
            }
        )

    def win_summary(field: str | None = None) -> dict[str, Any]:
        winners = [result["winner"] if field is None else result["dimensions"][field] for result in task_results]
        weighted = {name: 0.0 for name in ("configured", "control", "tie", "no_verdict")}
        counts = {name: winners.count(name) for name in weighted}
        for task, winner in zip(tasks, winners, strict=True):
            weighted[winner] += task.weight
        decisive_weight = weighted["configured"] + weighted["control"]
        return {
            "counts": counts,
            "weighted_counts": weighted,
            "configured_win_rate_decisive": (
                weighted["configured"] / decisive_weight if decisive_weight else None
            ),
        }

    metrics: dict[str, Any] = {}
    for arm in ARM_NAMES:
        selected = [record for record in arm_records if record["arm"] == arm]
        metrics[arm] = {
            field: metric_stats(selected, field)
            for field in ("tokens", "wall_duration_ms", "duration_ms", "num_turns", "total_cost_usd")
        }
    deltas: dict[str, float | None] = {}
    for field in ("tokens", "wall_duration_ms", "duration_ms", "num_turns", "total_cost_usd"):
        configured = metrics["configured"][field]["mean"]
        control = metrics["control"][field]["mean"]
        deltas[field] = configured - control if configured is not None and control is not None else None

    return {
        "task_results": task_results,
        "quality": {
            "overall": win_summary(),
            "dimensions": {dimension: win_summary(dimension) for dimension in dimensions_for(tasks[0].battery)},
        },
        "efficiency": {"arms": metrics, "configured_minus_control": deltas},
    }


def fmt_number(value: float | int | None, digits: int = 2) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value:.{digits}f}"


def loaded_summary(record: dict[str, Any]) -> list[str]:
    """Markdown cells for what one arm loaded; records journaled before tracing show n/a."""
    if "skill_files_read" not in record:
        return ["n/a"] * 5
    files = record["skill_files_read"]
    distinct = list(dict.fromkeys(path.removeprefix(".claude/skills/") for path in files))
    return [
        record["slash_command"] or "none",
        ", ".join(record["skill_calls"]) or "none",
        f"{len(files)}" + (f": {', '.join(distinct)}" if distinct else ""),
        str(record["subagents"]),
        str(len(record["tools_available"])),
    ]


def tool_difference(records: list[dict[str, Any]]) -> str | None:
    """One line naming tools offered to one arm and not the other."""
    tools = {arm: set() for arm in ARM_NAMES}
    for record in records:
        tools[record["arm"]].update(record.get("tools_available", []))
    if not all(tools.values()):
        return None
    only = {arm: sorted(tools[arm] - tools[other]) for arm, other in (ARM_NAMES, ARM_NAMES[::-1])}
    if not any(only.values()):
        return "Same tools in both arms."
    return " ".join(
        f"Only {arm}: {', '.join(names)}." for arm, names in only.items() if names
    )


def markdown_summary(
    metadata: dict[str, Any], aggregate_result: dict[str, Any], records: list[dict[str, Any]]
) -> str:
    quality = aggregate_result["quality"]
    overall = quality["overall"]
    lines = [
        f"# {metadata['battery'].title()} eval — {metadata['run_id']}",
        "",
        f"Replicates: {metadata['replicates']} per task. A replicate is decided only when both label orderings agree; "
        "a missing judge result or disagreeing orderings is no verdict.",
        "",
        "## Quality",
        "",
        "| Dimension | Configured wins | Control wins | Ties | No verdict | Configured win rate (decisive) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    rows = [("Overall", overall), *[(name, value) for name, value in quality["dimensions"].items()]]
    for name, value in rows:
        counts = value["counts"]
        formatted_rate = "n/a" if value["configured_win_rate_decisive"] is None else f"{value['configured_win_rate_decisive']:.1%}"
        lines.append(
            f"| {name.replace('_', ' ').title()} | {counts['configured']} | {counts['control']} | "
            f"{counts['tie']} | {counts['no_verdict']} | {formatted_rate} |"
        )
    lines.extend(
        [
            "",
            "## Per-task verdicts",
            "",
            "| Task | Weight | Winner |",
            "| --- | ---: | --- |",
        ]
    )
    for task in aggregate_result["task_results"]:
        lines.append(f"| {task['task_id']} | {task['weight']:g} | {task['winner']} |")
    lines.extend(
        [
            "",
            "## What each arm loaded",
            "",
            "| Task | Replicate | Arm | Slash command | Skill calls | Skill files read | Subagents | Tools |",
            "| --- | ---: | --- | --- | --- | --- | ---: | ---: |",
        ]
    )
    arm_records = sorted(
        (record for record in records if record["kind"] == "arm"),
        key=lambda record: (metadata["task_ids"].index(record["task_id"]), record["replicate"], record["arm"]),
    )
    for record in arm_records:
        cells = [record["task_id"], str(record["replicate"]), record["arm"], *loaded_summary(record)]
        lines.append("| " + " | ".join(cells) + " |")
    difference = tool_difference(arm_records)
    if difference:
        lines.extend(["", difference])
    lines.extend(
        [
            "",
            "## Efficiency (quality-neutral)",
            "",
            "| Metric | Configured mean ± stddev | Control mean ± stddev | Delta |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    labels = {
        "tokens": "Tokens",
        "wall_duration_ms": "Wall duration (ms)",
        "duration_ms": "Reported duration (ms)",
        "num_turns": "Turns",
        "total_cost_usd": "Cost (USD)",
    }
    for field, label in labels.items():
        configured = aggregate_result["efficiency"]["arms"]["configured"][field]
        control = aggregate_result["efficiency"]["arms"]["control"][field]
        delta = aggregate_result["efficiency"]["configured_minus_control"][field]
        lines.append(
            f"| {label} | {fmt_number(configured['mean'])} ± {fmt_number(configured['stddev'])} | "
            f"{fmt_number(control['mean'])} ± {fmt_number(control['stddev'])} | {fmt_number(delta)} |"
        )
    return "\n".join(lines) + "\n"


def print_dry_run(tasks: list[Task], replicates: int) -> None:
    comparisons = 0
    print(f"Battery: {tasks[0].battery}")
    print(f"Replicates: {replicates}")
    print("Tasks:")
    for task in tasks:
        print(f"  - {task.id} ({task.kind}, weight={task.weight:g})")
        for replicate in range(1, replicates + 1):
            print(f"    replicate {replicate}: paired Claude invocations [configured, control]")
            print("      judge order 1: candidate A / candidate B")
            print("      judge order 2: candidate B / candidate A")
            comparisons += 2
    print(f"Planned arm invocations: {len(tasks) * replicates * 2}")
    print(f"Maximum judge invocations: {comparisons} (coding gate mismatches skip judging)")
    print("Dry run: no agent or judge command was executed and no result file was written.")


def tree_digest(files: Iterable[tuple[str, bytes]]) -> str:
    """sha256 over (name, content) pairs in name order."""
    digest = hashlib.sha256()
    for name, content in sorted(files):
        digest.update(name.encode() + b"\0" + hashlib.sha256(content).digest())
    return digest.hexdigest()


def files_under(root: Path) -> list[tuple[str, bytes]]:
    """Files under root, without OS and bytecode litter that varies between machines."""
    return [
        (path.relative_to(root).as_posix(), path.read_bytes())
        for path in root.rglob("*")
        if path.is_file()
        and path.name != ".DS_Store"
        and path.suffix != ".pyc"
        and "__pycache__" not in path.parts
    ]


def task_digest(task: Task) -> str:
    # The rendered prompts, so a change to the prompt builder or slash prefix shows.
    named = [(f"prompt/{arm}", make_agent_prompt(task, arm).encode()) for arm in ARM_NAMES]
    files = [*([task.check_script] if task.check_script else [])]
    if task.battery == "ui":
        files.extend(UI_GATE_FILES)
    named.extend((path.relative_to(EVAL_DIR).as_posix(), path.read_bytes()) for path in files)
    if task.fixture_repo is not None:
        named.extend(
            (f"{task.fixture_repo.relative_to(EVAL_DIR).as_posix()}/{name}", content)
            for name, content in files_under(task.fixture_repo)
        )
    return tree_digest(named)


def fingerprint(tasks: list[Task], model: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="eval-config-") as temp:
        deploy_configuration(Path(temp))
        config = tree_digest(files_under(Path(temp) / ".claude"))
    version = subprocess.run(["claude", "--version"], text=True, capture_output=True, check=True).stdout
    return {
        "config_sha256": config,
        "tasks": {task.id: {"sha256": task_digest(task), "ceilings": limits_for(task)} for task in tasks},
        "model": model,
        "claude_version": version.strip(),
        "tool_flags": list(TOOL_FLAGS),
    }


def fingerprint_differences(stored: dict[str, Any], current: dict[str, Any]) -> list[str]:
    differences = [
        label
        for field, label in (
            ("config_sha256", "config tree"),
            ("model", "model"),
            ("claude_version", "CLI version"),
            ("tool_flags", "tool flags"),
        )
        if stored.get(field) != current[field]
    ]
    for task_id, entry in current["tasks"].items():
        previous = stored.get("tasks", {}).get(task_id, {})
        if previous.get("sha256") != entry["sha256"]:
            differences.append(f"{task_id} prompt/fixture/checks")
        if previous.get("ceilings") != entry["ceilings"]:
            differences.append(f"{task_id} ceilings")
    return differences


def metadata_for(run_id: str, battery: str, tasks: list[Task], replicates: int, model: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "battery": battery,
        "replicates": replicates,
        "task_ids": [task.id for task in tasks],
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "arm_model": model,
        "judge_model": JUDGE_MODEL,
        "judge_reasoning_effort": JUDGE_REASONING_EFFORT,
        "position_swap": "both orderings per replicate; agreement required",
        "quality_verdict_excludes_efficiency": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--battery", required=True, choices=("writing", "coding", "ui"))
    parser.add_argument("--task", help="run one task id")
    parser.add_argument("--dry-run", action="store_true", help="show planned work without invoking a model")
    parser.add_argument("--replicates", type=int, default=3)
    parser.add_argument("--model", default=ARM_MODEL, help=f"model for both arms (default: {ARM_MODEL})")
    parser.add_argument("--resume", metavar="RUN_ID", help="continue an interrupted run journal")
    parser.add_argument(
        "--rejudge",
        metavar="RUN_ID",
        help="new run reusing a prior run's journaled arm outputs; only the judging re-runs",
    )
    args = parser.parse_args(argv)
    if args.replicates < 1:
        parser.error("--replicates must be at least 1")
    if args.rejudge and args.resume:
        parser.error("--rejudge cannot be combined with --resume")

    tasks = discover_tasks(args.battery)
    if args.task:
        tasks = [task for task in tasks if task.id == args.task]
        if not tasks:
            parser.error(f"unknown task for {args.battery} battery: {args.task}")
    if args.dry_run:
        print_dry_run(tasks, args.replicates)
        return 0

    for executable in ("claude", "codex", "git"):
        if shutil.which(executable) is None:
            parser.error(f"required executable not found: {executable}")
    if args.battery == "ui" and shutil.which("node") is None:
        parser.error("required executable not found: node (see eval/README.md for UI setup)")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = args.resume or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    meta_path = RESULTS_DIR / f"{run_id}.meta.json"
    journal_path = RESULTS_DIR / f"{run_id}.records.jsonl"
    if args.resume:
        if not meta_path.exists():
            parser.error(f"resume metadata not found: {meta_path}")
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        expected = metadata_for(run_id, args.battery, tasks, args.replicates, args.model)
        for field in ("battery", "replicates", "task_ids"):
            if metadata.get(field) != expected[field]:
                parser.error(f"resume mismatch for {field}")
        # Arms from another config, task, model, CLI, or ceiling are not comparable.
        # A rejudge run's arms are fixed; only its judging resumes.
        if "rejudged_from" not in metadata:
            if "fingerprint" not in metadata:
                parser.error(
                    "resume refused: the run predates fingerprints, so its arms ran under other tools and prompts"
                )
            differences = fingerprint_differences(metadata["fingerprint"], fingerprint(tasks, args.model))
            if differences:
                parser.error(f"resume refused: fingerprint differs in {', '.join(differences)}")
    else:
        if meta_path.exists() or journal_path.exists():
            parser.error(f"result id collision: {run_id}; retry in one second")
        metadata = metadata_for(run_id, args.battery, tasks, args.replicates, args.model)
        if args.rejudge:
            source_meta_path = RESULTS_DIR / f"{args.rejudge}.meta.json"
            source_journal_path = RESULTS_DIR / f"{args.rejudge}.records.jsonl"
            if not source_meta_path.exists() or not source_journal_path.exists():
                parser.error(f"rejudge source not found: {args.rejudge}")
            source_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
            for field in ("battery", "replicates", "task_ids"):
                if source_meta.get(field) != metadata[field]:
                    parser.error(f"rejudge mismatch for {field}")
            # The arms, and so their model and fingerprint, belong to the source run.
            metadata["rejudged_from"] = args.rejudge
            metadata["arm_model"] = source_meta["arm_model"]
            metadata["fingerprint"] = source_meta.get("fingerprint")
        else:
            metadata["fingerprint"] = fingerprint(tasks, args.model)
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    journal = Journal(journal_path)
    if args.rejudge:
        for record in Journal(RESULTS_DIR / f"{args.rejudge}.records.jsonl").records.values():
            if record["kind"] == "arm" and not journal.get(record["key"]):
                journal.append(record)

    for task in tasks:
        for replicate in range(1, args.replicates + 1):
            arm_records: dict[str, dict[str, Any]] = {}
            pending: dict[concurrent.futures.Future[dict[str, Any]], str] = {}
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                for arm in ARM_NAMES:
                    key = f"arm:{task.id}:{replicate}:{arm}"
                    existing = journal.get(key)
                    if existing:
                        arm_records[arm] = existing
                    else:
                        result_dir = RESULTS_DIR / run_id / task.id / str(replicate) / arm
                        pending[executor.submit(run_arm, task, replicate, arm, result_dir, args.model)] = arm
                for future in concurrent.futures.as_completed(pending):
                    arm = pending[future]
                    record = future.result()
                    journal.append(record)
                    arm_records[arm] = record
                    print(f"captured {record['key']}", flush=True)

            gates = [arm_records[arm].get("gate") for arm in ARM_NAMES]
            gate_mismatch = task.battery == "coding" and bool(gates[0]["passed"]) != bool(gates[1]["passed"])
            if gate_mismatch:
                print(f"skipped judging {task.id} replicate {replicate}: deterministic gate decides", flush=True)
                continue
            for order_index, (first_arm, second_arm) in enumerate(POSITIONS, start=1):
                key = f"judge:{task.id}:{replicate}:{order_index}"
                if journal.get(key):
                    continue
                record = run_judge(
                    task,
                    replicate,
                    order_index,
                    first_arm,
                    second_arm,
                    arm_records[first_arm],
                    arm_records[second_arm],
                )
                journal.append(record)
                print(f"captured {record['key']}", flush=True)

    records = list(journal.records.values())
    aggregate_result = aggregate(tasks, records, args.replicates)
    final = {"metadata": metadata, "aggregate": aggregate_result, "records": records}
    json_path = RESULTS_DIR / f"{run_id}.json"
    markdown_path = RESULTS_DIR / f"{run_id}.md"
    json_path.write_text(json.dumps(final, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(markdown_summary(metadata, aggregate_result, records), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
