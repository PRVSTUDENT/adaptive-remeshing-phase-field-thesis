#!/usr/bin/env python3
"""
Abaqus Python ODB Extractor for F121DIAG:
Extracts SDV14 (phase d) and SDV16 (history H) from ODBs:
1. R2R13 Terminal Frame (Job 1389325.mmaster02)
2. Identity Restart PhaseInit Frame (Job 1389678.mmaster02 Step 1 Frame 1)
3. Continuous PK10R1 Frame at U1 = 0.030 mm (Job 1389677.mmaster02)
"""

import sys
import os
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

ABAQUS_PYTHON_SCRIPT = """# Py2.7 Abaqus script
from odbAccess import openOdb
import json
import math

r13_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13/M2STATE_FRACFIX_RESTART2R13.odb"
ident_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_IDENTITY_RESTART_U050/PK10R1_IDENTITY_RESTART_U050.odb"
cont_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/PK10R1_CONTINUOUS_U050/PK10R1_CONTINUOUS_U050.odb"

def extract_sdv_from_odb(odb_path, step_idx=-1, frame_idx=-1):
    odb = openOdb(odb_path)
    step_keys = list(odb.steps.keys())
    step = odb.steps[step_keys[step_idx]]
    frame = step.frames[frame_idx]
    
    # We want SDV14 (d) and SDV16 (H) if present
    # Or SDV13 / SDV18
    fo_keys = list(frame.fieldOutputs.keys())
    
    sdv_data = {}
    
    # Check SDV16 or SDV13 or SDV14
    target_fields = [f for f in fo_keys if "SDV" in f or "SDV16" in f or "SDV14" in f]
    
    for tf in target_fields:
        fo = frame.fieldOutputs[tf]
        vals = {}
        for v in fo.values:
            # key by elementLabel and integrationPoint
            elem = v.elementLabel
            ip = v.integrationPoint if v.integrationPoint is not None else 1
            vals["%d_%d" % (elem, ip)] = float(v.data)
        sdv_data[tf] = vals
        
    odb.close()
    return sdv_data

def main():
    res = {}
    print("Extracting R13...")
    try:
        res["r13_terminal"] = extract_sdv_from_odb(r13_odb_path, step_idx=-1, frame_idx=-1)
    except Exception as e:
        res["r13_err"] = str(e)
        
    print("Extracting Identity PhaseInit...")
    try:
        res["ident_phaseinit"] = extract_sdv_from_odb(ident_odb_path, step_idx=0, frame_idx=-1)
    except Exception as e:
        res["ident_err"] = str(e)

    print("Extracting Continuous U030...")
    try:
        res["cont_u030"] = extract_sdv_from_odb(cont_odb_path, step_idx=0, frame_idx=65) # approximate frame for 0.030mm
    except Exception as e:
        res["cont_err"] = str(e)

    with open("f121_sdv_extracted.json", "w") as f:
        json.dump(res, f)
    print("SAVED_SDV_JSON")

if __name__ == "__main__":
    main()
"""

def main():
    print("================================================================================")
    print("EXECUTING ABAQUS ODB FIELD EXTRACTION FOR F121DIAG")
    print("================================================================================")
    
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/abq_extract_f121.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{ABAQUS_PYTHON_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)
    
    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"export PATH=/cluster/application/abaqus/2023/Commands:$PATH && cd projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch && abaqus python abq_extract_f121.py"
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
    print("Abaqus python stdout:\n", res.stdout)
    print("Abaqus python stderr:\n", res.stderr)

if __name__ == "__main__":
    main()
