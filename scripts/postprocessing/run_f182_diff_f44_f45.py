#!/usr/bin/env python3
"""
F182 Audit F44 vs F45 Source Code Diff
Generate line-by-line diff between f44 and f45 UEL subroutines.
"""

import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BASE_DIR = ROOT / "models/generated/mode_ii/production_control_batch"
F44_PATH = BASE_DIR / "f44_mixed_uel_restart_stateinit.for"
F45_PATH = BASE_DIR / "f45_mixed_uel_restart_irreversible.for"

def main():
    with open(F44_PATH) as f:
        f44_lines = f.readlines()
    with open(F45_PATH) as f:
        f45_lines = f.readlines()

    diff = list(difflib.unified_diff(
        f44_lines, f45_lines,
        fromfile="f44_mixed_uel_restart_stateinit.for",
        tofile="f45_mixed_uel_restart_irreversible.for",
        n=3
    ))

    print("================================================================================")
    print("F44 vs F45 UNIFIED SOURCE DIFF & CLASSIFICATION")
    print("================================================================================")
    for line in diff:
        print(line, end="")

if __name__ == "__main__":
    main()
