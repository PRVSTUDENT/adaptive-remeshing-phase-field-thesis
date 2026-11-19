# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_method_c_cycle2_mesh.py
===============================================
Audits finite element mesh quality for the Method C Cycle-2 adapted receiver physical mesh:
- Min det(J) across all Gauss points
- Max Aspect Ratio (AR)
- Quad fraction
- Distorted element check
"""

from __future__ import print_function
import os
import sys
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case", "PK_METHOD_C_CYCLE2_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "method_c_cycle2_mesh_audit.json")

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

    gate_01_pass = res['jacobian_status'] == "PASS" and min_det_j > 0.0
    gate_02_pass = quad_frac >= 85.0
    gate_03_pass = mean_ar <= 2.5 and med_ar <= 1.8

    result = {
        "benchmark": "METHOD_C_CYCLE2_RECEIVER_MESH",
        "mesh_path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp",
        "metrics": {
            "total_elements": num_total,
            "quad_elements": num_quads,
            "tri_elements": num_tris,
            "quad_fraction_pct": round(quad_frac, 2),
            "min_det_j": min_det_j,
            "mean_aspect_ratio": round(mean_ar, 4),
            "median_aspect_ratio": round(med_ar, 4),
            "max_aspect_ratio": round(max_ar, 4)
        },
        "gates": {
            "jacobian_non_negative": gate_01_pass,
            "quad_fraction_ge_85pct": gate_02_pass,
            "aspect_ratio_mean_le_2p5": gate_03_pass,
            "all_gates_passed": gate_01_pass and gate_02_pass and gate_03_pass
        }
    }

    os.makedirs(os.path.dirname(AUDIT_JSON), exist_ok=True)
    with open(AUDIT_JSON, "w") as f:
        json.dump(result, f, indent=2)

    print("CYCLE 2 MESH AUDIT RESULT:")
    print("  Total elements: %d (Quads: %d [%.2f%%], Tris: %d)" % (
        num_total, num_quads, quad_frac, num_tris
    ))
    print("  Min det(J):     %e (status: %s)" % (min_det_j, res['jacobian_status']))
    print("  Aspect ratio:   mean=%.2f, median=%.2f, max=%.2f" % (mean_ar, med_ar, max_ar))
    print("  All gates pass: %s" % result["gates"]["all_gates_passed"])
    return result

if __name__ == "__main__":
    audit()
