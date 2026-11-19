"""metrics.py against the seeded fixture: python3 eval/tasks/audit/test_metrics.py -v

Needs git, uvx and npx. The first run fetches the pinned tools.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
METRICS = HERE.parents[2] / "skills" / "coding" / "architecture-audit" / "metrics.py"
sys.path[:0] = [str(HERE / "seeded"), str(METRICS.parent)]
import build  # noqa: E402
import metrics  # noqa: E402

SEEDS = json.loads((HERE / "seeded" / "seeds.json").read_text())
DEFECTS = {seed["id"]: seed for seed in SEEDS["defects"]}
CONTROL_PATHS = {path for control in SEEDS["controls"] for path in control["paths"]}


def measure(repo, *args):
    proc = subprocess.run([sys.executable, str(METRICS), str(repo), *args], capture_output=True, text=True, check=True)
    return proc.stdout


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def clone_files(snap):
    return {side.rsplit(":", 1)[0] for clone in snap["details"]["clones"] for side in (clone["first"], clone["second"])}


def flagged_paths(snap):
    details = snap["details"]
    locations = details["empty_catch_candidates"] + details["skipped_tests"] + details["test_files_without_assertions"]
    return ({location.split(":")[0] for location in locations} | clone_files(snap)
            | {f["path"] for f in details["functions_over_ccn_15"]})


class SeededFixture(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.repo = Path(cls.tmp.name) / "fixture"
        build.build(cls.repo)
        cls.snap = json.loads(measure(cls.repo))
        cls.status_after = git(cls.repo, "status", "--porcelain", "--ignored")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_measuring_leaves_no_file_in_the_fixture(self):
        self.assertEqual(self.status_after, "")

    def test_generated_files_are_not_sources(self):
        self.assertEqual(self.snap["metrics"]["files"], 15)
        self.assertEqual(self.snap["generated_files"], 2)

    def test_complex_function(self):
        seed = DEFECTS[3]
        self.assertEqual(self.snap["metrics"]["functions_over_ccn_15"], 1)
        [function] = self.snap["details"]["functions_over_ccn_15"]
        self.assertEqual((function["path"], function["name"], function["ccn"]),
                         (seed["paths"][0], seed["function"], seed["ccn"]))

    def test_complex_file_ranks_first_among_hotspots(self):
        self.assertEqual(self.snap["details"]["hotspots"][0]["path"], DEFECTS[3]["paths"][0])

    def test_function_copied_into_three_files(self):
        self.assertTrue(set(DEFECTS[2]["paths"]) <= clone_files(self.snap))

    def test_duplicated_block_in_large_file(self):
        path = DEFECTS[8]["paths"][0]
        self.assertEqual(len((self.repo / path).read_text().splitlines()), DEFECTS[8]["lines"])
        self.assertIn(path, clone_files(self.snap))

    def test_empty_catch(self):
        seed = DEFECTS[4]
        self.assertEqual(self.snap["details"]["empty_catch_candidates"], [f"{seed['paths'][0]}:{seed['line']}"])

    def test_test_without_assertions(self):
        self.assertEqual(self.snap["details"]["test_files_without_assertions"], DEFECTS[5]["paths"])

    def test_suppressions_and_skipped_test(self):
        seed = DEFECTS[6]
        self.assertEqual(self.snap["metrics"]["suppressions"]["@ts-ignore"], seed["ts_ignore"])
        self.assertEqual(self.snap["metrics"]["skipped_tests"], seed["skipped_tests"])
        self.assertTrue(self.snap["details"]["skipped_tests"][0].startswith(seed["paths"][1] + ":"))

    def test_cycle_is_found_only_with_the_alias_resolved(self):
        core = next(p for p in self.snap["packages"] if p["path"] == "pkg-core")
        self.assertEqual(core["madge"]["cycles"], [DEFECTS[1]["paths"]])
        files = [path.removeprefix("pkg-core/") for path in git(self.repo / "pkg-core", "ls-files", "*.ts").split()
                 if "/gen/" not in path]
        cycles, unresolved = metrics.madge_cycles(self.repo / "pkg-core", files, tsconfig=None)
        self.assertEqual(cycles, [])
        self.assertIn("@core/inventory", unresolved)

    def test_knip_without_node_modules_is_null_with_a_reason(self):
        self.assertIsNone(self.snap["metrics"]["unused_files"])
        for package in self.snap["packages"]:
            self.assertIsNone(package["knip"]["unused_files"])
            self.assertIn("node_modules", package["knip"]["skipped"])

    def test_clean_controls_are_not_flagged(self):
        self.assertFalse(flagged_paths(self.snap) & CONTROL_PATHS)


class History(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "fixture"
        self.history = Path(self.tmp.name) / "metrics.jsonl"
        build.build(self.repo)

    def tearDown(self):
        self.tmp.cleanup()

    def compare(self):
        return json.loads(subprocess.run([sys.executable, str(METRICS), "--compare", str(self.history)],
                                         capture_output=True, text=True, check=True).stdout)

    def test_untracked_file_is_counted_and_two_snapshots_compare(self):
        measure(self.repo, "--append", str(self.history))
        self.assertIsNone(self.compare()["comparison"])
        (self.repo / "pkg-core" / "src" / "extra.ts").write_text("export const extra = 1;\n")
        measure(self.repo, "--append", str(self.history))
        result = self.compare()
        self.assertEqual(result["changes"]["files"], {"before": 15, "after": 16, "change": 1,
                                                      "relative_change": round(1 / 15, 4)})
        self.assertIsNone(result["changes"]["suppressions.as any"]["relative_change"])
        self.assertIn("unused_files", [entry["metric"] for entry in result["not_comparable"]])

    def test_backfill_measures_three_ancestors_and_removes_its_worktrees(self):
        worktrees = git(self.repo, "worktree", "list")
        measure(self.repo, "--backfill", "90", "--points", "3", "--append", str(self.history))
        self.assertEqual(git(self.repo, "worktree", "list"), worktrees)
        history = [json.loads(line) for line in self.history.read_text().splitlines()]
        self.assertEqual([snap["kind"] for snap in history], ["history"] * 3)
        dates = [snap["date"] for snap in history]
        self.assertEqual(dates, sorted(set(dates)))
        audit = json.loads(measure(self.repo, "--append", str(self.history)))
        self.assertNotEqual(history[0]["metrics"]["files_per_commit_p90"], audit["metrics"]["files_per_commit_p90"])
        self.assertIn("cycles", [entry["metric"] for entry in self.compare()["not_comparable"]])


if __name__ == "__main__":
    unittest.main()
