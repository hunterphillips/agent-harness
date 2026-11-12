"""UI judge wiring checks; no model calls or browser required."""
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import run


class UIJudgeTests(unittest.TestCase):
    def test_image_labels_follow_both_candidate_orders(self):
        task = run.discover_tasks("ui")[0]
        with tempfile.TemporaryDirectory() as temp:
            arms = {}
            for arm in run.ARM_NAMES:
                screenshots = {}
                for size in ("desktop", "phone"):
                    path = Path(temp) / f"{arm}-{size}.png"
                    path.write_bytes(f"{arm} {size}".encode())
                    screenshots[size] = str(path)
                arms[arm] = {"result": f"<main>{arm} page content</main>", "screenshots": screenshots}

            for index, (first, second) in enumerate(run.POSITIONS, 1):
                def judge(args, *, cwd, input_text):
                    attached = [args[i + 1] for i, arg in enumerate(args) if arg == "-i"]
                    self.assertEqual([Path(path).name for path in attached], ["A-desktop.png", "A-phone.png", "B-desktop.png", "B-phone.png"])
                    expected = [f"{arm} {size}".encode() for arm in (first, second) for size in ("desktop", "phone")]
                    self.assertEqual([Path(path).read_bytes() for path in attached], expected)
                    self.assertLess(args.index("-"), args.index("-i"), "prompt `-` must precede the variadic -i flags")
                    self.assertIn("image 1 = A desktop", input_text)
                    self.assertIn("image 4 = B phone", input_text)
                    schema = json.loads(Path(args[args.index("--output-schema") + 1]).read_text())
                    self.assertEqual(schema["properties"]["criteria"]["required"], run.dimensions_for("ui"))
                    verdict = {"criteria": {}, "overall": {"winner": "A", "reason": "example", "flip_condition": "example"}}
                    Path(args[args.index("--output-last-message") + 1]).write_text(json.dumps(verdict))
                    return subprocess.CompletedProcess(args, 0, "", ""), 1

                with patch.object(run, "run_command", side_effect=judge):
                    result = run.run_judge(task, 1, index, first, second, arms[first], arms[second])
                self.assertEqual(result["label_map"], {"A": first, "B": second})
                self.assertIsNone(result["parse_error"])

            del arms["control"]["screenshots"]["phone"]
            with patch.object(run, "run_command") as command:
                with self.assertRaisesRegex(ValueError, "screenshots"):
                    run.run_judge(task, 1, 1, "configured", "control", arms["configured"], arms["control"])
                command.assert_not_called()

    def test_ui_gate_mismatch_still_requires_position_swap_agreement(self):
        task = run.discover_tasks("ui")[0]
        arms = {"configured": {"gate": {"passed": True}}, "control": {"gate": {"passed": False}}}
        judges = []
        for index, (first, second) in enumerate(run.POSITIONS, 1):
            label = "A" if first == "configured" else "B"
            judges.append({
                "order_index": index,
                "label_map": {"A": first, "B": second},
                "verdict": {
                    "criteria": {name: {"winner": label} for name in run.dimensions_for("ui")},
                    "overall": {"winner": label},
                },
            })
        result = run.reconcile_replicate(task, 1, arms, judges)
        self.assertEqual(result["overall"], "configured")
        self.assertEqual(result["basis"], "position_swap_agreement")
        judges[1]["verdict"]["overall"]["winner"] = "A"
        self.assertEqual(run.reconcile_replicate(task, 1, arms, judges)["overall"], "tie")
        self.assertEqual(run.reconcile_replicate(task, 1, arms, [])["basis"], "incomplete_judging")


if __name__ == "__main__":
    unittest.main()
