#!/usr/bin/env python3
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

DAT_FILE = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.dat"

def extract_trajectory():
    if not os.path.exists(DAT_FILE):
        return None
        
    u1_list = []
    rf1_list = []
    
    current_u = None
    current_rf = None
    
    with open(DAT_FILE, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "TIME COMPLETED IN THIS STEP" in line:
                m = re.search(r"TIME COMPLETED IN THIS STEP\s+([0-9.E+-]+)", line)
                if m:
                    # In step 1 under displacement control U1 = total_step_disp * step_time (total disp = 0.050mm)
                    step_time = float(m.group(1))
                    current_u = 0.050 * step_time
            if "TOTAL" in line and ("N_BOTTOM" in line or "RF1" in line or "1" in line):
                tokens = line.split()
                # Parse reaction force sum
                for tok in tokens:
                    try:
                        v = float(tok)
                        if abs(v) > 1e-4 and abs(v) < 100.0:
                            current_rf = abs(v)
                    except ValueError:
                        pass
            if current_u is not None and current_rf is not None:
                u1_list.append(current_u)
                rf1_list.append(current_rf)
                current_u = None
                current_rf = None

    if rf1_list:
        max_rf = max(rf1_list)
        idx_max = rf1_list.index(max_rf)
        u_max = u1_list[idx_max] if idx_max < len(u1_list) else 0.0
        term_rf = rf1_list[-1]
    else:
        max_rf = 0.0
        u_max = 0.0
        term_rf = 0.0

    return {
        "count": len(rf1_list),
        "max_rf1": max_rf,
        "u1_at_max_rf1": u_max,
        "terminal_rf1": term_rf
    }

def main():
    print(json.dumps(extract_trajectory(), indent=2))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f129_extract_rf.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
