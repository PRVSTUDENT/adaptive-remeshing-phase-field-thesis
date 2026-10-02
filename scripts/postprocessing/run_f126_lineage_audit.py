#!/usr/bin/env python3
"""
F126FIX Historical UEL Lineage Audit Script
Task ID: F126FIX-M2-UEL-UNDEGRADED-DRIVING-ENERGY-AND-ROLLBACK-SAFE-STATE-QUAL1
"""

import sys
import os
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

JOBS = [
    ("H0_1386372", "runs/hpc/stage_f/mode_ii_h0/evidence/1386372.mmaster02/f42_mixed_uel.for"),
    ("H1_1386447", "runs/hpc/stage_f/mode_ii_h1/evidence/1386447.mmaster02/f42_mixed_uel.for"),
    ("H2_1386448", "runs/hpc/stage_f/mode_ii_h2/evidence/1386448.mmaster02/f42_mixed_uel.for"),
    ("MM_1386469", "runs/hpc/stage_f/mode_ii_miseseri/evidence/1386469.mmaster02/f42_mixed_uel.for"),
    ("PK5_1386470", "runs/hpc/stage_f/mode_ii_pk5/evidence/1386470.mmaster02/f42_mixed_uel.for"),
    ("R1R11_1389278", "runs/hpc/mode_ii_state_transfer/evidence/1389278.mmaster02/f42_mixed_uel.for"),
    ("R2R13_1389325", "runs/hpc/mode_ii_state_transfer/evidence/1389325.mmaster02/f42_mixed_uel.for"),
    ("R2R14_1389328", "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02/f42_mixed_uel.for"),
    ("H1_full_1389351", "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/f42_mixed_uel.for"),
    ("H2_full_1389352", "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/f42_mixed_uel.for"),
    ("PK10R1_cont_1389677", "models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050/f42_mixed_uel.for"),
    ("PK10R1_ident_1389678", "models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050/f42_mixed_uel.for"),
    ("PK10R1_corr_1389680", "models/generated/mode_ii/production_control_batch/PK10R1_CORRECTED_IDENTITY_RESTART_U050/f42_mixed_uel.for")
]

def analyze_uel_file(fp):
    if not fp.exists():
        return {"exists": False}
        
    content = fp.read_text(encoding="utf-8", errors="ignore")
    sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
    
    # Check POS_M formulation:
    # Does C12 or C33 include DEG before POS_M calculation?
    lines = content.splitlines()
    has_deg_before_pos_m = False
    c12_has_deg = False
    pos_m_line = ""
    
    for i, line in enumerate(lines):
        if "C12 =" in line or "C12=" in line:
            if "DEG" in line:
                c12_has_deg = True
        if "POS_M =" in line or "POS_M=" in line:
            pos_m_line = line
            # Check if C12 was defined with DEG above this line
            if c12_has_deg:
                has_deg_before_pos_m = True
                
    pos_m_class = "DEGRADED_G_TIMES_PSI_PLUS_BUG" if has_deg_before_pos_m else "UNDEGRADED_PSI_PLUS_CORRECT"
    
    # History storage
    has_common_cb = "COMMON /CB_STATE_TRANSFER/" in content or "COMMON/CB_STATE_TRANSFER/" in content
    hist_class = "MODULE_ARRAY_UNMANAGED" if has_common_cb else "ABAKUS_SVARS_MANAGED"
    
    return {
        "exists": True,
        "sha256": sha256,
        "pos_m_class": pos_m_class,
        "hist_class": hist_class
    }

def main():
    print("================================================================================")
    print("F126FIX HISTORICAL UEL LINEAGE AUDIT")
    print("================================================================================")
    
    results = {}
    for job_name, rel_path in JOBS:
        local_fp = ROOT / rel_path
        res = analyze_uel_file(local_fp)
        results[job_name] = res
        print(f"{job_name:<25}: SHA={res.get('sha256', 'MISSING')[:12]} | POS_M={res.get('pos_m_class', 'N/A')}")
        
    (ROOT / "runs/hpc/mode_ii_control_batch/evidence/F126_LINEAGE_AUDIT.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
