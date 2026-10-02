#!/usr/bin/env python3
"""
F132DIAG Detailed Structural Comparison of H2 vs PK10R1 INP decks
Task ID: F132DIAG-M2-CORRECTED-H2-VS-PK10R1-MODEL-EQUIVALENCE-AND-MESH-CONVERGENCE1
"""

import sys
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

H2_INP = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.inp"
PK10_INP = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"

def main():
    h2_text = H2_INP.read_text(encoding="utf-8", errors="ignore")
    pk10_text = PK10_INP.read_text(encoding="utf-8", errors="ignore")

    print("================================================================================")
    print("F132DIAG STRUCTURAL MODEL EQUIVALENCE AUDIT")
    print("================================================================================")

    # 1. Boundary conditions
    print("\n--- H2 BOUNDARY CONDITIONS ---")
    for line in h2_text.splitlines():
        if "*Boundary" in line or (line.strip() and not line.startswith("*") and ("top" in line or "bottom" in line or "RP" in line or "N_" in line)):
            print("  ", line)

    print("\n--- PK10R1 BOUNDARY CONDITIONS ---")
    for line in pk10_text.splitlines():
        if "*Boundary" in line or (line.strip() and not line.startswith("*") and ("top" in line or "bottom" in line or "RP" in line or "N_" in line)):
            print("  ", line)

    # 2. Step definitions
    print("\n--- H2 STEP DEFINITION ---")
    in_step = False
    for line in h2_text.splitlines():
        if "*Step" in line: in_step = True
        if in_step:
            print("  ", line)
            if "*End Step" in line: in_step = False

    print("\n--- PK10R1 STEP DEFINITION ---")
    in_step = False
    for line in pk10_text.splitlines():
        if "*Step" in line: in_step = True
        if in_step:
            print("  ", line)
            if "*End Step" in line: in_step = False

if __name__ == "__main__":
    main()
