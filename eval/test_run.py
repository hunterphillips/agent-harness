"""Runner checks that need no model calls."""
import json
import unittest
from pathlib import Path

import run

FIXTURES = Path(__file__).parent / "fixtures" / "trace"


def load(name):
    return [json.loads(line) for line in (FIXTURES / name).read_text(encoding="utf-8").splitlines()]


class TraceTests(unittest.TestCase):
    def test_real_configured_trace(self):
        # Recorded from a configured coding-01 arm sent `/coding`: the slash
        # command expands inline, so no Skill call appears, and the workflow
        # file is read as `cd /workspace/.claude/skills/coding && cat diagnose/diagnose.md`.
        trace = run.summarize_trace(load("configured-coding-01.jsonl"))
        self.assertEqual(trace["skill_calls"], [])
        self.assertEqual(trace["skill_files_read"], [".claude/skills/coding/diagnose/diagnose.md"])
        self.assertEqual(trace["subagents"], 0)
        self.assertIn("Skill", trace["tools_available"])

    def test_synthetic_parser_cases(self):
        # Hand-written, not recorded: `ls` of a skill directory, cd into the
        # skills root, a relative cd from inside a skill, a grep pattern that
        # looks like a filename, and one subagent call under each tool name.
        trace = run.summarize_trace(load("synthetic-parser-cases.jsonl"))
        self.assertEqual(
            trace["skill_files_read"],
            [
                ".claude/skills/coding/SKILL.md",
                ".claude/skills/coding/tdd/tdd.md",
                ".claude/skills/coding/tdd/tdd.md",
            ],
        )
        self.assertEqual(trace["subagents"], 2)


class VerdictTests(unittest.TestCase):
    def test_tie_and_no_verdict_stay_distinct(self):
        task = run.discover_tasks("coding")[0]
        arms = {arm: {"gate": {"passed": True}} for arm in run.ARM_NAMES}

        def judges(first_winner, second_winner):
            records = []
            for index, (winner, (first, second)) in enumerate(zip((first_winner, second_winner), run.POSITIONS), 1):
                records.append({
                    "order_index": index,
                    "label_map": {"A": first, "B": second},
                    "verdict": {
                        "criteria": {name: {"winner": winner} for name in run.dimensions_for("coding")},
                        "overall": {"winner": winner},
                    },
                })
            return records

        tie = run.reconcile_replicate(task, 1, arms, judges("Tie", "Tie"))
        self.assertEqual(tie["overall"], "tie")
        self.assertEqual(set(tie["dimensions"].values()), {"tie"})
        # "A" in both orders names a different arm each time: the orders disagree.
        disagree = run.reconcile_replicate(task, 2, arms, judges("A", "A"))
        self.assertEqual(disagree["overall"], "no_verdict")
        self.assertEqual(set(disagree["dimensions"].values()), {"no_verdict"})
        self.assertEqual(run.reconcile_replicate(task, 3, arms, judges("Tie", "B"))["overall"], "no_verdict")
        self.assertEqual(run.reconcile_replicate(task, 4, arms, judges("Tie", "Tie")[:1])["overall"], "no_verdict")

        tasks = run.discover_tasks("coding")[:2]
        records = []
        for task, (first, second) in zip(tasks, (("Tie", "Tie"), ("A", "A"))):
            for arm in run.ARM_NAMES:
                records.append({"kind": "arm", "task_id": task.id, "replicate": 1, "arm": arm,
                                "gate": {"passed": True}, "metrics": {}})
            for record in judges(first, second):
                records.append({"kind": "judge", "task_id": task.id, "replicate": 1, **record})
        result = run.aggregate(tasks, records, 1)
        self.assertEqual([task["winner"] for task in result["task_results"]], ["tie", "no_verdict"])
        counts = result["quality"]["overall"]["counts"]
        self.assertEqual((counts["tie"], counts["no_verdict"]), (1, 1))
        self.assertEqual(result["quality"]["dimensions"]["simplicity"]["counts"]["no_verdict"], 1)

        # Task level: tie needs a majority of ties; a split or nothing completed is no verdict.
        self.assertEqual(run.majority(["tie", "tie", "configured"]), "tie")
        self.assertEqual(run.majority(["configured", "control", "no_verdict"]), "no_verdict")
        self.assertEqual(run.majority([]), "no_verdict")


if __name__ == "__main__":
    unittest.main()
