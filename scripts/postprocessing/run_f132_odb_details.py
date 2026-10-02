#!/usr/bin/env python3
"""
F132DIAG ODB Extraction & Analysis Script
Task ID: F132DIAG-M2-CORRECTED-H2-VS-PK10R1-MODEL-EQUIVALENCE-AND-MESH-CONVERGENCE1
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """import sys
import json
from odbAccess import openOdb

h2_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.odb"
pk10_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

def get_job_info(odb_path, total_disp=0.050):
    odb = openOdb(path=odb_path)
    frames = []
    
    for step_name, step in odb.steps.items():
        for frame in step.frames:
            t = frame.frameValue
            u1 = total_disp * t
            
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
            
            d_max = 0.0
            # Inspect U3 or SDV for d_max
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if len(val.data) >= 3 and val.data[2] is not None:
                        v = float(val.data[2])
                        if v > d_max: d_max = v
                        
            frames.append((u1, rf1_val, d_max))
            
    odb.close()
    return frames

h2_frames = get_job_info(h2_path)
pk10_frames = get_job_info(pk10_path)

res = {
    "h2_frames": h2_frames,
    "pk10_frames": pk10_frames
}
print("JSON_START" + json.dumps(res) + "JSON_END")
"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f132_odb_details.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        "export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; /cluster/application/abaqus/2023/Commands/abaqus python " + remote_script_path
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
    stdout = res.stdout
    json_start = stdout.find("JSON_START")
    json_end = stdout.find("JSON_END")
    if json_start != -1 and json_end != -1:
        data = json.loads(stdout[json_start+10:json_end])
        h2 = data["h2_frames"]
        pk10 = data["pk10_frames"]
        
        print("H2 frames count:", len(h2))
        print("First 5 H2:", h2[:5])
        print("Peak H2:", max(h2, key=lambda x: x[1]))
        print("Last 5 H2:", h2[-5:])
        
        print("\nPK10 frames count:", len(pk10))
        print("First 5 PK10:", pk10[:5])
        print("Peak PK10:", max(pk10, key=lambda x: x[1]))
        print("Last 5 PK10:", pk10[-5:])

if __name__ == "__main__":
    main()
