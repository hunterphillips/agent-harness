"""check_report.py's scoring: python3 eval/tasks/audit/test_check_report.py"""
import json
import unittest
from pathlib import Path

from check_report import score

SEEDS = json.loads((Path(__file__).resolve().parent / "seeded" / "seeds.json").read_text())


class Score(unittest.TestCase):
    def test_a_seed_needs_its_path_and_kind_and_a_control_is_a_false_positive(self):
        findings = [
            {"path": "pkg-core/src/storage.ts:7", "kind": "empty_catch", "severity": "Critical", "evidence": "x"},
            {"path": "pkg-core/src/pricing.ts", "kind": "duplication", "severity": "High", "evidence": "x"},
            {"path": "pkg-core/src/safe-write.ts", "kind": "empty_catch", "severity": "Low", "evidence": "x"},
        ]
        found, missed, false_positives = score(findings, SEEDS)
        self.assertEqual([d["id"] for d in found], [4])
        self.assertIn(3, [d["id"] for d in missed])
        self.assertEqual([f["path"] for f in false_positives], ["pkg-core/src/safe-write.ts"])


if __name__ == "__main__":
    unittest.main()
