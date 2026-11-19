# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_method_c_demo_mesh.py
=============================================
Audits finite element mesh quality for the Method C demonstration benchmark coarse mesh:
- Min det(J) across all Gauss points
- Max Aspect Ratio (AR)
- Quad fraction
- Distorted element check
"""

from __future__ import print_function
import os
import sys
import json
import numpy as np

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_DEMO_COARSE_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "method_c_demo_coarse_mesh_audit.json")

def audit():
    res = MeshQualityAuditEngine.evaluate_mesh(PHYS_INP)

    mean_ar = res['mean_aspect_ratio']
    med_ar = res['median_aspect_ratio']
    max_ar = res['max_aspect_ratio']
    min_det_j = res['min_det_j']
    quad_frac = res['quad_fraction_pct']
    num_total = res['total_elements']
    num_quads = res['quad_count']
    num_tris = res['tri_count']

    # Quality Gate checks consistent with thesis benchmarks
    gate_01_pass = res['jacobian_status'] == "PASS" and min_det_j > 0.0
    gate_02_pass = quad_frac >= 85.0
    gate_03_pass = mean_ar <= 2.0 and med_ar <= 1.5

    result = {
        "benchmark": "METHOD_C_DEMO_PLATE_ON_AXIS_HOLE",
        "mesh_path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_COARSE_PHYS.inp",
        "metrics": {
            "total_elements": num_total,
            "quad_elements": num_quads,
            "tri_elements": num_tris,
            "quad_fraction_pct": round(quad_frac, 2),
            "total_nodes": res['total_nodes'],
            "min_det_jacobian": float(min_det_j),
            "max_aspect_ratio": round(float(max_ar), 4),
            "mean_aspect_ratio": round(mean_ar, 4),
            "median_aspect_ratio": round(med_ar, 4),
            "min_corner_angle_deg": round(res['min_corner_angle_deg'], 2),
            "max_corner_angle_deg": round(res['max_corner_angle_deg'], 2)
        },
        "gates": {
            "gate_01_min_det_j_positive": "PASS" if gate_01_pass else "FAIL",
            "gate_02_quad_fraction_ge_85": "PASS" if gate_02_pass else "FAIL",
            "gate_03_aspect_ratio_quality": "PASS" if gate_03_pass else "FAIL"
        }
    }


    out_dir = os.path.dirname(AUDIT_JSON)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    with open(AUDIT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    print("AUDIT RESULTS:")
    print("  Total Elements:  %d (%d quads [%.2f%%], %d tris)" % (num_total, num_quads, quad_frac, num_tris))
    print("  Min det(J):      %.6e (%s)" % (min_det_j, "PASS" if gate_01_pass else "FAIL"))
    print("  Max Aspect Ratio: %.4f (%s)" % (max_ar, "PASS" if gate_03_pass else "FAIL"))
    print("  Mean Aspect Ratio:%.4f" % mean_ar)
    print("  Saved audit to:  %s" % AUDIT_JSON)

if __name__ == "__main__":
    audit()
