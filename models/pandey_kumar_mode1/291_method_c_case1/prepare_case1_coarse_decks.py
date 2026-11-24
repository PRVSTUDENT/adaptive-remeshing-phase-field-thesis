# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode1/291_method_c_case1/prepare_case1_coarse_decks.py
===========================================================================
Prepares:
1. PK_METHOD_C_CASE1_COARSE_JOB1.inp: Initial coarse solve deck targeting peak load u2 = 0.0058 mm.
2. PK_METHOD_C_CASE1_COARSE_PHYS.inp: Coarse physical mesh (2,906 elements, 2,988 nodes).
"""

import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1768_case1_donor", "PK_F1768_CASE_1_COARSE_COUPLED.inp")
OUT_JOB1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "291_method_c_case1", "PK_METHOD_C_CASE1_COARSE_JOB1.inp")
OUT_PHYS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "291_method_c_case1", "PK_METHOD_C_CASE1_COARSE_PHYS.inp")


def main():
    with open(SRC_INP, "r") as f:
        lines = f.readlines()

    # 1. Prepare PK_METHOD_C_CASE1_COARSE_JOB1.inp
    job1_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("*HEADING"):
            job1_lines.append("*HEADING\n")
            job1_lines.append("Method C Case 1 Coarse Model: PK_METHOD_C_CASE1_COARSE_JOB1\n")
            i += 2  # skip old heading
            continue
        # In Step 2, target u2 = 0.0058 mm to capture initiation and peak
        if line.strip().startswith("N_RP, 2, 2, 0.0100"):
            job1_lines.append("N_RP, 2, 2, 0.0058\n")
            i += 1
            continue
        job1_lines.append(line)
        i += 1

    with open(OUT_JOB1, "w") as f:
        f.writelines(job1_lines)
    print("Written %s (%d lines)" % (OUT_JOB1, len(job1_lines)))

    # 2. Prepare PK_METHOD_C_CASE1_COARSE_PHYS.inp
    nodes = []
    quads = []
    tris = []

    in_nodes = False
    in_phase_quad = False
    in_phase_tri = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.startswith("*"):
            u = s.upper()
            in_nodes = u.startswith("*NODE")
            in_phase_quad = ("*ELEMENT" in u and "TYPE=U1" in u)
            in_phase_tri = ("*ELEMENT" in u and "TYPE=U3" in u)
            continue
        if in_nodes:
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if len(parts) >= 3:
                nid = int(parts[0])
                if nid != 999999:  # exclude reference node
                    nodes.append(line)
        elif in_phase_quad:
            quads.append(line)
        elif in_phase_tri:
            tris.append(line)

    phys_lines = [
        "** ============================================================\n",
        "** Method C Case 1 Coarse Physical Mesh\n",
        "** Benchmark: Pandey & Kumar (2025) Section 4.1 Mode-I Plate\n",
        "** Statistics: %d nodes, %d elements (%d quads, %d tris, %.2f%% quad)\n" % (
            len(nodes), len(quads) + len(tris), len(quads), len(tris),
            100.0 * len(quads) / (len(quads) + len(tris))
        ),
        "** ============================================================\n",
        "*NODE\n"
    ]
    phys_lines.extend(nodes)
    phys_lines.append("*ELEMENT, TYPE=CPE4, ELSET=E_QUAD\n")
    phys_lines.extend(quads)
    if tris:
        phys_lines.append("*ELEMENT, TYPE=CPE3, ELSET=E_TRI\n")
        phys_lines.extend(tris)
    phys_lines.append("*ELSET, ELSET=ALL_ELEMENTS\nE_QUAD,\n")
    if tris:
        phys_lines.append("E_TRI,\n")

    with open(OUT_PHYS, "w") as f:
        f.writelines(phys_lines)
    print("Written %s (%d nodes, %d elements)" % (OUT_PHYS, len(nodes), len(quads) + len(tris)))


if __name__ == "__main__":
    main()
