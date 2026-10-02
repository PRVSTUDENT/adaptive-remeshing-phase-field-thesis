#!/usr/bin/env python3
import difflib
from pathlib import Path

r6_path = Path("models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/f44_mixed_uel_restart_stateinit.for")
r7_path = Path("models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/f44_mixed_uel_restart_stateinit.for")

r6_lines = r6_path.read_text(encoding="utf-8").splitlines(keepends=True)
r7_lines = r7_path.read_text(encoding="utf-8").splitlines(keepends=True)

diff = list(difflib.unified_diff(r6_lines, r7_lines, fromfile="R6_f44", tofile="R7_f44", lineterm=""))

print("=== UNIFIED DIFF BETWEEN R6 AND R7 UEL ===")
for line in diff:
    print(line)

print("\n=== LINE BY LINE AUDIT & CLASSIFICATION ===")
for i, (l6, l7) in enumerate(zip(r6_lines, r7_lines), start=1):
    if l6 != l7:
        print(f"Line {i}:")
        print(f"  R6: {l6.strip()}")
        print(f"  R7: {l7.strip()}")
        if "PK10R1_INC29_" in l6 and "PK10R1_INC29_" in l7:
            print("  Classification: binary_filename_or_path_only")
        else:
            print("  Classification: UNRESOLVED")
