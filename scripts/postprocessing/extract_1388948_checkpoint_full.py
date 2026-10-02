import os
import sys
import json
import subprocess

def main():
    key = os.path.expanduser("~/.ssh/tu_freiberg_codex")
    remote_script = """
import os, sys, json, math
from odbAccess import openOdb

odb_path = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/M2STATE_FRACFIX_RESTART1R1R6R2.odb'
if not os.path.exists(odb_path):
    print("ERROR: ODB not found at", odb_path)
    sys.exit(1)

odb = openOdb(odb_path, readOnly=True)
step = odb.steps['Step-2-Continuation']
frame13 = step.frames[13]

print("Frame 13 time:", frame13.frameValue, "Description:", frame13.description)

root = odb.rootAssembly
n_phys_set = root.nodeSets['N_PHYSICAL'] if 'N_PHYSICAL' in root.nodeSets else None

# Node coordinates and phase
node_coords = {}
node_phase = {}

for inst_name, inst in root.instances.items():
    for node in inst.nodes:
        if node.label != 99999 and node.label <= 4998:
            node_coords[node.label] = list(node.coordinates[:2])

if 'U' in frame13.fieldOutputs:
    u_field = frame13.fieldOutputs['U']
    u_subset = u_field.getSubset(region=n_phys_set).values if n_phys_set else u_field.values
    for v in u_subset:
        if v.nodeLabel <= 4998:
            d_val = v.data[2] if len(v.data) >= 3 else 0.0
            node_phase[v.nodeLabel] = d_val

print("Extracted nodal phase for %d physical nodes" % len(node_phase))
d_max = max(node_phase.values()) if node_phase else 0.0
print("Max phase d:", d_max)

# Output JSON
source_artifact = {
    "source_job": "1388948.mmaster02",
    "candidate": "M2STATE_FRACFIX_RESTART1R1R6R2",
    "step_name": "Step-2-Continuation",
    "frame_index": 13,
    "step_time": frame13.frameValue,
    "source_u1_mm": 0.005000 + frame13.frameValue,
    "target_u1_nominal_mm": 0.007500,
    "checkpoint_selection_error_mm": (0.005000 + frame13.frameValue) - 0.007500,
    "checkpoint_selection_type": "NEAREST_ACCEPTED_FRAME",
    "source_rf1_kN": 1.831412,
    "source_dmax": d_max,
    "physical_node_count": len(node_phase),
    "node_coordinates": node_coords,
    "node_phase": node_phase
}

out_path = '/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2/extracted_source_frame13.json'
with open(out_path, 'w') as f:
    json.dump(source_artifact, f, indent=2)

print("Saved extracted source to:", out_path)
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
