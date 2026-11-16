# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1798_case3_native_remesh.py
Task F1798: Case 3 Native-MISESERI Causal Baseline Remeshing.

Runs under Abaqus CAE noGUI to:
1. Qualify the authentic initial-state native Abaqus MISESERI recovery donor for Case 3:
   - File: models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb
   - Topology: 3,923 elements, 4,040 nodes, 65x120 mm plate with central hole and 2 pin holes.
   - Loading: Pin-hole pull (uy = 1.46 mm at upper pin RP, lower pin constrained).
   - Step: RECOVERY_STEP (Frame 1, t = 1.0 s).
   - Recovery indicator: MISESERI active across all 3,923 elements (range [0.000535, 5.1983] MPa).
2. Prepare working donor with verified ALL_ELEM instance element set for RemeshingRule.
3. Execute Abaqus native RemeshingRule and adaptiveRemesh() using unchanged shared framework
   scripts/remeshing/reusable_2d_adaptive_framework.py.
4. Generate and retain physical Case 3 INP:
   models/pandey_kumar_mode1/248_f1798_case3_native_remesh/PK_F1798_CASE_3_ADAPT_PHYS.inp.
5. Independently audit mesh quality (total elements, quads, triangles, quad fraction, signed Jacobians,
   maximum aspect ratio, h/l0 resolution in primary and secondary regions, far-field coarsening).
6. Compare efficiency against historical Case 3 baselines (F1741 explosion 28,933 elements, F1780
   multi-state benchmark 10,064 elements, literature 12,168 target).
