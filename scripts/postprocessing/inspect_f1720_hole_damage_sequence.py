# -*- coding: utf-8 -*-
"""
scripts/postprocessing/inspect_f1720_hole_damage_sequence.py

Inspects spatial phase-field damage evolution around all 5 holes (h1 through h5)
in PK_F1720_ADAPTED_PFM.odb across key frames, to reconcile the nucleation
and growth sequence with Pandey & Kumar (2025, Section 4.5, page 3277).
"""

import sys
import json
from odbAccess import openOdb

odb_path = r'models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.odb'
odb = openOdb(odb_path, readOnly=True)

root_assembly = odb.rootAssembly
instance = root_assembly.instances['PART-1-1'] if 'PART-1-1' in root_assembly.instances.keys() else root_assembly.instances.values()[0]

# Precompute element centroids
element_centroids = {}
for elem in instance.elements:
    conn = elem.connectivity
    coords = [instance.nodes[n_idx - 1].coordinates for n_idx in conn]
    cx = sum(c[0] for c in coords) / len(coords)
    cy = sum(c[1] for c in coords) / len(coords)
    element_centroids[elem.label] = (cx, cy)

n_phys = 13163
# Layer 3 UMAT overlay elements have label > 2 * n_phys
# Physical element label = elem.label - 2 * n_phys

# Holes definition:
# h1: (0, 0.5), r = 0.1
# h2: (0.35, 0.45), r = 0.1
# h3: (0.6, 0.55), r = 0.05
# h4: (0.75, 0.5), r = 0.075
# h5: (1, 0.45), r = 0.075

# Region boxes around holes / ligaments:
regions = {
    'h5_flank': {'x': (0.88, 1.00), 'y': (0.35, 0.55), 'desc': 'Hole 5 right edge flank'},
    'lig_h4_h5': {'x': (0.80, 0.95), 'y': (0.40, 0.55), 'desc': 'Ligament between h4 and h5'},
    'h4_flank': {'x': (0.68, 0.82), 'y': (0.42, 0.58), 'desc': 'Hole 4 interior flank'},
    'lig_h3_h4': {'x': (0.62, 0.72), 'y': (0.48, 0.58), 'desc': 'Narrowest ligament h3 <-> h4'},
    'h3_flank': {'x': (0.55, 0.65), 'y': (0.50, 0.60), 'desc': 'Hole 3 interior flank'},
    'lig_h2_h3': {'x': (0.40, 0.58), 'y': (0.40, 0.55), 'desc': 'Ligament between h2 and h3'},
    'lig_h1_h2': {'x': (0.05, 0.30), 'y': (0.40, 0.55), 'desc': 'Ligament between h1 and h2'},
}

# Collect frames across steps
all_frames = []
for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    for frame_idx, frame in enumerate(step.frames):
        all_frames.append((step_name, frame_idx, frame))

print("Total frames: %d" % len(all_frames))

# Extract all 179 frames without skipping
sample_indices = list(range(len(all_frames)))

results = []

for idx in sample_indices:
    step_name, frame_idx, frame = all_frames[idx]
    time_val = frame.frameValue

    # Extract displacement at RP (if available) or frame value
    # Check SDV1
    if 'SDV1' not in frame.fieldOutputs.keys():
        continue

    sdv1_field = frame.fieldOutputs['SDV1']
    
    # Track max damage in each region
    reg_max_d = {r: 0.0 for r in regions}
    reg_max_el = {r: 0 for r in regions}
    
    global_max_d = 0.0
    global_max_el = 0

    for val in sdv1_field.values:
        el_label = val.elementLabel
        if el_label <= 2 * n_phys:
            continue
        phys_label = el_label - 2 * n_phys
        cx, cy = element_centroids.get(phys_label, (0.0, 0.0))
        d_val = float(val.data)
        
        if d_val > global_max_d:
            global_max_d = d_val
            global_max_el = phys_label

        for r_name, r_box in regions.items():
            if r_box['x'][0] <= cx <= r_box['x'][1] and r_box['y'][0] <= cy <= r_box['y'][1]:
                if d_val > reg_max_d[r_name]:
                    reg_max_d[r_name] = d_val
                    reg_max_el[r_name] = phys_label

    frame_record = {
        'frame_index': idx,
        'step_name': step_name,
        'step_frame': frame_idx,
        'time_val': time_val,
        'global_max_d': global_max_d,
        'global_max_el': global_max_el,
        'regions': {r: {'max_d': round(reg_max_d[r], 5), 'max_el': reg_max_el[r]} for r in regions}
    }
    results.append(frame_record)
    print("Frame %3d (Step %s, Fr %2d): global_max_d=%.4f (El %d) | h5_flank=%.4f | lig_h4_h5=%.4f | lig_h3_h4=%.4f" % (
        idx, step_name, frame_idx, global_max_d, global_max_el,
        reg_max_d['h5_flank'], reg_max_d['lig_h4_h5'], reg_max_d['lig_h3_h4']
    ))

odb.close()

out_path = 'results/validation/f1720_hole_damage_sequence.json'
with open(out_path, 'w') as f:
    json.dump(results, f, indent=2)

print("\nSaved damage sequence audit to %s" % out_path)
