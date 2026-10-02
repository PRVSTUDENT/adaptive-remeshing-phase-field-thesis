#!/usr/bin/env python3
"""
F129EVAL Abaqus Python ODB Reaction Force & History Consistency Extractor
Task ID: F129EVAL-M2-CORRECTED-VIRGIN-BASELINES-EVALUATION1
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

ABAQUS_ODB_SCRIPT = """import sys
import json
from odbAccess import openOdb

odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

odb = openOdb(path=odb_path)

trajectory = []
for step_name, step in odb.steps.items():
    for frame in step.frames:
        t = frame.frameValue
        u1 = 0.050 * t
        
        # Reaction forces at N_BOTTOM or all nodes
        rf_field = frame.fieldOutputs['RF']
        rf1_pos = 0.0
        rf1_neg = 0.0
        for val in rf_field.values:
            if val.data[0] is not None:
                if val.data[0] > 0:
                    rf1_pos += val.data[0]
                else:
                    rf1_neg += abs(val.data[0])
                
        rf1_val = max(rf1_pos, rf1_neg)
        trajectory.append((u1, rf1_val))
    
odb.close()

u1_vals = [p[0] for p in trajectory]
rf1_vals = [p[1] for p in trajectory]

max_rf = max(rf1_vals)
idx_max = rf1_vals.index(max_rf)
u1_max = u1_vals[idx_max]
term_rf = rf1_vals[-1]

res = {
    "num_frames": len(trajectory),
    "max_rf1": max_rf,
    "u1_at_max_rf1": u1_max,
    "terminal_rf1": term_rf,
    "first_10": trajectory[:10],
    "last_10": trajectory[-10:]
}
print("JSON_START" + json.dumps(res) + "JSON_END")
"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/extract_odb_abq.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{ABAQUS_ODB_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        "export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; /cluster/application/abaqus/2023/Commands/abaqus python " + remote_script_path
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=180)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
