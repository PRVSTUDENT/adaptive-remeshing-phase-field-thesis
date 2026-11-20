# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_method_c_case3_mesh.py
=============================================
Task: METHOD-C-CASE3-ADAPTATION-PACKAGE
Audits the physical mesh quality for Case 3 coarse mesh against FE quality gates:
- Gate 01: Positive Signed Isoparametric Jacobian (min det(J) > 0)
- Gate 02: Quad Element Dominance (quad fraction >= 85%)
- Gate 03: Element Aspect Ratio Quality (mean aspect ratio <= 2.5)
"""

from __future__ import print_function
import os
import sys
import json
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import MeshQualityAuditEngine

PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "PK_METHOD_C_CASE3_COARSE_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "method_c_case3_mesh_audit.json")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def run_audit():
    print("Auditing Case 3 coarse physical mesh: %s" % PHYS_INP)
    if not os.path.exists(PHYS_INP):
        raise IOError("Physical mesh file missing: %s" % PHYS_INP)

    audit_res = MeshQualityAuditEngine.evaluate_mesh(PHYS_INP, l0_mm=0.285)

    mesh_sha = compute_sha256(PHYS_INP)

    # Format quality gates
    gate_01_pass = audit_res.get("min_det_j", 0.0) > 0.0 and audit_res.get("non_positive_jacobians", 0) == 0
    gate_02_pass = audit_res.get("quad_fraction_pct", 0.0) >= 85.0
    gate_03_pass = audit_res.get("mean_aspect_ratio", 99.0) <= 2.5

    audit_summary = {
        "mesh_path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_PHYS.inp",
        "mesh_sha256": mesh_sha,
        "benchmark": "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins",
        "statistics": {
            "total_elements": audit_res.get("total_elements"),
            "quad_elements": audit_res.get("quad_count"),
            "tri_elements": audit_res.get("tri_count"),
            "quad_fraction_pct": audit_res.get("quad_fraction_pct"),
            "total_nodes": audit_res.get("total_nodes")
        },
        "quality_metrics": {
            "min_det_j": audit_res.get("min_det_j"),
            "non_positive_jacobians": audit_res.get("non_positive_jacobians"),
            "mean_aspect_ratio": audit_res.get("mean_aspect_ratio"),
            "max_aspect_ratio": audit_res.get("max_aspect_ratio"),
            "mean_h_area_mm": audit_res.get("mean_h_area_mm"),
            "min_h_area_mm": audit_res.get("min_h_area_mm"),
            "max_h_area_mm": audit_res.get("max_h_area_mm")
        },
        "gates": {
            "gate_01_jacobian": "PASS" if gate_01_pass else "FAIL",
            "gate_02_quad_fraction": "PASS" if gate_02_pass else "FAIL",
            "gate_03_aspect_ratio": "PASS" if gate_03_pass else "FAIL",
            "all_gates_pass": gate_01_pass and gate_02_pass and gate_03_pass
        }
    }

    with open(AUDIT_JSON, "w") as f:
        json.dump(audit_summary, f, indent=2)

    print("\nMESH QUALITY AUDIT RESULTS:")
    print("  Total elements:    %d (%d quads [%.2f%%], %d tris)" % (
        audit_summary["statistics"]["total_elements"],
        audit_summary["statistics"]["quad_elements"],
        audit_summary["statistics"]["quad_fraction_pct"],
        audit_summary["statistics"]["tri_elements"]
    ))
    print("  Total nodes:       %d" % audit_summary["statistics"]["total_nodes"])
    print("  Min det(J):        %.6e (%s)" % (
        audit_summary["quality_metrics"]["min_det_j"], audit_summary["gates"]["gate_01_jacobian"]
    ))
    print("  Quad fraction:     %.2f%% (%s)" % (
        audit_summary["statistics"]["quad_fraction_pct"], audit_summary["gates"]["gate_02_quad_fraction"]
    ))
    print("  Mean aspect ratio: %.4f (%s)" % (
        audit_summary["quality_metrics"]["mean_aspect_ratio"], audit_summary["gates"]["gate_03_aspect_ratio"]
    ))
    print("  All gates:         %s" % ("PASS" if audit_summary["gates"]["all_gates_pass"] else "FAIL"))
    print("  Audit JSON:        %s" % AUDIT_JSON)

    return audit_summary

if __name__ == "__main__":
    run_audit()
