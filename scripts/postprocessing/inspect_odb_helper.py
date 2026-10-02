import os
import sys
import subprocess

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_host = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
    remote_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R1"

    py_script = """import os, sys, json
from odbAccess import openOdb

odb_path = 'M2STATE_FRACFIX_RESTART2R1.odb'
odb = openOdb(odb_path, readOnly=True)

print("ODB Steps: " + str(list(odb.steps.keys())))
for s_name, step in odb.steps.items():
    print("Step: " + str(s_name) + " Frames: " + str(len(step.frames)))
    for i, frame in enumerate(step.frames):
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            vals = u_field.values
            d_vals = []
            u1_vals = []
            u2_vals = []
            u3_vals = []
            for v in vals:
                if v.nodeLabel <= 10080:
                    data = v.data
                    if len(data) >= 1: u1_vals.append(data[0])
                    if len(data) >= 2: u2_vals.append(data[1])
                    if len(data) >= 3: u3_vals.append(data[2])
            print("  Frame {} (t={}): count={}, U1_max={:.6f}, U2_max={:.6f}, U3_max={:.6f}".format(
                i, frame.frameValue, len(vals),
                max(u1_vals) if u1_vals else 0.0,
                max(u2_vals) if u2_vals else 0.0,
                max(u3_vals) if u3_vals else 0.0
            ))

print("\\nREPRESENTATIVE NODES (100, 1500, 2292, 4862, 4994, 6394, 7186, 9756):")
rep_nodes = [100, 1500, 2292, 4862, 4994, 6394, 7186, 9756]
for s_name, step in odb.steps.items():
    last_frame = step.frames[-1]
    if 'U' in last_frame.fieldOutputs:
        u_field = last_frame.fieldOutputs['U']
        sub = u_field.getSubset(region=odb.rootAssembly.nodeSets['N_PHYSICAL']) if 'N_PHYSICAL' in odb.rootAssembly.nodeSets else u_field
        val_map = {v.nodeLabel: v.data for v in sub.values}
        print("Step " + str(s_name) + " Last Frame U values:")
        for nid in rep_nodes:
            if nid in val_map:
                print("  Node {:5d}: U = {}".format(nid, val_map[nid]))
"""

    remote_file = f"{remote_dir}/inspect_odb.py"
    cmd_write = [
        "ssh", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", remote_host,
        f"cat << 'EOF' > {remote_file}\n{py_script}\nEOF\n"
    ]
    subprocess.run(cmd_write, check=True)

    cmd_run = [
        "ssh", "-i", key, "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", remote_host,
        f"cd {remote_dir} && source /etc/profile 2>/dev/null; module load abaqus/2023 python/gcc/11.4.0/3.11.7 2>/dev/null; abaqus python inspect_odb.py"
    ]
    res = subprocess.run(cmd_run, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

if __name__ == '__main__':
    main()
