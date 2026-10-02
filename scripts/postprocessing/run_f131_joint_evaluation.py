#!/usr/bin/env python3
"""
F131EVAL Joint Scientific Evaluation Script for Corrected Baselines H2 (1389685) & PK10R1 (1389684)
Task ID: F131EVAL-M2-CORRECTED-VIRGIN-BASELINES-JOINT-EVALUATION1
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

h2_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.odb"
pk10_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

def extract_odb_metrics(odb_path, total_disp=0.050):
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
            trajectory.append((u1, rf1_val))
            
    odb.close()
    
    u1_vals = [p[0] for p in trajectory]
    rf1_vals = [p[1] for p in trajectory]
    
    max_rf = max(rf1_vals)
    idx_max = rf1_vals.index(max_rf)
    u1_max = u1_vals[idx_max]
    term_rf = rf1_vals[-1]
    
    return {
        "num_frames": len(trajectory),
        "max_rf1": max_rf,
        "u1_at_max_rf1": u1_max,
        "terminal_rf1": term_rf,
        "trajectory": trajectory
    }

h2_res = extract_odb_metrics(h2_odb_path)
pk10_res = extract_odb_metrics(pk10_odb_path)

peak_ratio = pk10_res["max_rf1"] / h2_res["max_rf1"] if h2_res["max_rf1"] > 0 else 0.0
rel_diff_peak = abs(pk10_res["max_rf1"] - h2_res["max_rf1"]) / h2_res["max_rf1"] if h2_res["max_rf1"] > 0 else 0.0

summary = {
    "H2_job_id": "1389685.mmaster02",
    "H2_physical_elements": 33852,
    "H2_max_rf1": h2_res["max_rf1"],
    "H2_u1_at_max_rf1": h2_res["u1_at_max_rf1"],
    "H2_terminal_rf1": h2_res["terminal_rf1"],
    "H2_num_frames": h2_res["num_frames"],
    
    "PK10R1_job_id": "1389684.mmaster02",
    "PK10R1_physical_elements": 9612,
    "PK10R1_max_rf1": pk10_res["max_rf1"],
    "PK10R1_u1_at_max_rf1": pk10_res["u1_at_max_rf1"],
    "PK10R1_terminal_rf1": pk10_res["terminal_rf1"],
    "PK10R1_num_frames": pk10_res["num_frames"],
    
    "peak_force_convergence_ratio": peak_ratio,
    "relative_difference_peak_force": rel_diff_peak
}

print("JSON_START" + json.dumps(summary) + "JSON_END")
"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f131_joint_eval.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        "export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; /cluster/application/abaqus/2023/Commands/abaqus python " + remote_script_path
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)

if __name__ == "__main__":
    main()
