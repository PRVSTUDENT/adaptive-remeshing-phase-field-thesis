# -*- coding: utf-8 -*-
"""
probe_case2_crack_breach.py
Inspect the crack breach into the off-axis hole across frames 160 to 220.
"""
from odbAccess import openOdb

odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
odb = openOdb(odb_path, readOnly=True)
s2 = odb.steps['Step-2']
root_inst = odb.rootAssembly.instances.values()[0]

# Pre-calculate element centroid
elem_centers = {}
for elem in root_inst.elements:
    conn = elem.connectivity
    pts = [root_inst.nodes[nid-1].coordinates for nid in conn]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    elem_centers[elem.label] = (cx, cy)

print("Hole center: (0.65, 0.65), radius: 0.10")
print("Notch tip: (0.50, 0.50)")
# Primary corridor: x in [0.50, 0.65], y between notch and hole
# Hole boundary: distance to (0.65, 0.65) approx 0.10
# Distal corridor: x > 0.65, y near hole right edge (x in [0.75, 1.0], y in [0.55, 0.75])

for frame_idx in [160, 170, 175, 180, 190, 200, 210, 220, 250]:
    f = s2.frames[frame_idx]
    sdv1 = f.fieldOutputs['SDV1']
    
    # Average damage per element
    elem_d = {}
    for v in sdv1.values:
        el = v.elementLabel
        elem_d.setdefault(el, []).append(v.data)
    
    elem_mean_d = {el: sum(vals)/len(vals) for el, vals in elem_d.items()}
    
    # Check max damage near notch tip (x in [0.50, 0.55], y in [0.48, 0.52])
    notch_d = max(d for el, d in elem_mean_d.items() if 0.50 <= elem_centers[el][0] <= 0.55 and 0.48 <= elem_centers[el][1] <= 0.52)
    # Check max damage near hole entrance (x in [0.55, 0.65], y in [0.52, 0.60])
    hole_in_d = max(d for el, d in elem_mean_d.items() if 0.55 <= elem_centers[el][0] <= 0.65 and 0.52 <= elem_centers[el][1] <= 0.62)
    # Check max damage in distal ligament (x in [0.75, 1.0], y in [0.55, 0.75])
    distal_d = max(d for el, d in elem_mean_d.items() if 0.75 <= elem_centers[el][0] <= 1.0 and 0.55 <= elem_centers[el][1] <= 0.75)
    
    # Number of elements with d > 0.8
    num_broken = sum(1 for d in elem_mean_d.values() if d > 0.8)
    num_damaged = sum(1 for d in elem_mean_d.values() if d > 0.2)
    
    print("Frame %3d (time=%.4f, uy=%.6f): notch_d=%.4f, hole_in_d=%.4f, distal_d=%.4f, broken(d>0.8)=%d, damaged(d>0.2)=%d" % (
        frame_idx, f.frameValue, f.fieldOutputs['U'].values[0].data[1] if f.fieldOutputs['U'].values else 0.0,
        notch_d, hole_in_d, distal_d, num_broken, num_damaged
    ))

odb.close()
