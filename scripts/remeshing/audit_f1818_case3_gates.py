# -*- coding: utf-8 -*-
import sys
import math
import os

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))
from reusable_2d_adaptive_framework import MeshQualityAuditEngine, py_sum

paths = [
    ("Var 2b", os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "variant_2b_reduced", "PK_F1816_V2B_CASE_3_PHYS.inp")),
    ("Var 2a", os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "variant_2a_overlapping", "PK_F1816_V2A_CASE_3_PHYS.inp")),
]

l0 = 0.285

for label, p in paths:
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(p)
    all_elems = list(quads.items()) + list(tris.items())
    
    # 1. Correct corridor: y in [45.0, 65.0]
    sec_elems_corr = []
    # 2. Defective corridor: y in [45.0, 75.0]
    sec_elems_def = []
    
    for eid, conn in all_elems:
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(pt[0] for pt in pts) / len(pts)
        cy = py_sum(pt[1] for pt in pts) / len(pts)
        if 36.5 <= cx <= 65.0:
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            if 45.0 <= cy <= 65.0:
                sec_elems_corr.append(h)
            if 45.0 <= cy <= 75.0:
                sec_elems_def.append(h)
                
    n_tot_corr = len(sec_elems_corr)
    n_fine_corr = py_sum(1 for h in sec_elems_corr if h <= l0 + 1e-9)
    cov_corr = float(n_fine_corr) / n_tot_corr * 100.0 if n_tot_corr > 0 else 0.0
    
    n_tot_def = len(sec_elems_def)
    n_fine_def = py_sum(1 for h in sec_elems_def if h <= l0 + 1e-9)
    cov_def = float(n_fine_def) / n_tot_def * 100.0 if n_tot_def > 0 else 0.0
    
    print("%s:" % label)
    print("  Standard y in [45.0, 65.0]: n_tot=%d, n_fine=%d, cov=%.2f%% (PASS=%s)" % (n_tot_corr, n_fine_corr, cov_corr, cov_corr >= 90.0))
    print("  Defective y in [45.0, 75.0]: n_tot=%d, n_fine=%d, cov=%.2f%% (PASS=%s)" % (n_tot_def, n_fine_def, cov_def, cov_def >= 90.0))
