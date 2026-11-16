# -*- coding: utf-8 -*-
"""
probe_case2_damage_history.py
Scan Step-2 frames in PK_HOLE_COARSE_JOB1.odb to identify the exact post-breach causal state.
"""
from odbAccess import openOdb
import sys

odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
odb = openOdb(odb_path, readOnly=True)

s2 = odb.steps['Step-2']
print("Total Step-2 frames: %d" % len(s2.frames))

# Check frame stride
for i in range(0, len(s2.frames), 25):
    f = s2.frames[i]
    sdv1 = f.fieldOutputs['SDV1']
    vals = [v.data for v in sdv1.values]
    u = f.fieldOutputs['U']
    uy_vals = [v.data[1] for v in u.values]
    print("Frame %3d: time=%.4f, uy_max=%.6f, d_min=%.4f, d_max=%.4f, vals=%d" % (
        i, f.frameValue, max(uy_vals), min(vals), max(vals), len(vals)
    ))

# Also check last frame
f = s2.frames[-1]
vals = [v.data for v in f.fieldOutputs['SDV1'].values]
print("Frame %3d: time=%.4f, d_min=%.4f, d_max=%.4f" % (len(s2.frames)-1, f.frameValue, min(vals), max(vals)))

odb.close()
