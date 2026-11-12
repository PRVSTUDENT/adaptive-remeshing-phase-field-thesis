# -*- coding: utf-8 -*-
"""
scripts/remeshing/diagnose_f1723_ligament_errors.py
==================================================
Examine MISESERI and MISESAVG in all four ligaments across frames of PK_F1720_COARSE_COUPLED.odb.
"""
from __future__ import print_function
import os
import sys
import json
import math
from odbAccess import openOdb

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")

odb = openOdb(COUPLED_ODB, readOnly=True)
inst = odb.rootAssembly.instances['PART-1-1']

# Compute element centroids
elem_centroids = {}
for elem in inst.elements:
    conn = elem.connectivity
    coords = [inst.getNodeFromLabel(n).coordinates for n in conn]
    cx = sum([c[0] for c in coords]) / float(len(coords))
    cy = sum([c[1] for c in coords]) / float(len(coords))
    elem_centroids[elem.label] = (cx, cy)

# Classify elements into the 4 ligaments
# Lig 1: h1 <-> h2: x in [0.08, 0.27], y in [0.40, 0.56]
# Lig 2: h2 <-> h3: x in [0.42, 0.57], y in [0.42, 0.58]
# Lig 3: h3 <-> h4: x in [0.63, 0.70], y in [0.48, 0.56]
# Lig 4: h4 <-> h5: x in [0.80, 0.95], y in [0.42, 0.54]
ligament_elems = {
    'lig1_h1_h2': [],
    'lig2_h2_h3': [],
    'lig3_h3_h4': [],
    'lig4_h4_h5': [],
    'bulk': []
}

for label, (cx, cy) in elem_centroids.items():
    if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
        ligament_elems['lig1_h1_h2'].append(label)
    elif 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
        ligament_elems['lig2_h2_h3'].append(label)
    elif 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56:
        ligament_elems['lig3_h3_h4'].append(label)
    elif 0.80 <= cx <= 0.95 and 0.42 <= cy <= 0.54:
        ligament_elems['lig4_h4_h5'].append(label)
    else:
        ligament_elems['bulk'].append(label)

print("Element counts:")
for k, v in ligament_elems.items():
    print("  %s: %d elements" % (k, len(v)))

def analyze_step_frames(step_name):
    step = odb.steps[step_name]
    print("\n" + "=" * 70)
    print("Analyzing Step: %s (%d frames)" % (step_name, len(step.frames)))
    print("=" * 70)

    # Pick sample frames
    n_frames = len(step.frames)
    indices = [0, 1, 3, 6, n_frames//2, n_frames - 1]
    # Remove duplicates and clamp
    indices = sorted(list(set([max(0, min(n_frames - 1, i)) for i in indices])))

    for idx in indices:
        f = step.frames[idx]
        t = f.frameValue
        if 'MISESERI' not in f.fieldOutputs or 'MISESAVG' not in f.fieldOutputs:
            continue
        miseseri_field = f.fieldOutputs['MISESERI']
        misesavg_field = f.fieldOutputs['MISESAVG']

        # Extract values
        miseseri_vals = {}
        for val in miseseri_field.values:
            miseseri_vals[val.elementLabel] = val.data

        misesavg_vals = {}
        for val in misesavg_field.values:
            misesavg_vals[val.elementLabel] = val.data

        # Overall average Mises
        avg_mises_global = sum(misesavg_vals.values()) / max(1, len(misesavg_vals))

        print("\n--- Frame %3d (t = %.6f) | Global MISESAVG = %.4f MPa ---" % (idx, t, avg_mises_global))
        print("  Ligament      | Count | Max MISESERI | Mean MISESERI | Max eta_e (%) | Mean eta_e (%)")
        print("  --------------+-------+--------------+---------------+---------------+---------------")
        for lig_name in ['lig1_h1_h2', 'lig2_h2_h3', 'lig3_h3_h4', 'lig4_h4_h5']:
            labels = ligament_elems[lig_name]
            eri_sub = [miseseri_vals.get(lbl, 0.0) for lbl in labels]
            avg_sub = [misesavg_vals.get(lbl, avg_mises_global) for lbl in labels]
            eta_sub = [(eri_sub[i] / max(1e-12, avg_sub[i])) * 100.0 for i in range(len(labels))]

            max_eri = max(eri_sub) if eri_sub else 0.0
            mean_eri = sum(eri_sub) / max(1, len(eri_sub))
            max_eta = max(eta_sub) if eta_sub else 0.0
            mean_eta = sum(eta_sub) / max(1, len(eta_sub))

            print("  %-13s | %5d | %12.4f | %13.4f | %13.2f | %13.2f" %
                  (lig_name, len(labels), max_eri, mean_eri, max_eta, mean_eta))

analyze_step_frames('Step-1')
analyze_step_frames('Step-2')

odb.close()
