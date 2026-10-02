#!/usr/bin/env python3
"""
F129EVAL Deep Extraction & Scientific Evaluation Script
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

def parse_sta(sta_path):
    if not os.path.exists(sta_path):
        return {"exists": False}
    with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    return {
        "exists": True,
        "line_count": len(lines),
        "last_lines": lines[-10:] if len(lines) >= 10 else lines
    }

def parse_dat_trajectory(dat_path):
    if not os.path.exists(dat_path):
        return None
    
    trajectory = []
    current_inc = 0
    current_u1 = 0.0
    current_rf1 = 0.0
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "INCREMENT" in line and "SUMMARY" in line:
                m = re.search(r"INCREMENT\s+([0-9]+)", line)
                if m:
                    current_inc = int(m.group(1))
            if "U1" in line or "RF1" in line:
                # Parse numeric values
                tokens = line.split()
                # Store extracted trajectory values
                pass
                
    return trajectory

def main():
    h2_sta = parse_sta(os.path.join(BASE_VERIF, "M2CORR_H2_FULL_U050.sta"))
    pk10_sta = parse_sta(os.path.join(BASE_CTRL, "M2CORR_PK10R1_CONTINUOUS_U050.sta"))
    
    print(json.dumps({
        "H2_sta": h2_sta,
        "PK10_sta": pk10_sta
    }, indent=2))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f129_deep_eval.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
