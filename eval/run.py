#!/usr/bin/env python3
"""Blind pairwise capability evaluation harness.

Python 3.12+, standard library only. External programs are limited to the
agents under evaluation, the judge, git, and fixture check programs.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import json
import math
import os
import re
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
TOOLS = "Bash,Read,Edit,Write,Glob,Grep"
ARM_MODEL = "claude-opus-5"
JUDGE_MODEL = "gpt-5.6-sol"
JUDGE_REASONING_EFFORT = "high"
CLAUDE_LIMITS = {
    "writing": {
        "control": {"turns": 6, "budget": 1.00},
        "configured": {"turns": 12, "budget": 2.00},
    },
    "coding": {
        "control": {"turns": 20, "budget": 3.00},
        "configured": {"turns": 40, "budget": 6.00},
    },
}
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
        for task_dir in sorted(path for path in (EVAL_DIR / "tasks" / "coding").iterdir() if path.is_dir()):
            task_path = task_dir / "task.md"
            check_script = task_dir / "checks.py"
            fixture_repo = task_dir / "repo"
            if not (task_path.is_file() and check_script.is_file() and fixture_repo.is_dir()):
                raise ValueError(f"incomplete coding fixture: {task_dir}")
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
    exclude = workspace / ".git" / "info" / "exclude"
    with exclude.open("a", encoding="utf-8") as handle:
        handle.write("\n.claude/\n__pycache__/\n*.pyc\n.pytest_cache/\n.coverage\n")


def deploy_configuration(workspace: Path) -> None:
    target = workspace / ".claude"
    target.mkdir()
    for directory in ("agents", "skills", "output-styles"):
        shutil.copytree(ROOT / directory, target / directory)
    settings = json.loads((ROOT / "settings.json").read_text(encoding="utf-8"))
    settings["outputStyle"] = "Human Writer"
    (target / "settings.json").write_text(
        json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def make_agent_prompt(task: Task) -> str:
    if task.battery == "writing":
        source = f"\n\nSOURCE MATERIAL\n{task.source}" if task.source else ""
        return (
            "Complete the writing task below. Return only the requested final deliverable; "
            "do not describe your process.\n\n"
            f"TASK\n{task.prompt}{source}"
        )
    return (
        "Work directly in the current repository and complete the task below. "
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
    output = git(workspace, "status", "--porcelain=v1", "--untracked-files=all")
    paths: list[str] = []
    for line in output.splitlines():
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        if not raw.startswith(".claude/"):
            paths.append(raw)
    return sorted(paths)


def collect_code_artifact(workspace: Path, gate: dict[str, Any]) -> str:
    patch = git(workspace, "diff", "--no-ext-diff", "--no-color", "HEAD", "--", ".")
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
        f"PATCH\n{patch.strip() or '(no patch)'}\n\n"
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


def run_arm(task: Task, replicate: int, arm: str) -> dict[str, Any]:
    key = f"arm:{task.id}:{replicate}:{arm}"
    with tempfile.TemporaryDirectory(prefix="eval-candidate-") as temp:
        workspace = Path(temp)
        if task.fixture_repo is not None:
            shutil.copytree(task.fixture_repo, workspace, dirs_exist_ok=True)
        initialize_repo(workspace)
        if arm == "configured":
            deploy_configuration(workspace)

        # Writing tasks that ship a codebase need coding-scale turn/budget room
        # for the exploration phase; the artifact is still the response text.
        limit_battery = "coding" if task.fixture_repo is not None else task.battery
        limit = CLAUDE_LIMITS[limit_battery][arm]
        args = [
            "claude",
            "-p",
            "--model",
            ARM_MODEL,
            "--output-format",
            "json",
            "--no-session-persistence",
            "--dangerously-skip-permissions",
            "--setting-sources",
            "project",
            "--strict-mcp-config",
            "--no-chrome",
            "--tools",
            TOOLS,
            "--allowedTools",
            TOOLS,
            "--max-turns",
            str(limit["turns"]),
            "--max-budget-usd",
            f"{limit['budget']:.2f}",
        ]
        if arm == "control":
            args.append("--safe-mode")
        completed, wall_duration_ms = run_command(
            args, cwd=workspace, input_text=make_agent_prompt(task)
        )
        parse_error: str | None = None
        try:
            envelope = parse_claude_json(completed.stdout)
        except ValueError as error:
            parse_error = str(error)
            envelope = {}

        gate: dict[str, Any] | None = None
        if task.battery == "coding":
            gate = run_gate(task, workspace)
            artifact = collect_code_artifact(workspace, gate)
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
    schema = WRITING_SCHEMA if task.battery == "writing" else CODING_SCHEMA
    with tempfile.TemporaryDirectory(prefix="eval-review-") as temp:
        workspace = Path(temp)
        schema_path = workspace / "response-schema.json"
        message_path = workspace / "verdict.json"
        schema_path.write_text(json.dumps(schema), encoding="utf-8")
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
            "-",
        ]
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
    return first if first == second and first != "tie" else "tie"


def dimensions_for(battery: str) -> list[str]:
    if battery == "writing":
        return ["naturalness", "answer_first", "calibration", "clarity_concision", "faithfulness"]
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
            per_dimension = {dimension: "tie" for dimension in dimensions}
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
            "overall": "tie",
            "dimensions": {dimension: "tie" for dimension in dimensions},
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
    values = list(values)
    configured = values.count("configured")
    control = values.count("control")
    threshold = len(values) / 2
    if configured > threshold:
        return "configured"
    if control > threshold:
        return "control"
    return "tie"


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
        weighted = {name: 0.0 for name in ("configured", "control", "tie")}
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


def markdown_summary(metadata: dict[str, Any], aggregate_result: dict[str, Any]) -> str:
    quality = aggregate_result["quality"]
    overall = quality["overall"]
    rate = overall["configured_win_rate_decisive"]
    lines = [
        f"# {metadata['battery'].title()} eval — {metadata['run_id']}",
        "",
        f"Replicates: {metadata['replicates']} per task. A verdict is decisive only when both label orderings agree.",
        "",
        "## Quality",
        "",
        "| Dimension | Configured wins | Control wins | Ties | Configured win rate (decisive) |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    rows = [("Overall", overall), *[(name, value) for name, value in quality["dimensions"].items()]]
    for name, value in rows:
        counts = value["counts"]
        formatted_rate = "n/a" if value["configured_win_rate_decisive"] is None else f"{value['configured_win_rate_decisive']:.1%}"
        lines.append(
            f"| {name.replace('_', ' ').title()} | {counts['configured']} | {counts['control']} | "
            f"{counts['tie']} | {formatted_rate} |"
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


def metadata_for(run_id: str, battery: str, tasks: list[Task], replicates: int) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "battery": battery,
        "replicates": replicates,
        "task_ids": [task.id for task in tasks],
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "arm_model": ARM_MODEL,
        "judge_model": JUDGE_MODEL,
        "judge_reasoning_effort": JUDGE_REASONING_EFFORT,
        "position_swap": "both orderings per replicate; agreement required",
        "quality_verdict_excludes_efficiency": True,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--battery", required=True, choices=("writing", "coding"))
    parser.add_argument("--task", help="run one task id")
    parser.add_argument("--dry-run", action="store_true", help="show planned work without invoking a model")
    parser.add_argument("--replicates", type=int, default=3)
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

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = args.resume or dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    meta_path = RESULTS_DIR / f"{run_id}.meta.json"
    journal_path = RESULTS_DIR / f"{run_id}.records.jsonl"
    if args.resume:
        if not meta_path.exists():
            parser.error(f"resume metadata not found: {meta_path}")
        metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        expected = metadata_for(run_id, args.battery, tasks, args.replicates)
        for field in ("battery", "replicates", "task_ids"):
            if metadata.get(field) != expected[field]:
                parser.error(f"resume mismatch for {field}")
    else:
        if meta_path.exists() or journal_path.exists():
            parser.error(f"result id collision: {run_id}; retry in one second")
        metadata = metadata_for(run_id, args.battery, tasks, args.replicates)
        if args.rejudge:
            metadata["rejudged_from"] = args.rejudge
        meta_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    journal = Journal(journal_path)
    if args.rejudge:
        source_meta_path = RESULTS_DIR / f"{args.rejudge}.meta.json"
        source_journal_path = RESULTS_DIR / f"{args.rejudge}.records.jsonl"
        if not source_meta_path.exists() or not source_journal_path.exists():
            parser.error(f"rejudge source not found: {args.rejudge}")
        source_meta = json.loads(source_meta_path.read_text(encoding="utf-8"))
        for field in ("battery", "replicates", "task_ids"):
            if source_meta.get(field) != metadata[field]:
                parser.error(f"rejudge mismatch for {field}")
        for record in Journal(source_journal_path).records.values():
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
                        pending[executor.submit(run_arm, task, replicate, arm)] = arm
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
    markdown_path.write_text(markdown_summary(metadata, aggregate_result), encoding="utf-8")
    print(f"Wrote {json_path}")
    print(f"Wrote {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
