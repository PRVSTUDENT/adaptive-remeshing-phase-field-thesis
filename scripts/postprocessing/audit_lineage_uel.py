#!/usr/bin/env python3
"""
Audit Mechanical Residual Defect Lineage across H0, H1, H2, MM, PK5, R1R11, R2R13, R2R14
"""

import sys
import os
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def check_fortran_file(fp):
    if not fp.exists():
        return None, None, "FILE_NOT_FOUND"
    
    content = fp.read_text(encoding="utf-8", errors="ignore")
    sha256 = hashlib.sha256(fp.read_bytes()).hexdigest()
    
    lines = content.splitlines()
    
    # Check JTYPE 2 (mechanical quad)
    # Check if RHS = RHS - AMATRX*U or RHS = -F_INT is inside or outside DO KPT=1,4
    inside_kpt = False
    rhs_inside = False
    rhs_outside = False
    has_f_int = False
    
    for i, l in enumerate(lines):
        l_strip = l.strip().upper()
        if "DO KPT = 1" in l_strip or "DO 100 KPT = 1" in l_strip or "DO 200 KPT = 1" in l_strip:
            inside_kpt = True
        elif "END DO" in l_strip or "100 CONTINUE" in l_strip or "200 CONTINUE" in l_strip:
            inside_kpt = False
            
        if "RHS" in l_strip and ("AMATRX" in l_strip or "F_INT" in l_strip):
            if "F_INT" in l_strip:
                has_f_int = True
            if inside_kpt:
                rhs_inside = True
            else:
                rhs_outside = True

    if has_f_int and rhs_outside and not rhs_inside:
        formulation = "CORRECTED_OUTSIDE_GP"
    elif rhs_inside:
        formulation = "DEFECTIVE_INSIDE_GP"
    elif rhs_outside:
        formulation = "CORRECTED_OUTSIDE_GP"
    else:
        formulation = "UNRESOLVED"
        
    return sha256, fp, formulation

def audit_all_jobs():
    print("=== AUDIT 5: MECHANICAL RESIDUAL DEFECT LINEAGE AUDIT ===")
    
    # Candidate paths for each job
    job_paths = {
        "H0_1386372": [
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H0_VERIFY/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_verification/evidence/1386372.mmaster02/f42_mixed_uel.for",
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H0_VERIFY/f42_uel.for"
        ],
        "H1_1386447": [
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H1_VERIFY/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_verification/evidence/1386447.mmaster02/f42_mixed_uel.for",
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H1_VERIFY/f42_uel.for"
        ],
        "H2_1386448": [
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H2_VERIFY/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_verification/evidence/1386448.mmaster02/f42_mixed_uel.for",
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_H2_VERIFY/f42_uel.for"
        ],
        "MM_1386469": [
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_MM_PRE_ANALYSIS/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_verification/evidence/1386469.mmaster02/f42_mixed_uel.for",
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_MM_PRE_ANALYSIS/f42_uel.for"
        ],
        "PK5_1386470": [
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_PK5_PRE_ANALYSIS/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_verification/evidence/1386470.mmaster02/f42_mixed_uel.for",
            ROOT / "models/generated/mode_ii/production_verification_batch/M2_PK5_PRE_ANALYSIS/f42_uel.for"
        ],
        "R1R11_1389278": [
            ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R11/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/f42_mixed_uel.for"
        ],
        "R2R13_1389325": [
            ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02/f42_mixed_uel.for"
        ],
        "R2R14_1389328": [
            ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14/f42_mixed_uel.for",
            ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02/f42_mixed_uel.for"
        ]
    }

    results = {}
    for job, paths in job_paths.items():
        found = False
        for p in paths:
            if p.exists():
                sha256, fp, form = check_fortran_file(p)
                results[job] = {
                    "path": str(p),
                    "sha256": sha256,
                    "formulation": form
                }
                found = True
                break
        if not found:
            results[job] = {
                "path": "NOT_FOUND",
                "sha256": "NONE",
                "formulation": "UNRESOLVED"
            }

    print(f"{'Job Name':<16} {'Formulation':<24} {'SHA256':<64}")
    print("-" * 110)
    for job, data in results.items():
        print(f"{job:<16} {data['formulation']:<24} {data['sha256']:<64}")

    return results

if __name__ == '__main__':
    audit_all_jobs()
