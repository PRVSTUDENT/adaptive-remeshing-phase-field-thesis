# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode2/294_method_c_mode2/prepare_mode2_coarse_decks.py
=========================================================================
Prepares canonical coarse decks for Method C Mode-II:
1. PK_METHOD_C_MODE2_COARSE_JOB1.inp: Initial coarse solve deck targeting pre-peak u1 = 0.0095 mm.
2. PK_METHOD_C_MODE2_COARSE_PHYS.inp: Coarse physical mesh (2,960 elements, 3,036 nodes).
"""

import os
import re

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "Job-1_UEL_paper_horizon.inp")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "294_method_c_mode2")
OUT_JOB1 = os.path.join(OUT_DIR, "PK_METHOD_C_MODE2_COARSE_JOB1.inp")
OUT_PHYS = os.path.join(OUT_DIR, "PK_METHOD_C_MODE2_COARSE_PHYS.inp")


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    with open(SRC_INP, "r") as f:
        lines = f.readlines()

    # 1. Prepare PK_METHOD_C_MODE2_COARSE_JOB1.inp
    # Retain Step 1 targeting ux = 0.0095 mm (initiation)
    job1_lines = []
    i = 0
    in_step2 = False

    while i < len(lines):
        line = lines[i]
        if line.startswith("*Heading") or line.startswith("*HEADING"):
            job1_lines.append("*Heading\n")
            job1_lines.append("** Method C Mode-II Coarse Model: PK_METHOD_C_MODE2_COARSE_JOB1\n")
            # skip until next keyword
            i += 1
            while i < len(lines) and not lines[i].startswith("*"):
                i += 1
            continue

        if "STEP 2:" in line or "name=Step-2" in line:
            in_step2 = True

        if in_step2:
            # We only need Step 1 for Cycle 0 coarse solve
            i += 1
            continue

        # The legacy Mode-II deck used E,nu,Gc,l0. The mandated frozen
        # source reads l0,Gc,E,nu,k,N_PHYS, irrespective of comment labels.
        if line.strip().upper().startswith('*UEL PROPERTY'):
            job1_lines.append(line)
            job1_lines.append('0.015, 0.0027, 210.0, 0.3, 1.0e-7, 2960.\n')
            i += 2
            continue

        # Avoid field-output time points silently forcing 1000 increments
        # when the declared coarse stepping is 0.005 (200 increments).
        if line.strip().lower().startswith('*output, field, time interval='):
            job1_lines.append('*Output, field, time interval=0.005\n')
            i += 1
            continue

        # Adjust Step 1 terminal displacement to 0.0095 mm
        if line.strip().startswith("N_RP, 1, 1, 0.0100"):
            job1_lines.append("N_RP, 1, 1, 0.0095\n")
            i += 1
            continue

        # Use efficient time stepping for Cycle 0
        if line.strip().startswith("5.0E-4, 1.0, 1.0E-9, 5.0E-4"):
            job1_lines.append("0.005, 1.0, 1.0E-9, 0.005\n")
            i += 1
            continue

        job1_lines.append(line)
        i += 1

    with open(OUT_JOB1, "w") as f:
        f.writelines(job1_lines)
    print("Written %s (%d lines)" % (OUT_JOB1, len(job1_lines)))

    # 2. Prepare PK_METHOD_C_MODE2_COARSE_PHYS.inp
    # Extract only physical nodes and Layer 1 elements (1..2960) with sets
    phys_lines = []
    phys_lines.append("*Heading\n")
    phys_lines.append("** Method C Mode-II Coarse Physical Mesh: PK_METHOD_C_MODE2_COARSE_PHYS\n")
    phys_lines.append("** 2960 physical elements (2860 quads, 100 tris), 3036 nodes\n")

    in_nodes = False
    in_phase_quads = False
    in_phase_tris = False
    in_nsets = False

    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.startswith("*"):
            u = s.upper()
            in_nodes = u.startswith("*NODE")
            in_phase_quads = ("*ELEMENT" in u and "ELSET=PHASE_QUADS" in u)
            in_phase_tris = ("*ELEMENT" in u and "ELSET=PHASE_TRIS" in u)
            in_nsets = u.startswith("*NSET") or u.startswith("*ELSET")

            # Skip mech and umat layers
            if "MECH_" in u or "UMAT_" in u or "*EQUATION" in u or "*STEP" in u or "*USER ELEMENT" in u:
                continue

            if in_phase_quads:
                phys_lines.append("*ELEMENT, TYPE=CPE4, ELSET=ALLELEMENTS\n")
                continue
            if in_phase_tris:
                phys_lines.append("*ELEMENT, TYPE=CPE3, ELSET=ALLELEMENTS\n")
                continue

            if in_nodes or in_nsets:
                phys_lines.append(line)
                continue
        else:
            if in_nodes:
                # Exclude reference point 999999 from physical mesh
                if s.startswith("999999,"):
                    continue
                phys_lines.append(line)
            elif in_phase_quads or in_phase_tris:
                phys_lines.append(line)
            elif in_nsets:
                phys_lines.append(line)

    with open(OUT_PHYS, "w") as f:
        f.writelines(phys_lines)
    print("Written %s (%d lines)" % (OUT_PHYS, len(phys_lines)))


if __name__ == "__main__":
    main()
