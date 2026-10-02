#!/usr/bin/env python3
"""
F138DIAG Comprehensive Transactional History & Handoff State Audit Script
Task ID: F138DIAG-M2-PK10R1-TRANSACTIONAL-HISTORY-SERIALIZATION-AND-HANDOFF-STATE-AUDIT1
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

pk10_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"
pk10_dat = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.dat"

def audit_f138():
    if not os.path.exists(pk10_odb):
        return {"error": "ODB not found"}
        
    odb = openOdb(path=pk10_odb)
    
    # Inspect step 1 frame 29
    step_name = list(odb.steps.keys())[0]
    step = odb.steps[step_name]
    
    frame_29 = step.frames[29]
    
    sdv_keys = list(frame_29.fieldOutputs.keys())
    
    sdv16_max = 0.0
    sdv13_max = 0.0
    sdv4_max = 0.0
    
    if 'SDV16' in frame_29.fieldOutputs:
        f = frame_29.fieldOutputs['SDV16']
        for val in f.values:
            if val.data is not None and float(val.data) > sdv16_max:
                sdv16_max = float(val.data)
                
    if 'SDV13' in frame_29.fieldOutputs:
        f = frame_29.fieldOutputs['SDV13']
        for val in f.values:
            if val.data is not None and float(val.data) > sdv13_max:
                sdv13_max = float(val.data)

    if 'SDV4' in frame_29.fieldOutputs:
        f = frame_29.fieldOutputs['SDV4']
        for val in f.values:
            if val.data is not None and float(val.data) > sdv4_max:
                sdv4_max = float(val.data)
                
    # Extract trajectory of SDV16, SDV13 across frames 20 to 35
    traj = []
    for idx in range(20, 35):
        fr = step.frames[idx]
        t = fr.frameValue
        u1 = 0.050 * t
        s16 = 0.0
        s13 = 0.0
        if 'SDV16' in fr.fieldOutputs:
            for val in fr.fieldOutputs['SDV16'].values:
                if val.data is not None and float(val.data) > s16: s16 = float(val.data)
        if 'SDV13' in fr.fieldOutputs:
            for val in fr.fieldOutputs['SDV13'].values:
                if val.data is not None and float(val.data) > s13: s13 = float(val.data)
        traj.append((idx, t, u1, s16, s13))

    odb.close()
    
    return {
        "sdv_keys": sdv_keys,
        "inc29_sdv16_max": sdv16_max,
        "inc29_sdv13_max": sdv13_max,
        "inc29_sdv4_max": sdv4_max,
        "traj_20_35": traj
    }

print "JSON_START" + json.dumps(audit_f138()) + "JSON_END"
"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f138_audit_abq.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, "cat << 'EOF' > " + remote_script_path + "\n" + REMOTE_SCRIPT + "\nEOF"]
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
        print("================================================================================")
        print("F138DIAG TRANSACTIONAL STATE AUDIT RESULTS")
        print("================================================================================")
        print(json.dumps(data, indent=2))

if __name__ == "__main__":
    main()
