# -*- coding: utf-8 -*-
"""
Extract data from ODBs and INP for F1654 Method A Publication Figures.
"""
import sys
import os
import json
import odbAccess

print("--- Extracting Recovery ODB Data ---")
odb_rec = odbAccess.openOdb('PK_HOLE_RECOVERY_SOLVE.odb', readOnly=True)
frame_rec = odb_rec.steps['Step-1'].frames[-1]

# Nodes and elements of coarse mesh
inst_rec = odb_rec.rootAssembly.instances['PLATE-1']
coarse_nodes = {n.label: (float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_rec.nodes}

coarse_elements = {}
for el in inst_rec.elements:
    coarse_elements[el.label] = {
        'type': el.type,
        'connectivity': [int(lbl) for lbl in el.connectivity]
    }

# MISESERI, MISESAVG, S_mises
miseseri_field = frame_rec.fieldOutputs['MISESERI']
misesavg_field = frame_rec.fieldOutputs['MISESAVG']
s_field = frame_rec.fieldOutputs['S']

miseseri_by_elem = {}
for v in miseseri_field.values:
    if v.elementLabel not in miseseri_by_elem:
        miseseri_by_elem[v.elementLabel] = float(v.data)

misesavg_by_elem = {}
for v in misesavg_field.values:
    if v.elementLabel not in misesavg_by_elem:
        misesavg_by_elem[v.elementLabel] = float(v.data)

s_mises_by_elem = {}
for v in s_field.values:
    eid = v.elementLabel
    if eid not in s_mises_by_elem:
        s_mises_by_elem[eid] = []
    s_mises_by_elem[eid].append(float(v.mises))
# Average over integration points
for eid in s_mises_by_elem:
    vals = s_mises_by_elem[eid]
    s_mises_by_elem[eid] = float(sum(vals) / len(vals))

odb_rec.close()
print("Extracted coarse mesh: %d nodes, %d elements, %d MISESERI" % 
      (len(coarse_nodes), len(coarse_elements), len(miseseri_by_elem)))

# Extract Job 1 authentic damage SDV1
print("--- Extracting Job 1 Authentic Damage ---")
odb_j1 = odbAccess.openOdb('models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb', readOnly=True)
frame_j1 = odb_j1.steps['Step-1'].frames[-1]
sdv1_field = frame_j1.fieldOutputs['SDV1']
d_by_elem = {}
for v in sdv1_field.values:
    eid = v.elementLabel
    phys_id = eid - 2 * 2906 if eid > 2 * 2906 else eid
    if phys_id not in d_by_elem:
        d_by_elem[phys_id] = float(v.data)
odb_j1.close()
print("Extracted Job 1 damage: %d elements" % len(d_by_elem))

# Save coarse extraction to JSON
coarse_data = {
    'nodes': coarse_nodes,
    'elements': coarse_elements,
    'miseseri': miseseri_by_elem,
    'misesavg': misesavg_by_elem,
    's_mises': s_mises_by_elem,
    'damage_step1': d_by_elem
}

with open('f1654_coarse_data.json', 'w') as f:
    json.dump(coarse_data, f)
print("Saved f1654_coarse_data.json")
