#!/usr/bin/env python3
"""
F133DIAG Mode-II Boundary Condition & Loading Definition Reconciliation Audit
Task ID: F133DIAG-M2-INTENDED-BC-AND-CORRECTED-BASELINE-DEFINITION-RECONCILIATION1
"""

import sys
import os
import re
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS_TO_AUDIT = [
    ("1386372", "H0 historical", "models/generated/mode_ii/production_verification_batch/M2REF_H0_FULL_U050/M2REF_H0_FULL_U050.inp"),
    ("1386447", "H1 historical", "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/M2REF_H1_FULL_U050.inp"),
    ("1386448", "H2 historical", "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/M2REF_H2_FULL_U050.inp"),
    ("1386469", "MM historical", "models/generated/mode_ii/production_verification_batch/M2REF_MM_FULL_U050/M2REF_MM_FULL_U050.inp"),
    ("1386470", "PK5 historical", "models/generated/mode_ii/production_verification_batch/M2REF_PK5_FULL_U050/M2REF_PK5_FULL_U050.inp"),
    ("1389278", "R1R11", "models/generated/mode_ii/production_remesh_batch/M2STATE_FRACFIX_RESTART1R1R11/M2STATE_FRACFIX_RESTART1R1R11.inp"),
    ("1389325", "R2R13", "models/generated/mode_ii/production_remesh_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.inp"),
    ("1389328", "R2R14", "models/generated/mode_ii/production_remesh_batch/M2STATE_FRACFIX_RESTART2R14/M2STATE_FRACFIX_RESTART2R14.inp"),
    ("1389351", "H1 full", "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/M2REF_H1_FULL_U050.inp"),
    ("1389352", "H2 full", "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/M2REF_H2_FULL_U050.inp"),
    ("1389677", "PK10R1 continuous historical", "models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050/PK10R1_CONTINUOUS_U050.inp"),
    ("1389685", "corrected H2", "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.inp"),
    ("1389684", "corrected PK10R1", "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp")
]

def audit_inp_file(inp_path):
    if not inp_path.exists():
        return None
        
    content = inp_path.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    
    top_u1 = "UNRESOLVED"
    top_u2 = "UNRESOLVED"
    bottom_u1 = "UNRESOLVED"
    bottom_u2 = "UNRESOLVED"
    rp_eq = "NONE"
    phase_bc = "NONE"
    
    in_boundary = False
    in_equation = False
    
    eq_lines = []
    
    for i, line in enumerate(lines):
        ls = line.strip()
        if ls.startswith("**") or not ls:
            continue
            
        if ls.upper().startswith("*EQUATION"):
            in_equation = True
            in_boundary = False
            continue
        elif ls.upper().startswith("*BOUNDARY"):
            in_boundary = True
            in_equation = False
            continue
        elif ls.startswith("*"):
            in_boundary = False
            in_equation = False
            continue
            
        if in_equation:
            eq_lines.append(ls)
        elif in_boundary:
            # Parse boundary conditions
            tokens = [t.strip() for t in ls.split(",")]
            if len(tokens) >= 3:
                nset = tokens[0]
                dof_start = tokens[1]
                dof_end = tokens[2]
                val = tokens[3] if len(tokens) > 3 else "0"
                
                if "BOTTOM" in nset.upper() or "BOTTOM_NODES" in nset.upper():
                    if dof_start == "1" and (dof_end == "2" or dof_end == "1"):
                        bottom_u1 = f"FIXED ({val})"
                    if (dof_start == "2" or dof_start == "1") and dof_end == "2":
                        bottom_u2 = f"FIXED ({val})"
                elif "TOP" in nset.upper() or "TOP_NODES" in nset.upper():
                    if dof_start == "1": top_u1 = f"FIXED ({val})"
                    if dof_start == "2" or dof_end == "2": top_u2 = f"FIXED ({val})"
                elif "RP" in nset.upper() or nset == "99999":
                    if dof_start == "1": top_u1 = f"PRESCRIBED RP ({val})"
                    if dof_start == "2": top_u2 = f"PRESCRIBED RP ({val})"
                    
    # Parse equation line Tying
    if eq_lines:
        rp_eq = " ".join(eq_lines[:4])
        
    # Classify BC
    if top_u2 == "UNRESOLVED" or "FREE" in top_u2:
        bc_class = "MODE_II_TOP_U2_FREE"
        top_u2 = "FREE"
    elif "FIXED" in top_u2 or "0" in top_u2:
        bc_class = "MODE_II_TOP_U2_FIXED"
    else:
        bc_class = "OTHER"
        
    return {
        "top_u1": top_u1,
        "top_u2": top_u2,
        "bottom_u1": bottom_u1,
        "bottom_u2": bottom_u2,
        "rp_eq": rp_eq,
        "phase_bc": phase_bc,
        "bc_class": bc_class
    }

def main():
    print("================================================================================")
    print("F133DIAG MECHANICAL BC LINEAGE AUDIT")
    print("================================================================================")
    
    print(f"\n{'Job ID':<10} | {'Name':<28} | {'Top U1':<18} | {'Top U2':<10} | {'Bottom U1/U2':<15} | {'BC Class':<22}")
    print("-" * 115)
    
    for job_id, job_name, rel_inp in JOBS_TO_AUDIT:
        inp_path = ROOT / rel_inp
        info = audit_inp_file(inp_path)
        if info:
            bot_str = f"{info['bottom_u1']}/{info['bottom_u2']}"
            print(f"{job_id:<10} | {job_name:<28} | {info['top_u1']:<18} | {info['top_u2']:<10} | {bot_str:<15} | {info['bc_class']:<22}")
        else:
            print(f"{job_id:<10} | {job_name:<28} | FILE NOT FOUND: {rel_inp}")

if __name__ == "__main__":
    main()
