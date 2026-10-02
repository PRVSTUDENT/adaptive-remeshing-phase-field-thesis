#!/usr/bin/env python3
"""
F136DIAG Corrected Uniform Reference Acceptance, Phase-Bound, Topology Error, & Restart Selection Audit
Task ID: F136DIAG-M2-CORRECTED-REFERENCE-ACCEPTANCE-AND-RESTART-STATE-SELECTION1
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
import math
from odbAccess import openOdb

h1_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
h2_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb"
pk10_odb = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

def extract_full_chronology(odb_path, total_disp=0.050):
    if not os.path.exists(odb_path):
        return None
        
    odb = openOdb(path=odb_path)
    frames = []
    
    for step_name, step in odb.steps.items():
        for inc_idx, frame in enumerate(step.frames):
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
            h_max = 0.0
            count_d_gt_1 = 0
            total_d_nodes = 0
            max_overshoot = 0.0
            first_u1_d_gt_1 = None
            
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if len(val.data) >= 3 and val.data[2] is not None:
                        d = float(val.data[2])
                        total_d_nodes += 1
                        if d > d_max: d_max = d
                        if d > 1.0:
                            count_d_gt_1 += 1
                            ov = d - 1.0
                            if ov > max_overshoot: max_overshoot = ov
                            
            if 'SDV_HMAX' in frame.fieldOutputs:
                h_field = frame.fieldOutputs['SDV_HMAX']
                for val in h_field.values:
                    if val.data is not None:
                        v = float(val.data)
                        if v > h_max: h_max = v
            elif 'SDV1' in frame.fieldOutputs:
                h_field = frame.fieldOutputs['SDV1']
                for val in h_field.values:
                    if val.data is not None:
                        v = float(val.data)
                        if v > h_max: h_max = v
                        
            frames.append({
                "inc": inc_idx,
                "step_time": t,
                "u1": u1,
                "rf1": rf1_val,
                "dmax": d_max,
                "hmax": h_max,
                "count_d_gt_1": count_d_gt_1,
                "total_d_nodes": total_d_nodes,
                "max_overshoot": max_overshoot
            })
            
    odb.close()
    return frames

out = {
    "h1": extract_full_chronology(h1_odb),
    "h2": extract_full_chronology(h2_odb),
    "pk10": extract_full_chronology(pk10_odb)
}

print "JSON_START" + json.dumps(out) + "JSON_END"
sys.stdout.flush()

"""

def main():
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f136_audit_abq.py"
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
        (ROOT / "scripts/postprocessing/f136_data.json").write_text(json.dumps(data, indent=2))
        print("Data successfully saved to scripts/postprocessing/f136_data.json")

if __name__ == "__main__":
    main()
