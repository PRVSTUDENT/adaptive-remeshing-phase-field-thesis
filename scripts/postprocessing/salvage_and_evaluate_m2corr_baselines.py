#!/usr/bin/env python3
"""
F129EVAL Corrected Virgin Baselines Salvage & Scientific Evaluation Script
Task ID: F129EVAL-M2-CORRECTED-VIRGIN-BASELINES-EVALUATION1
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

REMOTE_SCRIPT = """#!/usr/bin/env python3
import os
import re
import json

BASE_VERIF = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050"
BASE_CTRL  = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050"

def parse_dat_file(dat_path):
    if not os.path.exists(dat_path):
        return None
    
    completed = False
    increments = 0
    u1_vals = []
    rf1_vals = []
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
        if "THE ANALYSIS HAS BEEN COMPLETED" in content:
            completed = True
            
        # Parse increment table / summary blocks
        # Looking for U1 and RF1 outputs
        for line in content.splitlines():
            if "INCREMENT" in line and "SUMMARY" in line:
                increments += 1
                
    # Also parse detailed trajectory from DAT or ODB if available
    return {
        "exists": True,
        "completed": completed,
        "content_length": len(content)
    }

def main():
    h2_dat = os.path.join(BASE_VERIF, "M2CORR_H2_FULL_U050.dat")
    h2_sta = os.path.join(BASE_VERIF, "M2CORR_H2_FULL_U050.sta")
    pk10_dat = os.path.join(BASE_CTRL, "M2CORR_PK10R1_CONTINUOUS_U050.dat")
    pk10_sta = os.path.join(BASE_CTRL, "M2CORR_PK10R1_CONTINUOUS_U050.sta")
    
    h2_res = parse_dat_file(h2_dat)
    pk10_res = parse_dat_file(pk10_dat)
    
    out = {
        "H2": h2_res,
        "PK10R1": pk10_res
    }
    print(json.dumps(out, indent=2))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("F129EVAL CORRECTED BASELINES EVIDENCE SALVAGE & SCIENTIFIC EVALUATION")
    print("================================================================================")

    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f129_eval.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
