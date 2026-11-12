#!/usr/bin/env python3
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gate import check

if __name__ == "__main__":
    raise SystemExit(check(Path(sys.argv[1]).resolve(), Path(__file__).resolve().parent / "repo"))