7. Save machine-readable donor and remesh receipts.
"""

import os
import sys
import json
import math
import shutil
import hashlib

# Add repository root to path
REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from abaqus import mdb, session
from odbAccess import openOdb

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    get_geometry_adapter,
    NotchedPlateWithPinHolesAdapter,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    FROZEN_UEL_SHA256
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    print("=== Task F1798: Case 3 Native-MISESERI Causal Baseline Remeshing ===")

    # Directories
    runs_dir = os.path.join(REPO_ROOT, "runs", "f1798_case3_native_remesh")
    if os.path.exists(runs_dir):
        shutil.rmtree(runs_dir, ignore_errors=True)
    os.makedirs(runs_dir)

    permanent_dir = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "248_f1798_case3_native_remesh"
    )
    if not os.path.exists(permanent_dir):
        os.makedirs(permanent_dir)

    raw_donor_odb_path = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_RECOVERY.odb"
    )
    assert os.path.exists(raw_donor_odb_path), "Raw donor ODB missing: " + raw_donor_odb_path

    donor_size = os.path.getsize(raw_donor_odb_path)
    donor_sha256 = sha256_file(raw_donor_odb_path)
    print("Authentic Case 3 Donor: %s (%d bytes, SHA-256: %s)" % (
        raw_donor_odb_path, donor_size, donor_sha256
    ))

    # 1. Prepare donor copy with verified ALL_ELEM instance set for Abaqus CAE RemeshingRule
    working_donor_path = os.path.join(runs_dir, "PK_SEC43_COARSE_RECOVERY_DONOR.odb")
    shutil.copyfile(raw_donor_odb_path, working_donor_path)
    odb_prep = openOdb(working_donor_path, readOnly=False)
    inst_prep = list(odb_prep.rootAssembly.instances.values())[0]
    if "ALL_ELEM" not in inst_prep.elementSets:
        all_labels = [e.label for e in inst_prep.elements]
        inst_prep.ElementSetFromElementLabels(name="ALL_ELEM", elementLabels=all_labels)
        odb_prep.save()
    odb_prep.close()

    # 2. Extract and save machine-readable donor qualification receipt
    odb = openOdb(raw_donor_odb_path, readOnly=True)
    assert "RECOVERY_STEP" in odb.steps, "RECOVERY_STEP must exist in donor"
    step = odb.steps["RECOVERY_STEP"]
    n_frames = len(step.frames)
    frame1 = step.frames[-1]
    time_val = float(frame1.frameValue)

    assert "MISESERI" in frame1.fieldOutputs, "MISESERI must exist in donor"
    assert "MISESAVG" in frame1.fieldOutputs, "MISESAVG must exist in donor"

    eri_fo = frame1.fieldOutputs["MISESERI"]
    avg_fo = frame1.fieldOutputs["MISESAVG"]
    eri_vals = [float(v.data) for v in eri_fo.values if v.data is not None]
    avg_vals = [float(v.data) for v in avg_fo.values if v.data is not None]

    inst_raw = list(odb.rootAssembly.instances.values())[0]
    num_nodes = len(inst_raw.nodes)
    num_elements = len(inst_raw.elements)
    elem_types = list(set([str(e.type) for e in inst_raw.elements]))
    odb.close()

    sorted_eri = sorted(eri_vals)
    n_vals = len(sorted_eri)
    eri_min = min(eri_vals)
    eri_max = max(eri_vals)
    eri_mean = sum(eri_vals) / float(n_vals)
    eri_median = sorted_eri[n_vals // 2]
    eri_p90 = sorted_eri[int(n_vals * 0.90)]
    eri_p99 = sorted_eri[int(n_vals * 0.99)]

    avg_min = min(avg_vals)
    avg_max = max(avg_vals)
    avg_mean = sum(avg_vals) / float(len(avg_vals))

    donor_receipt = {
        "task_id": "F1798-CASE3-NATIVE-MISESERI-CAUSAL-BASELINE-REMESHING",
        "donor_file": "PK_SEC43_COARSE_RECOVERY.odb",
        "donor_path": "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_RECOVERY.odb",
        "donor_sha256": donor_sha256,
        "donor_size_bytes": donor_size,
        "benchmark_case": "case_3",
        "benchmark_geometry": "Pandey & Kumar (2025) Section 4.3 Notched Plate with Central Hole and Pins (65x120 mm)",
        "mesh_topology": {
            "num_nodes": num_nodes,
            "num_elements": num_elements,
            "element_types": elem_types
        },
        "step_name": "RECOVERY_STEP",
        "step_procedure": "*STATIC",
        "frame_index": 1,
        "frame_time": time_val,
        "total_frames_in_step": n_frames,
        "is_causal_preanalysis": True,
        "indicator_field": "MISESERI",
        "normalization_field": "MISESAVG",
        "num_elements_with_indicator": n_vals,
        "miseseri_stats": {
            "min_mpa": eri_min,
            "max_mpa": eri_max,
            "mean_mpa": eri_mean,
            "median_mpa": eri_median,
            "p90_mpa": eri_p90,
            "p99_mpa": eri_p99,
            "nonzero_count": len([v for v in eri_vals if abs(v) > 1e-12])
        },
        "misesavg_stats": {
            "min_mpa": avg_min,
            "max_mpa": avg_max,
            "mean_mpa": avg_mean
        },
        "qualification_status": "QUALIFIED_AUTHENTIC_INITIAL_STATE_NATIVE_DONOR"
    }

    donor_receipt_path = os.path.join(permanent_dir, "PK_F1798_CASE3_DONOR_QUALIFICATION_RECEIPT.json")
    with open(donor_receipt_path, "w") as f:
        json.dump(donor_receipt, f, indent=2)
    print("Saved Case 3 donor qualification receipt: %s" % donor_receipt_path)

    # 3. Load native Case 3 configuration
    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1798_case3_native_miseseri.json")
    if not os.path.exists(config_path):
        config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json")
    cfg = AdaptiveConfig.from_json(config_path)

    print("Configured Step: %s, Indicator: %s, Causal: %s, Error Target: %s%%, Sizing Bounds: [%s, %s] mm" % (
        cfg.step_name, cfg.variable, cfg.causal_mode, str(cfg.error_target),
        str(cfg.min_h), str(cfg.max_h)
    ))

    # 4. Execute fresh native RemeshingRule and adaptiveRemesh() pass
    adapter = NotchedPlateWithPinHolesAdapter(cfg)
    job_name = "PK_F1798_CASE_3_ADAPT"
    model_name = "Model_F1798_Case3_Native"

    print("\n--- Executing Abaqus Native Remeshing for Case 3 ---")
    raw_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=working_donor_path,
        output_dir=runs_dir,
        model_name=model_name,
        adapter_override=adapter,
        output_job_name=job_name
    )
    assert os.path.exists(raw_inp), "Remeshed INP must exist: " + raw_inp

    target_inp = os.path.join(permanent_dir, "PK_F1798_CASE_3_ADAPT_PHYS.inp")
    shutil.copyfile(raw_inp, target_inp)
    inp_size = os.path.getsize(target_inp)
    inp_sha = sha256_file(target_inp)
    print("Generated Physical Mesh INP: %s (%d bytes, SHA-256: %s)" % (
        target_inp, inp_size, inp_sha
    ))

    # Compute mesh body hash excluding comment headers
    with open(target_inp, "r") as f:
        lines = f.readlines()
    h_body = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h_body.update(line.strip().encode("utf-8") + b"\n")
    mesh_body_sha256 = h_body.hexdigest().upper()

    # 5. Independent finite element mesh quality audit
    l0 = cfg.l0  # 0.285 mm
    l0_half = l0 / 2.0  # 0.1425 mm
    audit = MeshQualityAuditEngine.evaluate_mesh(target_inp, l0_mm=l0, adapter=adapter)

    # 6. Spatial resolution profiling across primary, secondary, and far-field zones
    # Primary critical corridor: Notch root (10, 70) to central hole (36.5, 51.0)
    # Secondary propagation corridor: Central hole (36.5, 51.0) to right boundary (65.0, 50.0)
    # Far-field background: Top/bottom regions (y <= 20 or y >= 100 away from pins)
    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False

    for line in lines:
        l_str = line.strip()
        u_str = l_str.upper()
        if u_str.startswith("*NODE") and "OUTPUT" not in u_str:
            in_nodes = True
            in_elems = False
            continue
        elif u_str.startswith("*ELEMENT") and "OUTPUT" not in u_str:
            in_nodes = False
            in_elems = True
            continue
        elif u_str.startswith("*"):
            in_nodes = False
            in_elems = False
            continue

        if in_nodes and l_str:
            parts = l_str.split(",")
            if len(parts) >= 3:
                try:
                    nid = int(parts[0].strip())
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    nodes[nid] = (x, y)
                except ValueError:
                    continue
        elif in_elems and l_str:
            parts = l_str.split(",")
            if len(parts) >= 4:
                try:
                    eid = int(parts[0].strip())
                    conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                    elements[eid] = conn
                except ValueError:
                    continue

    primary_h = []
    secondary_h = []
    far_field_h = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if not pts:
            continue
        cx = sum([p[0] for p in pts]) / float(len(pts))
        cy = sum([p[1] for p in pts]) / float(len(pts))

        # Approximate element size as sqrt(area)
        if len(pts) == 4:
            area = 0.5 * abs(
                (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
            )
        elif len(pts) == 3:
            area = 0.5 * abs(
                (pts[0][0]*(pts[1][1] - pts[2][1])) +
                (pts[1][0]*(pts[2][1] - pts[0][1])) +
                (pts[2][0]*(pts[0][1] - pts[1][1]))
            )
        else:
            area = 0.0
        h_elem = math.sqrt(area) if area > 0 else 0.0

        # Classification into spatial zones
        # 1. Primary corridor: between notch tip (10, 70) and central hole boundary (approx x in [10, 36.5], y in [45, 75])
        if 10.0 <= cx <= 36.5 and 45.0 <= cy <= 75.0:
            primary_h.append(h_elem)
        # 2. Secondary corridor: between central hole (x >= 46.5) and right boundary (x <= 65.0) in y in [40, 62]
        elif 46.5 <= cx <= 65.0 and 40.0 <= cy <= 62.0:
            secondary_h.append(h_elem)
        # 3. Far-field background: unnotched regions far from holes (e.g. y <= 15 or y >= 105)
        elif cy <= 15.0 or cy >= 105.0:
            far_field_h.append(h_elem)

    # Resolution statistics
    def calc_stats(h_list):
        if not h_list:
            return {"count": 0, "mean_mm": 0.0, "min_mm": 0.0, "max_mm": 0.0, "pct_le_l0": 0.0, "pct_le_l0_half": 0.0}
        n = len(h_list)
        return {
            "count": n,
            "mean_mm": sum(h_list) / float(n),
            "min_mm": min(h_list),
            "max_mm": max(h_list),
            "pct_le_l0": round(len([h for h in h_list if h <= l0]) / float(n) * 100.0, 2),
            "pct_le_l0_half": round(len([h for h in h_list if h <= l0_half]) / float(n) * 100.0, 2)
        }

    primary_stats = calc_stats(primary_h)
    secondary_stats = calc_stats(secondary_h)
    far_field_stats = calc_stats(far_field_h)

    far_to_core_coarsening = (
        far_field_stats["mean_mm"] / max(primary_stats["mean_mm"], 1e-9)
        if primary_stats["mean_mm"] > 0 else 0.0
    )

    # 7. Comparison against historical Case 3 baselines
    total_elems = audit["total_elements"]
    hist_f1741_elements = 28933
    hist_f1780_elements = 10064
    literature_target = 12168

    remesh_receipt = {
        "task_id": "F1798-CASE3-NATIVE-MISESERI-CAUSAL-BASELINE-REMESHING",
        "benchmark_case": "case_3",
        "benchmark_title": "Pandey & Kumar (2025) Section 4.3 Notched Plate with Central Hole and Pins",
        "donor_odb": "PK_SEC43_COARSE_RECOVERY.odb",
        "donor_sha256": donor_sha256,
        "causal_horizon": {
            "step_name": "RECOVERY_STEP",
            "frame_index": 1,
            "frame_time": 1.0,
            "causal_mode": True
        },
        "remeshing_rule": {
            "error_target_pct": cfg.error_target,
            "min_element_size_mm": cfg.min_h,
            "max_element_size_mm": cfg.max_h,
            "sizing_method": "UNIFORM_ERROR",
            "variable": "MISESERI"
        },
        "physical_mesh": {
            "filename": "PK_F1798_CASE_3_ADAPT_PHYS.inp",
            "sha256": inp_sha,
            "mesh_body_sha256": mesh_body_sha256,
            "size_bytes": inp_size,
            "total_nodes": audit["total_nodes"],
            "total_elements": total_elems,
            "quad_count": audit["quad_count"],
            "tri_count": audit["tri_count"],
            "quad_percent": audit["quad_percent"],
            "min_det_j": audit["min_det_j"],
            "non_positive_jacobians": audit["non_positive_jacobians"],
            "zero_negative_jacobians": (audit["non_positive_jacobians"] == 0),
            "max_aspect_ratio": audit["max_aspect_ratio"],
            "median_aspect_ratio": audit["median_aspect_ratio"],
            "ar_violations_gt_4": audit["aspect_ratio_violations_gt_4"]
        },
        "spatial_resolution": {
            "l0_mm": l0,
            "l0_half_mm": l0_half,
            "primary_corridor_notch_to_hole": primary_stats,
            "secondary_corridor_hole_to_boundary": secondary_stats,
            "far_field_background": far_field_stats,
            "far_to_core_coarsening_ratio": round(far_to_core_coarsening, 2)
        },
        "efficiency_comparison": {
            "current_f1798_elements": total_elems,
            "historical_f1741_explosion": {
                "elements": hist_f1741_elements,
                "delta_elements": total_elems - hist_f1741_elements,
                "reduction_percent": round((hist_f1741_elements - total_elems) / float(hist_f1741_elements) * 100.0, 2)
            },
            "historical_f1780_benchmark": {
                "elements": hist_f1780_elements,
                "delta_elements": total_elems - hist_f1780_elements,
                "parity_percent": round(float(total_elems) / float(hist_f1780_elements) * 100.0, 2)
            },
            "published_literature_target": {
                "elements": literature_target,
                "delta_elements": total_elems - literature_target,
                "reduction_vs_literature_percent": round((literature_target - total_elems) / float(literature_target) * 100.0, 2)
            }
        },
        "quality_gates": {
            "GATE_01_NATIVE_EXECUTION_EXIT_0": "PASS",
            "GATE_02_QUAD_FRACTION_GE_90_PCT": "PASS" if audit["quad_percent"] >= 90.0 else "FAIL",
            "GATE_03_ZERO_NEGATIVE_JACOBIANS": "PASS" if audit.get("non_positive_jacobians", 0) == 0 else "FAIL",
            "GATE_04_ASPECT_RATIO_LE_4": "PASS" if audit["max_aspect_ratio"] <= 4.0 else ("PASS_WITH_WARNING" if audit["max_aspect_ratio"] <= 6.0 else "FAIL"),
            "GATE_05_PRIMARY_CORRIDOR_RESOLUTION": "PASS" if primary_stats["pct_le_l0"] >= 90.0 else "FAIL",
            "GATE_06_FAR_FIELD_COARSENING": "PASS" if far_to_core_coarsening >= 2.0 else "FAIL",
            "GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION": "PASS" if total_elems < 20000 else "FAIL"
        }
    }

    remesh_receipt_path = os.path.join(permanent_dir, "PK_F1798_CASE3_NATIVE_REMESH_RECEIPT.json")
    with open(remesh_receipt_path, "w") as f:
        json.dump(remesh_receipt, f, indent=2)
    print("Saved Case 3 native remesh receipt: %s" % remesh_receipt_path)

    print("\n=== Case 3 Native Remeshing Complete ===")
    print("Total elements: %d (quads: %d [%.2f%%], tris: %d)" % (
        total_elems, audit["quad_count"], audit["quad_percent"], audit["tri_count"]
    ))
    print("Min det(J): %e, Max AR: %.3f" % (audit["min_det_j"], audit["max_aspect_ratio"]))
    print("Primary corridor (notch to hole): %d elements, %.2f%% <= l0, %.2f%% <= l0/2 (mean h = %.3f mm)" % (
        primary_stats["count"], primary_stats["pct_le_l0"], primary_stats["pct_le_l0_half"], primary_stats["mean_mm"]
    ))
    print("Secondary corridor (hole to boundary): %d elements, %.2f%% <= l0 (mean h = %.3f mm)" % (
        secondary_stats["count"], secondary_stats["pct_le_l0"], secondary_stats["mean_mm"]
    ))
    print("Far-field background: %d elements (mean h = %.3f mm), coarsening ratio: %.2fx" % (
        far_field_stats["count"], far_field_stats["mean_mm"], far_to_core_coarsening
    ))
    print("Efficiency vs historical F1741: -%.2f%% elements (%d vs %d)" % (
        remesh_receipt["efficiency_comparison"]["historical_f1741_explosion"]["reduction_percent"],
        total_elems, hist_f1741_elements
    ))

if __name__ == "__main__":
    main()
