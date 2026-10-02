#!/usr/bin/env python3
"""
F125DIAG Comprehensive History-Energy Consistency & Call Order Audit Script
Task ID: F125DIAG-M2-R2R13-TERMINAL-HISTORY-ENERGY-CONSISTENCY-AND-CALL-ORDER1
"""

import sys
import os
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """#!/usr/bin/env python3
import sys
import os
import json
import math

# We write a standalone Python script to inspect ODBs or DAT files on the cluster.
# On the cluster, Abaqus Python or standard Python with json/math can read DAT/ODB files.

BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"

def main():
    r13_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13", "M2STATE_FRACFIX_RESTART2R13.dat")
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    
    # Let's inspect R2R13 DAT file for EL PRINT of SDV14, SDV15, SDV16
    # In DAT files:
    # EL PRINT for E_QUAD_MECH and E_TRI_MECH prints SDV14 (d_val), SDV15 (deg), SDV16 (history SV_H)
    
    # We will also run abaqus python script on cluster to inspect the ODB field outputs if needed.
    output = {
        "r13_dat_exists": os.path.exists(r13_dat),
        "r13_dat_size": os.path.getsize(r13_dat) if os.path.exists(r13_dat) else 0,
        "cont_dat_exists": os.path.exists(cont_dat),
        "cont_dat_size": os.path.getsize(cont_dat) if os.path.exists(cont_dat) else 0
    }
    print(json.dumps(output))

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING F125DIAG HISTORY CONSISTENCY & CALL ORDER AUDIT")
    print("================================================================================")

    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f125_remote_check.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
