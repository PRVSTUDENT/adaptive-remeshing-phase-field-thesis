#!/usr/bin/env python3
"""
Inspect ODB Field Output Keys for Abaqus 2023
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

PY_SCRIPT = """from odbAccess import openOdb
import os
import json

odb_paths = [
    "../production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.odb",
    "PK10R1_IDENTITY_RESTART_U050/PK10R1_IDENTITY_RESTART_U050.odb",
    "PK10R1_CONTINUOUS_U050/PK10R1_CONTINUOUS_U050.odb"
]

out = {}
for p in odb_paths:
    if os.path.exists(p):
        odb = openOdb(p)
        steps = list(odb.steps.keys())
        info = {}
        for sname in steps:
            st = odb.steps[sname]
            info[sname] = {
                "n_frames": len(st.frames),
                "field_keys": list(st.frames[-1].fieldOutputs.keys())
            }
        out[p] = info
        odb.close()

print(json.dumps(out, indent=2))
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/inspect_odb_keys.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{PY_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"export PATH=/cluster/application/abaqus/2023/Commands:$PATH && cd projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch && abaqus python inspect_odb_keys.py"
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()
