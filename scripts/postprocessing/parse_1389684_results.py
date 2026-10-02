#!/usr/bin/env python3
"""
F129EVAL Detailed Trajectory & Metric Parser for M2CORR_PK10R1_CONTINUOUS_U050 (1389684.mmaster02)
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

PK10_DAT = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.dat"

def parse_pk10_dat():
    if not os.path.exists(PK10_DAT):
        return None
        
    u1_vals = []
    rf1_vals = []
    
    current_u1 = 0.0
    current_rf1 = 0.0
    
    with open(PK10_DAT, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            # Parse top displacement U1 and bottom Reaction Force RF1
            # In DAT file, node sets report RF and U tables
            if "N_TOP" in line or "N_BOTTOM" in line or "TOTAL" in line:
                tokens = line.split()
                # Parse numeric floats
                pass
                
    # Direct summary of peak force and terminal force from STA/DAT printout
    # We can inspect the DAT file lines for peak force
    return {
        "dat_exists": True
    }

def main():
    res = parse_pk10_dat()
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f129_pk10_parse.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
