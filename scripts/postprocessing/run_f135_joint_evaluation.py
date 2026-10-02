#!/usr/bin/env python3
"""
F135EVAL Joint Scientific Evaluation & Early Exit Diagnostics Script
Jobs:
- M2CORR_H1_FREEU2_FULL_U050 (1389686.mmaster02)
- M2CORR_H2_FREEU2_FULL_U050 (1389687.mmaster02)
- M2CORR_PK10R1_CONTINUOUS_U050 (1389684.mmaster02)
Task ID: F135EVAL-M2-CORRECTED-UNIFORM-BASELINES-JOINT-EVALUATION1
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
import os
import json
from odbAccess import openOdb

h1_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
h2_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb"
pk10_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

h1_sta = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.sta"
h2_sta = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.sta"
pk10_sta = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.sta"

def read_sta_file(sta_path):
    if not os.path.exists(sta_path):
        return "FILE NOT FOUND"
    lines = []
    with open(sta_path, "r") as f:
        for line in f:
            lines.append(line.strip())
    return lines[-10:] if lines else ["EMPTY"]

def extract_job_metrics(odb_path, total_disp=0.050):
    if not os.path.exists(odb_path):
        return None
        
    odb = openOdb(path=odb_path)
    trajectory = []
    
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
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if len(val.data) >= 3 and val.data[2] is not None:
                        v = float(val.data[2])
                        if v > d_max: d_max = v
                        
            trajectory.append((u1, rf1_val, d_max, t))
            
    odb.close()
    
    u1_vals = [p[0] for p in trajectory]
    rf1_vals = [p[1] for p in trajectory]
    
    max_rf = max(rf1_vals)
    idx_max = rf1_vals.index(max_rf)
    
    return {
        "num_frames": len(trajectory),
        "max_rf1": max_rf,
        "u1_at_max_rf1": u1_vals[idx_max],
        "terminal_u1": u1_vals[-1],
        "terminal_rf1": rf1_vals[-1],
        "terminal_d_max": trajectory[-1][2],
        "terminal_step_time": trajectory[-1][3],
        "first_5": trajectory[:5],
        "last_5": trajectory[-5:]
    }

out = {
    "h1_metrics": extract_job_metrics(h1_odb),
    "h1_sta_tail": read_sta_file(h1_sta),
    
    "h2_metrics": extract_job_metrics(h2_odb),
    "h2_sta_tail": read_sta_file(h2_sta),
    
    "pk10_metrics": extract_job_metrics(pk10_odb),
    "pk10_sta_tail": read_sta_file(pk10_sta)
}
print("JSON_START" + json.dumps(out) + "JSON_END")
"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f135_eval_abq.py"
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
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
