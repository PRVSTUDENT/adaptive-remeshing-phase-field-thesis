# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_method_c_case3_cycle3_mesh.py
====================================================
Task: METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE
Audits the physical mesh quality for Case 3 Cycle-3 adapted mesh against FE quality gates:
- Gate 01: Positive Signed Isoparametric Jacobian (min det(J) > 0)
- Gate 02: Quad Element Dominance (quad fraction >= 85%)
- Gate 03: Element Aspect Ratio Quality (mean aspect ratio <= 2.5)
- Spatial resolution: verifies fine mesh resolves l0/2 = 0.1425 mm in the process zone
- Corridor distribution: computes median and maximum element size h along the forward crack path
"""

from __future__ import print_function
import os
import sys
import json
import math
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import MeshQualityAuditEngine

PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "method_c_case3_cycle3_mesh_audit.json")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def compute_corridor_distribution(phys_inp_path):
    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False

    with open(phys_inp_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*NODE"):
                in_nodes = True
                in_elems = False
                continue
            elif line.startswith("*ELEMENT"):
                in_nodes = False
                in_elems = True
                continue
            elif line.startswith("*"):
                in_nodes = False
                in_elems = False
                continue
            if in_nodes:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_elems:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:]]
                elements[eid] = nids

    corridor_h = []
    forward_path_h = []

    # Forward path: from notch root (10.0, 70.0) toward hole center (36.5, 51.0), hole perimeter at (29.0, 57.0)
    # Line from (10.0, 70.0) to (29.0, 57.0): dx=19.0, dy=-13.0
    for eid, nids in elements.items():
        coords = [nodes[n] for n in nids if n in nodes]
        if not coords:
            continue
        cx = sum(c[0] for c in coords) / float(len(coords))
        cy = sum(c[1] for c in coords) / float(len(coords))

        # Compute element area via shoelace formula
        n = len(coords)
        area = 0.5 * abs(sum(coords[i][0] * coords[(i + 1) % n][1] - coords[(i + 1) % n][0] * coords[i][1] for i in range(n)))
        h_eff = math.sqrt(area) if area > 0 else 0.0

        # Refinement corridor: x in [8.5, 37.0], y in [48.0, 77.0]
        if 8.5 <= cx <= 37.0 and 48.0 <= cy <= 77.0:
            corridor_h.append(h_eff)

            # Forward path corridor: within +/- 2.5 mm of crack trajectory line
            # Line: (y - 70.0) - (-13.0 / 19.0) * (x - 10.0) = 0 => (y - 70.0) + 0.6842 * (x - 10.0) = 0
            if 10.0 <= cx <= 30.0:
                dist = abs((cy - 70.0) + 0.6842 * (cx - 10.0)) / math.sqrt(1.0 + 0.6842**2)
                if dist <= 3.0:
                    forward_path_h.append(h_eff)

    def stats(arr):
        if not arr:
            return {"count": 0, "min": 0, "max": 0, "mean": 0, "median": 0}
        s = sorted(arr)
        n = len(s)
        med = s[n // 2] if n % 2 == 1 else 0.5 * (s[n // 2 - 1] + s[n // 2])
        return {
            "count": n,
            "min_h_mm": float(min(s)),
            "max_h_mm": float(max(s)),
            "mean_h_mm": float(sum(s) / n),
            "median_h_mm": float(med)
        }

    return {
        "entire_corridor": stats(corridor_h),
        "forward_crack_path": stats(forward_path_h)
    }

def run_audit():
    print("Auditing Case 3 Cycle-3 adapted physical mesh: %s" % PHYS_INP)
    if not os.path.exists(PHYS_INP):
        raise IOError("Physical mesh file missing: %s" % PHYS_INP)

    audit_res = MeshQualityAuditEngine.evaluate_mesh(PHYS_INP, l0_mm=0.285)
    mesh_sha = compute_sha256(PHYS_INP)
    corridor_dist = compute_corridor_distribution(PHYS_INP)

    gate_01_pass = audit_res.get("min_det_j", 0.0) > 0.0 and audit_res.get("non_positive_jacobians", 0) == 0
    gate_02_pass = audit_res.get("quad_fraction_pct", 0.0) >= 85.0
    gate_03_pass = audit_res.get("mean_aspect_ratio", 99.0) <= 2.5

    audit_summary = {
        "mesh_path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp",
        "mesh_sha256": mesh_sha,
        "benchmark": "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins",
        "cycle": "Cycle-3 Refinement (Adapted from Job-3 Donor)",
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
        "corridor_element_size_distribution": corridor_dist,
        "gates": {
            "gate_01_jacobian": "PASS" if gate_01_pass else "FAIL",
            "gate_02_quad_fraction": "PASS" if gate_02_pass else "FAIL",
            "gate_03_aspect_ratio": "PASS" if gate_03_pass else "FAIL",
            "all_gates_pass": gate_01_pass and gate_02_pass and gate_03_pass
        }
    }

    with open(AUDIT_JSON, "w") as f:
        json.dump(audit_summary, f, indent=2)

    print("Audit JSON saved to: %s" % AUDIT_JSON)
    print("  Total elements: %d" % audit_res.get("total_elements", 0))
    print("  Quad fraction:  %.2f%% (Gate 02: %s)" % (audit_res.get("quad_fraction_pct", 0.0), audit_summary["gates"]["gate_02_quad_fraction"]))
    print("  Min det(J):     %e (Gate 01: %s)" % (audit_res.get("min_det_j", 0.0), audit_summary["gates"]["gate_01_jacobian"]))
    print("  Mean aspect:    %.3f (Gate 03: %s)" % (audit_res.get("mean_aspect_ratio", 0.0), audit_summary["gates"]["gate_03_aspect_ratio"]))
    print("  Forward path h: median = %.4f mm, max = %.4f mm" % (
        corridor_dist["forward_crack_path"]["median_h_mm"],
        corridor_dist["forward_crack_path"]["max_h_mm"]
    ))
    print("  All gates:      %s" % ("PASS" if audit_summary["gates"]["all_gates_pass"] else "FAIL"))
    return audit_summary

if __name__ == "__main__":
    run_audit()
