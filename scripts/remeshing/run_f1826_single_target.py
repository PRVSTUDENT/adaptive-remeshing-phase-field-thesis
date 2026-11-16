# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1826_single_target.py
============================================
Task F1826: Adapter Harmonization & Original Gate 06 Verification Runner.
Executes a single benchmark case at a specified error target within an isolated Abaqus CAE session:
- Loads benchmark configuration
- Overrides error_target to the calibrated Pareto value
- Executes native Abaqus adaptiveRemesh() via harmonized reusable_2d_adaptive_framework.py
- Generates target physical mesh .inp in 270_f1826_adapter_harmonization/<case>
- Evaluates Gate 06 under the ORIGINAL geometric partition definition
- Computes supplementary size-thresholded and corner coarsening diagnostics
- Evaluates governing scientific resolution gates
- Writes audit receipt JSON using repo-relative paths
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    get_geometry_adapter,
    py_sum
)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def compute_body_sha256(inp_path):
    h = hashlib.sha256()
    with open(inp_path, "r") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


def to_repo_rel(path):
    if not path:
        return ""
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace("\\", "/")


def run_target(cid, error_target, out_dir, job_name):
    cases_meta = {
        "case_1": {
            "name": "Case 1: Mode-I Edge-Cracked Plate (Method A.2 Multi-State Recovery)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
            "l0_mm": 0.0075,
            "corner_filter": lambda cx, cy: (cx < 0.2 and (cy < 0.2 or cy > 0.8))
        },
        "case_2": {
            "name": "Case 2: Plate with an Off-Axis Hole (Method A.2 Multi-State Recovery)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2", "PK_HOLE_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
            "l0_mm": 0.0075,
            "corner_filter": lambda cx, cy: (cx < 0.2 and (cy < 0.2 or cy > 0.8))
        },
        "case_3": {
            "name": "Case 3: Notched Plate with Hole and Pins (Method A.2 Multi-State Recovery)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3", "SEC43_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
            "l0_mm": 0.285,
            "corner_filter": lambda cx, cy: (cx > 40.0 and (cy < 10.0 or cy > 110.0))
        },
        "case_5": {
            "name": "Case 5: Plate with Seven Holes (Table 6 Parity)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
            "expected_donor_sha": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E",
            "l0_mm": 0.0080,
            "corner_filter": lambda cx, cy: (cy < 0.15 and (cx < 0.2 or cx > 0.8))
        }
    }

    if cid not in cases_meta:
        raise ValueError("Unknown case ID: %s" % cid)

    meta = cases_meta[cid]
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("--- [F1826 Single] Case: %s | Target: %.2f%% ---" % (cid, error_target))

    cfg = AdaptiveConfig.from_json(meta["config_path"])
    cfg.error_target = float(error_target)

    donor_path = meta["donor_path"]
    if not os.path.exists(donor_path):
        raise RuntimeError("Donor ODB does not exist: %s" % donor_path)
    donor_sha = compute_sha256(donor_path)
    print("  Donor ODB SHA-256: %s" % donor_sha)

    # Execute Native Remesh
    model_name = "Model_F1826_%s" % cid.upper()
    phys_inp_path = os.path.join(out_dir, job_name + "_PHYS.inp")
    adapter = get_geometry_adapter(cfg)

    AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=donor_path,
        output_dir=out_dir,
        model_name=model_name,
        adapter_override=adapter,
        output_job_name=job_name
    )

    if not os.path.exists(phys_inp_path):
        raise RuntimeError("Expected physical mesh not found: %s" % phys_inp_path)

    inp_sha = compute_sha256(phys_inp_path)
    inp_body_sha = compute_body_sha256(phys_inp_path)
    print("  Generated INP: %s" % to_repo_rel(phys_inp_path))
    print("  INP Whole SHA: %s" % inp_sha)
    print("  INP Body  SHA: %s" % inp_body_sha)

    # Evaluate FE Quality Audit under Harmonized Adapter (Original Gate 06)
    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp_path, l0_mm=meta["l0_mm"], adapter=adapter)

    # Detailed Element Parse for Supplementary Diagnostics
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp_path)
    elem_coords = []
    all_h = []
    l0 = meta["l0_mm"]

    for eid, conn in quads.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != 4: continue
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*y[1] - y[0]*x[1]) + (x[1]*y[2] - y[1]*x[2]) + (x[2]*y[3] - y[2]*x[3]) + (x[3]*y[0] - y[3]*x[0]))
        h = math.sqrt(area) if area > 0 else 0.0
        cx = py_sum(x) / 4.0
        cy = py_sum(y) / 4.0
        all_h.append(h)
        elem_coords.append((cx, cy, h))

    for eid, conn in tris.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != 3: continue
        x = [p[0] for p in pts]
        y = [p[1] for p in pts]
        area = 0.5 * abs((x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1])))
        h = math.sqrt(area) if area > 0 else 0.0
        cx = py_sum(x) / 3.0
        cy = py_sum(y) / 3.0
        all_h.append(h)
        elem_coords.append((cx, cy, h))

    all_h.sort()
    min_h = all_h[0]
    med_h = all_h[len(all_h)//2]
    max_h = all_h[-1]

    # Supplementary: Size-Thresholded Partitioning
    size_pz = [h for h in all_h if h <= l0]
    size_ff = [h for h in all_h if h > l0]
    m_size_pz = py_sum(size_pz)/len(size_pz) if size_pz else 0.0
    m_size_ff = py_sum(size_ff)/len(size_ff) if size_ff else 0.0
    ratio_size_thresh = m_size_ff / m_size_pz if m_size_pz > 0 else 0.0

    # Supplementary: Geometric Corner Sampling
    corner_h = [h for (cx, cy, h) in elem_coords if meta["corner_filter"](cx, cy)]
    m_corner_h = py_sum(corner_h)/len(corner_h) if corner_h else 0.0
    max_corner_h = max(corner_h) if corner_h else 0.0
    ratio_corner_mean = m_corner_h / min_h if min_h > 0 else 0.0
    ratio_corner_max = max_corner_h / min_h if min_h > 0 else 0.0

    # Scientific Resolution Gates Evaluation
    scientific_gate_name = ""
    scientific_gate_status = "FAIL"
    scientific_metrics = {}

    if cid == "case_1":
        scientific_gate_name = "SCIENTIFIC_GATE_FULL_LIGAMENT"
        lig_elems = [h for (cx, cy, h) in elem_coords if cx >= 0.5 and abs(cy - 0.5) <= 0.02]
        pass_list = [h for h in lig_elems if h <= l0 / 2.0]
        n_pass = len(pass_list)
        pct_pass = (float(n_pass) / len(lig_elems)) * 100.0 if lig_elems else 0.0
        scientific_metrics = {
            "ligament_elements": len(lig_elems),
            "pct_le_l0_half": pct_pass,
            "threshold_pct": 95.0
        }
        scientific_gate_status = "PASS" if pct_pass >= 95.0 else "FAIL"

    elif cid == "case_2":
        scientific_gate_name = "SCIENTIFIC_GATE_OUTER_DISTAL"
        outer_elems = [h for (cx, cy, h) in elem_coords if cx >= 0.90 and abs(cy - 0.50) <= 0.05]
        pass_list = [h for h in outer_elems if h <= l0 / 2.0]
        n_pass = len(pass_list)
        pct_pass = (float(n_pass) / len(outer_elems)) * 100.0 if outer_elems else 0.0
        scientific_metrics = {
            "outer_distal_elements": len(outer_elems),
            "pct_le_l0_half": pct_pass,
            "threshold_pct": 95.0
        }
        scientific_gate_status = "PASS" if pct_pass >= 95.0 else "FAIL"

    elif cid == "case_3":
        scientific_gate_name = "SCIENTIFIC_GATE_SECONDARY_CORRIDOR"
        sec_elems = [h for (cx, cy, h) in elem_coords if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0]
        pass_list = [h for h in sec_elems if h <= l0]
        n_pass = len(pass_list)
        pct_pass = (float(n_pass) / len(sec_elems)) * 100.0 if sec_elems else 0.0
        scientific_metrics = {
            "secondary_corridor_elements": len(sec_elems),
            "pct_le_l0": pct_pass,
            "threshold_pct": 90.0
        }
        scientific_gate_status = "PASS" if pct_pass >= 90.0 else "FAIL"

    elif cid == "case_5":
        scientific_gate_name = "SCIENTIFIC_GATE_INTER_HOLE"
        inter_elems = [h for (cx, cy, h) in elem_coords if 0.30 <= cy <= 0.65 and 0.15 <= cx <= 0.85]
        pass_list = [h for h in inter_elems if h <= l0]
        n_pass = len(pass_list)
        pct_pass = (float(n_pass) / len(inter_elems)) * 100.0 if inter_elems else 0.0
        scientific_metrics = {
            "inter_hole_elements": len(inter_elems),
            "pct_le_l0": pct_pass,
            "threshold_pct": 90.0
        }
        scientific_gate_status = "PASS" if pct_pass >= 90.0 else "FAIL"

    # Compile Receipt
    orig_gate06 = "PASS" if audit["refinement_ratio_far_to_core"] >= 2.0 else "FAIL"

    receipt = {
        "case_id": cid,
        "name": meta["name"],
        "error_target_pct": error_target,
        "physical_mesh_path": to_repo_rel(phys_inp_path),
        "mesh_sha256": inp_sha,
        "mesh_body_sha256": inp_body_sha,
        "total_elements": audit["total_elements"],
        "quad_count": audit["quad_count"],
        "tri_count": audit["tri_count"],
        "quad_percent": audit["quad_percent"],
        "min_det_j": audit["min_det_j"],
        "max_aspect_ratio": audit["max_aspect_ratio"],
        "min_h_mm": min_h,
        "max_h_mm": max_h,
        "original_gate_06": {
            "definition": "Geometric domain partitioning via harmonized adapter classify_region()",
            "process_zone_count": audit["process_zone_elements_count"],
            "mean_pz_h_mm": audit["mean_process_zone_h_area_mm"],
            "mean_ff_h_mm": audit["mean_far_field_h_area_mm"],
            "refinement_ratio": audit["refinement_ratio_far_to_core"],
            "threshold": 2.0,
            "status": orig_gate06
        },
        "supplementary_diagnostics": {
            "size_thresholded": {
                "definition": "Size threshold h <= l0 vs h > l0",
                "pz_count": len(size_pz),
                "ff_count": len(size_ff),
                "mean_pz_h_mm": m_size_pz,
                "mean_ff_h_mm": m_size_ff,
                "refinement_ratio": round(ratio_size_thresh, 4),
                "status": "PASS" if ratio_size_thresh >= 2.0 else "FAIL"
            },
            "geometric_corner": {
                "definition": "Specimen corners far from defects vs crack core min size",
                "corner_sample_count": len(corner_h),
                "mean_corner_h_mm": m_corner_h,
                "max_corner_h_mm": max_corner_h,
                "ratio_corner_mean_to_min": round(ratio_corner_mean, 2),
                "ratio_corner_max_to_min": round(ratio_corner_max, 2)
            }
        },
        "scientific_gate": {
            "name": scientific_gate_name,
            "status": scientific_gate_status,
            "metrics": scientific_metrics
        }
    }

    # Copy abaqus.rpy execution journal
    rpy_src = os.path.join(REPO_ROOT, "abaqus.rpy")
    if os.path.exists(rpy_src):
        rpy_dst = os.path.join(out_dir, "%s_abaqus.rpy" % cid)
        shutil.copyfile(rpy_src, rpy_dst)
        receipt["execution_replay_journal"] = to_repo_rel(rpy_dst)

    receipt_path = os.path.join(out_dir, job_name + "_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)

    print("--- Finished %s: Elements=%d, Original Gate 06 Ratio=%.4fx (%s), Scientific Gate=%s ---" % (
        cid, audit["total_elements"], audit["refinement_ratio_far_to_core"], orig_gate06, scientific_gate_status
    ))
    return receipt


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: abaqus cae noGUI=run_f1826_single_target.py -- <cid> <error_target> <out_dir> <job_name>")
        sys.exit(1)
    cid_arg = sys.argv[-4]
    target_arg = float(sys.argv[-3])
    out_dir_arg = sys.argv[-2]
    job_arg = sys.argv[-1]
    run_target(cid_arg, target_arg, out_dir_arg, job_arg)
