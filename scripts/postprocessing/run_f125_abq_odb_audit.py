#!/usr/bin/env python3
"""
Cluster Abaqus ODB History-Energy Auditor for R2R13 and PK10R1 Continuous
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

CLUSTER_PY = """# Abaqus Python script executed inside abaqus python environment
import sys
import os
import json
import math
from odbAccess import openOdb

def analyze_odb_history(odb_path):
    if not os.path.exists(odb_path):
        return None
    odb = openOdb(odb_path, readOnly=True)
    step_name = odb.steps.keys()[-1]
    step = odb.steps[step_name]
    last_frame = step.frames[-1]
    
    # Extract displacements
    u_field = last_frame.fieldOutputs['U']
    u_dict = {}
    for v in u_field.values:
        u_dict[v.nodeLabel] = (v.data[0], v.data[1], v.data[2] if len(v.data)>2 else 0.0)
        
    # Extract SDV16 (history H) if present
    sdv16_dict = {}
    if 'SDV16' in last_frame.fieldOutputs:
        sdv16_field = last_frame.fieldOutputs['SDV16']
        for v in sdv16_field.values:
            sdv16_dict[(v.elementLabel, v.integrationPoint)] = v.data
            
    # Extract SDV14 (d) if present
    sdv14_dict = {}
    if 'SDV14' in last_frame.fieldOutputs:
        sdv14_field = last_frame.fieldOutputs['SDV14']
        for v in sdv14_field.values:
            sdv14_dict[(v.elementLabel, v.integrationPoint)] = v.data

    odb.close()
    return {
        "num_nodes": len(u_dict),
        "num_sdv16_ips": len(sdv16_dict),
        "num_sdv14_ips": len(sdv14_dict)
    }

def main():
    r13_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.odb"
    cont_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050/PK10R1_CONTINUOUS_U050.odb"
    
    res_r13 = analyze_odb_history(r13_odb)
    res_cont = analyze_odb_history(cont_odb)
    
    out = {
        "r13": res_r13,
        "continuous": res_cont
    }
    print("RESULTS_JSON_START")
    print(json.dumps(out))
    print("RESULTS_JSON_END")

if __name__ == "__main__":
    main()
"""

def main():
    remote_py_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f125_abq_script.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_py_path}\n{CLUSTER_PY}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"source /etc/profile.d/lmod.sh 2>/dev/null || source /etc/profile.d/modules.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7; /cluster/application/abaqus/2023/Commands/abaqus python {remote_py_path}"
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=180)
    print("Stdout:", res.stdout)
    if res.stderr:
        print("Stderr:", res.stderr)

if __name__ == "__main__":
    main()
