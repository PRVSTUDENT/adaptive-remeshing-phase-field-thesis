import os
import subprocess
import sys

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, sys, json
from odbAccess import openOdb

odb_path = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/M2STATE_FRACFIX_RESTART1R1R6R2.odb'
if not os.path.exists(odb_path):
    print("ODB NOT FOUND:", odb_path)
    sys.exit(1)

odb = openOdb(odb_path, readOnly=True)
print("ODB Opened:", odb.name)

frames_info = []
for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    print("Step:", step_name, "Frames:", len(step.frames))
    for idx, frame in enumerate(step.frames):
        st_time = frame.frameValue
        if step_name == "Step-2-Continuation":
            u1_total = 0.005000 + st_time
        else:
            u1_total = 0.0
            
        u_max = 0.0
        rf1_total = 0.0
        d_min = 1e9
        d_max = -1e9
        
        if "U" in frame.fieldOutputs:
            u_field = frame.fieldOutputs["U"]
            for v in u_field.values:
                if v.nodeLabel == 99999:
                    u1_ref = v.data[0]
                else:
                    if len(v.data) >= 3:
                        d_val = v.data[2]
                        if d_val < d_min: d_min = d_val
                        if d_val > d_max: d_max = d_val
        if "RF" in frame.fieldOutputs:
            rf_field = frame.fieldOutputs["RF"]
            for v in rf_field.values:
                if v.nodeLabel == 99999:
                    rf1_total = v.data[0]
                    
        frames_info.append({
            "step": step_name,
            "frame": idx,
            "step_time": st_time,
            "total_U1": u1_total,
            "RF1": rf1_total,
            "phase_min": d_min if d_min < 1e8 else 0.0,
            "phase_max": d_max if d_max > -1e8 else 0.0
        })

print("SUMMARY_JSON_START")
print(json.dumps(frames_info, indent=2))
print("SUMMARY_JSON_END")
"""
    cmd = [
        "ssh", "-i", key,
        "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no",
        "pr21vyci@mlogin01.hrz.tu-freiberg.de",
        f"source /etc/profile 2>/dev/null; module load abaqus/2023 python/gcc/11.4.0/3.11.7 2>/dev/null; abaqus python -c {subprocess.list2cmdline([remote_script])}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("STDOUT:\n", res.stdout)
    print("STDERR:\n", res.stderr)
    print("RC =", res.returncode)

if __name__ == "__main__":
    main()
