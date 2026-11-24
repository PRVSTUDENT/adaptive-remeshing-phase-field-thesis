# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode1/293_method_c_case5/prepare_case5_coarse_decks.py
===========================================================================
Prepares:
1. PK_METHOD_C_CASE5_COARSE_JOB1.inp: Initial coarse solve deck targeting precritical u2 = 0.0050 mm.
2. PK_METHOD_C_CASE5_COARSE_PHYS.inp: Coarse physical mesh (2,566 elements, 2,688 nodes).
3. PK_METHOD_C_CASE5_ADAPTIVE_PHYS.inp: Adaptive physical mesh (15,708 elements, 16,094 nodes).
"""

import os
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_JOB1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.inp")
SRC_COARSE_PHYS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
SRC_ADAPT_PHYS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "293_method_c_case5")
OUT_JOB1 = os.path.join(OUT_DIR, "PK_METHOD_C_CASE5_COARSE_JOB1.inp")
OUT_COARSE_PHYS = os.path.join(OUT_DIR, "PK_METHOD_C_CASE5_COARSE_PHYS.inp")
OUT_ADAPT_PHYS = os.path.join(OUT_DIR, "PK_METHOD_C_CASE5_ADAPTIVE_PHYS.inp")


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    # 1. Prepare PK_METHOD_C_CASE5_COARSE_JOB1.inp
    with open(SRC_JOB1, "r") as f:
        lines = f.readlines()

    job1_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("*HEADING"):
            job1_lines.append("*HEADING\n")
            job1_lines.append("Method C Case 5 Coarse Model: PK_METHOD_C_CASE5_COARSE_JOB1\n")
            i += 2  # skip old heading lines
            continue

        if "STEP 2: Tension into localization regime" in line or (line.strip().startswith("*STEP") and "NAME=Step-2" in line):
            break  # End after Step 1

        job1_lines.append(line)
        i += 1

    with open(OUT_JOB1, "w") as f:
        f.writelines(job1_lines)
    print("Written %s (%d lines)" % (OUT_JOB1, len(job1_lines)))

    # 2. Copy coarse physical mesh
    shutil.copyfile(SRC_COARSE_PHYS, OUT_COARSE_PHYS)
    print("Copied coarse physical mesh to %s" % OUT_COARSE_PHYS)

    # 3. Copy adaptive physical mesh
    shutil.copyfile(SRC_ADAPT_PHYS, OUT_ADAPT_PHYS)
    print("Copied adaptive physical mesh to %s" % OUT_ADAPT_PHYS)


if __name__ == "__main__":
    main()
