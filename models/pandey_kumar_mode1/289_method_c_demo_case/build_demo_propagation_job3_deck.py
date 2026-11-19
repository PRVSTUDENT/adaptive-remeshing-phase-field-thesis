# -*- coding: utf-8 -*-
"""
build_demo_propagation_job3_deck.py
===================================
Generates the Abaqus/Standard input deck for Job-3:
Model: PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp
Task: METHOD-C-PHASE3-FORWARD-PROPAGATION-PACKAGE

Simulation Architecture:
- Discretization: Refined receiver mesh (10,299 physical / 30,897 layered elements)
- Initial Conditions: Transferred state and history H0 (SVARS 9..12) via *INITIAL CONDITIONS, TYPE=SOLUTION
- Step 1 (Re-Equilibrate):
    * Initial ramp / fixed-load re-equilibration to u2 = 0.0050 mm
    * Reconstructs exact equilibrium state verified in Job 2 (Exit 0, 0 cutbacks, RF2 = 0.548386 kN)
- Step 2 (Forward Crack Propagation):
    * Positive displacement continuation from u2 = 0.0050 mm to u2 = 0.0100 mm
    * Initial dt = 0.10, max dt = 0.20 (4-6 nominal increments across step), min dt = 1e-8
    * Traces crack propagation from initial notch tip (0.5, 0.5) mm toward the central hole at (0.75, 0.5) mm
"""
from __future__ import print_function
import os
import sys
import hashlib

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
JOB2_INP = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp")
JOB3_INP = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp")


def build_job3_deck():
    if not os.path.exists(JOB2_INP):
        raise RuntimeError("Base Job-2 input deck missing: %s" % JOB2_INP)

    with open(JOB2_INP, "r") as f:
        job2_lines = f.readlines()

    # Find where Step 1 starts
    step_start_idx = -1
    for idx, line in enumerate(job2_lines):
        if "STEP 1: Fixed-Load Re-Equilibration" in line or line.strip().upper().startswith("*STEP"):
            step_start_idx = idx
            # If it's a comment line before *STEP, find the first comment of that block
            while step_start_idx > 0 and job2_lines[step_start_idx - 1].strip().startswith("**"):
                step_start_idx -= 1
            break

    if step_start_idx == -1:
        raise RuntimeError("Could not find *STEP in Job-2 deck")

    # Header and model definition up to Step 1
    pre_step_lines = job2_lines[:step_start_idx]

    # Update Heading in pre_step_lines
    out_lines = []
    in_heading = False
    for line in pre_step_lines:
        if line.strip().upper().startswith("*HEADING"):
            in_heading = True
            out_lines.append("*HEADING\n")
            out_lines.append("PK_METHOD_C_DEMO_PROPAGATION_JOB3 - Method C Step-2 Forward Crack Propagation\n")
            out_lines.append("** Demonstration Case: 1.0x1.0 mm plate with 0.5 mm crack and hole at (0.75, 0.5) mm\n")
            out_lines.append("** Discretization: Refined mesh (10,299 physical / 30,897 layered elements)\n")
            out_lines.append("** Step 1: Re-equilibration at u2 = 0.0050 mm\n")
            out_lines.append("** Step 2: Forward crack propagation from u2 = 0.0050 mm to u2 = 0.0100 mm\n")
            out_lines.append("** Initial Conditions: *INITIAL CONDITIONS, TYPE=SOLUTION (transferred H0)\n")
            out_lines.append("** Subroutine: Frozen UEL CE8D5EDC... (f42_mixed_uel.for)\n")
        elif in_heading:
            if line.strip().startswith("*"):
                in_heading = False
                out_lines.append(line)
            else:
                # skip old heading lines
                continue
        else:
            out_lines.append(line)

    # Append Two-Step Definition: Step 1 (Re-Equilibrate) and Step 2 (Propagate)
    steps_text = """** ----------------------------------------------------------
** STEP 1: Fixed-Load Re-Equilibration at u2 = 0.0050 mm
** ----------------------------------------------------------
*STEP, NAME=Step-1-ReEquilibrate, NLGEOM=NO, INC=1000
*STATIC
0.01, 1.0, 1.0E-07, 0.05
*BOUNDARY
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_RP, 1, 1, 0.0
N_RP, 2, 2, 0.0050
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
RF
*NODE OUTPUT
U
*ELEMENT OUTPUT, ELSET=umatelem
S, MISESERI, MISESAVG, EVOL, SDV
*NODE PRINT, FREQ=1, NSET=N_RP
U2, RF2
*END STEP
** ----------------------------------------------------------
** STEP 2: Forward Crack Propagation to u2 = 0.0100 mm
** Advancing load from u2 = 0.0050 mm to 0.0100 mm across 4-6 increments
** Initial dt = 0.10, Max dt = 0.20, Min dt = 1.0E-08
** ----------------------------------------------------------
*STEP, NAME=Step-2-Propagate, NLGEOM=NO, INC=5000
*STATIC
0.10, 1.0, 1.0E-08, 0.20
*BOUNDARY, OP=MOD
N_RP, 2, 2, 0.0100
*OUTPUT, FIELD, FREQUENCY=1
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
RF
*NODE OUTPUT
U
*ELEMENT OUTPUT, ELSET=umatelem
S, MISESERI, MISESAVG, EVOL, SDV
*NODE PRINT, FREQ=1, NSET=N_RP
U2, RF2
*END STEP
"""
    out_lines.append(steps_text)

    with open(JOB3_INP, "w") as f:
        f.writelines(out_lines)

    # Compute SHA-256
    h = hashlib.sha256()
    with open(JOB3_INP, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    deck_sha = h.hexdigest().upper()

    file_size = os.path.getsize(JOB3_INP)
    print("Generated Job-3 Deck: %s" % JOB3_INP)
    print("File size: %d bytes" % file_size)
    print("SHA-256: %s" % deck_sha)

    return JOB3_INP, deck_sha, file_size


if __name__ == "__main__":
    build_job3_deck()
