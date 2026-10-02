#!/usr/bin/env python3
"""
Inspect Fortran UEL files for all 8 target jobs
"""

import sys
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

jobs = [
    ("H0 1386372", ROOT / "models/generated/mode_ii/verification_batch/M2REF_H0_NPHYSFIX_REPRO/f42_mixed_uel.for"),
    ("H1 1386447", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/f42_mixed_uel.for"),
    ("H2 1386448", ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/f42_mixed_uel.for"),
    ("MM 1386469", ROOT / "models/generated/mode_ii/production_adaptive_batch/M2ADAPT_MM_FRACFIX_PROD/f42_mixed_uel.for"),
    ("PK5 1386470", ROOT / "models/generated/mode_ii/production_adaptive_batch/M2ADAPT_PK5_FRACFIX_PROD/f42_mixed_uel.for"),
    ("R1R11 1389278", ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11/f42_mixed_uel.for"),
    ("R2R13 1389325", ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/f42_mixed_uel.for"),
    ("R2R14 1389328", ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/f42_mixed_uel.for"),
]

def analyze_fortran(fp):
    if not fp.exists():
        return "MISSING", "NONE", False, False
    
    raw = fp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    lines = fp.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    # Check JTYPE 2 (quad mechanical)
    # Check where RHS is updated
    # Look for DO KPT / END DO
    in_jtype2 = False
    in_kpt = False
    rhs_in_kpt = False
    rhs_out_kpt = False
    
    for i, l in enumerate(lines):
        l_upper = l.upper()
        if "IF (JTYPE .EQ. 2" in l_upper or "IF (JTYPE.EQ.2" in l_upper:
            in_jtype2 = True
        elif in_jtype2 and ("IF (JTYPE .EQ." in l_upper or "IF (JTYPE.EQ." in l_upper):
            in_jtype2 = False
            
        if in_jtype2:
            if "DO KPT = 1" in l_upper or "DO 100 KPT = 1" in l_upper or "DO 200 KPT = 1" in l_upper:
                in_kpt = True
            elif "END DO" in l_upper or "100 CONTINUE" in l_upper or "200 CONTINUE" in l_upper:
                in_kpt = False
                
            if "RHS(" in l_upper:
                if in_kpt:
                    rhs_in_kpt = True
                else:
                    rhs_out_kpt = True

    if rhs_in_kpt:
        form = "DEFECTIVE_INSIDE_GP"
    elif rhs_out_kpt:
        form = "CORRECTED_OUTSIDE_GP"
    else:
        form = "OTHER"
        
    return form, sha, fp

def main():
    print("=== AUDIT 5: MECHANICAL RESIDUAL DEFECT LINEAGE AUDIT ===")
    print(f"{'Job Name':<16} {'Formulation':<24} {'SHA256':<64}")
    print("-" * 110)
    for name, fp in jobs:
        form, sha, path = analyze_fortran(fp)
        print(f"{name:<16} {form:<24} {sha:<64}")

if __name__ == '__main__':
    main()
