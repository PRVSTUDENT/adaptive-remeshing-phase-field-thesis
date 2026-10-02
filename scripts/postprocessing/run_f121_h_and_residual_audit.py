#!/usr/bin/env python3
"""
F121DIAG History Contamination and Phase Residual Remote Extractor
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """#!/usr/bin/env python3
import sys
import os
import re
import json
import math
import numpy as np

# We inspect the ODB files or DAT files on cluster to compute H advancement and phase residual.
# ODBs available on cluster:
# R13 ODB: projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.odb
# Identity PhaseInit ODB / Datacheck ODB: projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050/PK10R1_IDENTITY_RESTART_U050.odb

def main():
    r13_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"
    ident_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050"
    cont_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050"

    print("Checking ODB files...")
    r13_odb = os.path.join(r13_dir, "M2STATE_FRACFIX_RESTART2R13.odb")
    ident_odb = os.path.join(ident_dir, "PK10R1_IDENTITY_RESTART_U050.odb")
    cont_odb = os.path.join(cont_dir, "PK10R1_CONTINUOUS_U050.odb")

    for p in [r13_odb, ident_odb, cont_odb]:
        print(p, "exists:", os.path.exists(p), "size:", os.path.getsize(p) if os.path.exists(p) else 0)

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f121_h_res_audit.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    res = subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"], capture_output=True, text=True)
    print(res.stdout)

if __name__ == "__main__":
    main()
