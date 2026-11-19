#!/usr/bin/env python3
"""Score an audit's findings against the seeded fixture.

    check_report.py FINDINGS seeds.json

FINDINGS is a JSON list of objects with path, kind, severity and evidence.
A seed counts as found when a finding names one of its paths with its kind.
A finding on a clean control's path is a false positive. Exits non-zero when
fewer than 7 of the 8 seeds are found or any false positive exists.
"""
import json
import re
import sys

REQUIRED_SEEDS = 7


def normalize(path):
    """A finding's path without a leading ./ or a trailing :line or :start-end."""
    return re.sub(r":\d+(?:-\d+)?$", "", path.strip()).removeprefix("./")


def score(findings, seeds):
    named = {(normalize(f["path"]), f["kind"]) for f in findings}
    found = [d for d in seeds["defects"] if any((path, d["kind"]) in named for path in d["paths"])]
    missed = [d for d in seeds["defects"] if d not in found]
    controls = {path for control in seeds["controls"] for path in control["paths"]}
    false_positives = [f for f in findings if normalize(f["path"]) in controls]
    return found, missed, false_positives


def main(findings_path, seeds_path):
    with open(findings_path, encoding="utf-8") as handle:
        findings = json.load(handle)
    with open(seeds_path, encoding="utf-8") as handle:
        seeds = json.load(handle)
    found, missed, false_positives = score(findings, seeds)
    for label, defects in (("found", found), ("missed", missed)):
        for d in defects:
            print(f"{label}: seed {d['id']} {d['kind']} ({', '.join(d['paths'])})")
    for f in false_positives:
        print(f"false positive: {f['path']} {f['kind']} {f.get('severity')}: {f.get('evidence')}")
    passed = len(found) >= REQUIRED_SEEDS and not false_positives
    print(f"{len(found)} of {len(seeds['defects'])} seeds, {len(false_positives)} false positives: "
          f"{'pass' if passed else 'fail'}")
    return 0 if passed else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: check_report.py FINDINGS seeds.json")
    sys.exit(main(sys.argv[1], sys.argv[2]))
