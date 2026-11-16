# -*- coding: utf-8 -*-
"""
probe_case2_reaction_force.py
Examine reaction force RF2 vs displacement uy and frame index around crack breach.
"""
from odbAccess import openOdb

odb_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb"
odb = openOdb(odb_path, readOnly=True)
s2 = odb.steps['Step-2']
root_inst = odb.rootAssembly.instances.values()[0]

# Find top nodes (y = 1.0)
top_nodes = set()
for node in root_inst.nodes:
    if abs(node.coordinates[1] - 1.0) < 1e-5:
        top_nodes.add(node.label)

print("Found %d top nodes" % len(top_nodes))

for frame_idx in range(150, 220, 5):
    f = s2.frames[frame_idx]
    rf = f.fieldOutputs['RF']
    rf2_tot = sum(v.data[1] for v in rf.values if v.nodeLabel in top_nodes)
    
    u = f.fieldOutputs['U']
    uy_top = max(v.data[1] for v in u.values if v.nodeLabel in top_nodes)
    
    sdv1 = f.fieldOutputs['SDV1']
    d_max = max(v.data for v in sdv1.values)
    
    print("Frame %3d: time=%.4f, uy_top=%.6f mm, RF2=%.4f N (or kN?), d_max=%.4f" % (
        frame_idx, f.frameValue, uy_top, rf2_tot, d_max
    ))

odb.close()
