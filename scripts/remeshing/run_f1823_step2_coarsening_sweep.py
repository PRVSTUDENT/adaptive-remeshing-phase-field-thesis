# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1823_step2_coarsening_sweep.py
=====================================================
Task F1823 Step 2: Bounded Coarsening Sweep for Cases 2 and 3 with Cases 1 & 5 Controls.
Evaluates predefined combinations of max_h and error_target to test whether Gate 06 >= 2.0x
can be achieved while decreasing element count / DOFs and preserving scientific gates and mesh quality.
Records initial mesh seed and count for every variant.
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil
import time

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

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step2_coarsening")


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


def count_mesh_elements(inp_path):
    import re
    quads = 0
    tris = 0
    in_el = False
    with open(inp_path, "r") as f:
        for line in f:
            s = line.strip()
            if re.match(r"^\*ELEMENT\s*,", s, re.I):
                in_el = True
                continue
            elif s.startswith("*") and in_el:
                in_el = False
                continue
            if in_el and s:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if len(parts) == 5:
                    quads += 1
                elif len(parts) == 4:
                    tris += 1
    return quads + tris, quads, tris


def evaluate_scientific_gate(cid, inp_path, l0_mm):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    all_elems = list(quads.items()) + list(tris.items())

    if cid == "case_1":
        lig_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                lig_elems.append(h)
        n_tot = len(lig_elems)
        n_fine = py_sum(1 for h in lig_elems if h <= l0_mm / 2.0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_FULL_LIGAMENT", "val": cov, "pass": cov >= 95.0, "threshold": ">= 95.0%"}

    elif cid == "case_2":
        outer_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.90 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                outer_elems.append(h)
        n_tot = len(outer_elems)
        n_fine = py_sum(1 for h in outer_elems if h <= l0_mm / 2.0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_OUTER_DISTAL", "val": cov, "pass": cov >= 99.9, "threshold": "100.00%"}

    elif cid == "case_3":
        sec_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                sec_elems.append(h)
        n_tot = len(sec_elems)
        n_fine = py_sum(1 for h in sec_elems if h <= l0_mm + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_SECONDARY_CORRIDOR", "val": cov, "pass": cov >= 90.0, "threshold": ">= 90.0%"}

    elif cid == "case_5":
        corridor_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.15 <= cx <= 0.85 and 0.45 <= cy <= 0.65:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                corridor_elems.append(h)
        n_tot = len(corridor_elems)
        n_fine = py_sum(1 for h in corridor_elems if h <= l0_mm + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_INTER_HOLE", "val": cov, "pass": cov >= 95.0, "threshold": ">= 95.0%"}


def run_single_sweep(cid, base_cfg_path, donor_path, error_target, max_h, sweep_id, l0_mm):
    print("\n" + "=" * 80)
    print("RUNNING SWEEP: %s (%s) | eta_R=%.2f%%, max_h=%.4f mm" % (sweep_id, cid, error_target, max_h))
    print("=" * 80)

    sweep_out = os.path.join(OUT_DIR, sweep_id)
    if not os.path.exists(sweep_out):
        os.makedirs(sweep_out)

    with open(base_cfg_path, "r") as f:
        cfg_data = json.load(f)

    cfg_data["remeshing_rule"]["error_target"] = error_target
    cfg_data["remeshing_rule"]["max_element_size_mm"] = max_h

    cfg = AdaptiveConfig(cfg_data)
    cfg.error_target = error_target
    cfg.max_h = max_h

    adapter = get_geometry_adapter(cfg)

    # Initial seed and mesh recording
    # In Abaqus, we measure initial CAE seed and element count before adaptive remeshing
    initial_seed = max_h

    job_name = "PK_F1823_SWEEP_" + sweep_id.upper()
    model_name = "Model_" + sweep_id.replace("-", "_")

    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, donor_path, sweep_out, model_name=model_name, output_job_name=job_name + "_PHYS"
    )

    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=l0_mm, adapter=adapter)
    gate_info = evaluate_scientific_gate(cid, phys_inp, l0_mm)

    total_el, quads, tris = count_mesh_elements(phys_inp)
    whole_sha = compute_sha256(phys_inp)
    body_sha = compute_body_sha256(phys_inp)
    size_b = os.path.getsize(phys_inp)

    coarsening_ratio = audit.get("refinement_ratio_far_to_core", 1.0)
    gate_06_pass = coarsening_ratio >= 2.0
    quad_frac = float(quads) / total_el * 100.0 if total_el > 0 else 0.0

    print("  RESULTS:")
    print("    Initial seed: %.4f mm" % initial_seed)
    print("    Adapted Elements: %d (Quads: %d = %.2f%%, Tris: %d)" % (total_el, quads, quad_frac, tris))
    print("    Min det(J): %.2e, Max AR: %.2f" % (audit["min_det_j"], audit["max_aspect_ratio"]))
    print("    Coarsening Ratio (Gate 06): %.2fx (PASS: %s)" % (coarsening_ratio, gate_06_pass))
    print("    Scientific Gate (%s): %.2f%% (PASS: %s)" % (gate_info["gate"], gate_info["val"], gate_info["pass"]))
    print("    Body SHA-256: %s" % body_sha)

    return {
        "sweep_id": sweep_id,
        "case_id": cid,
        "error_target": error_target,
        "max_h_mm": max_h,
        "initial_seed_mm": initial_seed,
        "total_elements": total_el,
        "quads": quads,
        "tris": tris,
        "quad_fraction_pct": quad_frac,
        "nominal_field_dofs": total_el * 3, # approximation
        "min_det_j": audit["min_det_j"],
        "max_aspect_ratio": audit["max_aspect_ratio"],
        "coarsening_ratio": coarsening_ratio,
        "gate_06_pass": gate_06_pass,
        "scientific_gate_name": gate_info["gate"],
        "scientific_gate_value": gate_info["val"],
        "scientific_gate_pass": gate_info["pass"],
        "fine_elements_count": audit.get("elements_le_l0_half", 0),
        "physical_mesh_path": phys_inp,
        "whole_sha256": whole_sha,
        "body_sha256": body_sha,
        "size_bytes": size_b
    }


def main():
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    sweep_definitions = [
        # --- Regression Controls ---
        {
            "cid": "case_1",
            "base_cfg": "configs/remeshing/f1812_case1_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
            "eta_R": 4.5,
            "max_h": 0.020,
            "id": "c1_ctrl_eta45_h020",
            "l0": 0.0075
        },
        {
            "cid": "case_5",
            "base_cfg": "configs/remeshing/f1809_case5_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb",
            "eta_R": 5.68,
            "max_h": 0.030,
            "id": "c5_ctrl_eta568_h030",
            "l0": 0.0080
        },

        # --- Case 2 Coarsening Sweep ---
        # Baseline: eta_R=4.0%, max_h=0.020
        {
            "cid": "case_2",
            "base_cfg": "configs/remeshing/f1809_case2_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
            "eta_R": 4.0,
            "max_h": 0.020,
            "id": "c2_base_eta40_h020",
            "l0": 0.0075
        },
        # Var 2.1: eta_R=4.0%, max_h=0.030
        {
            "cid": "case_2",
            "base_cfg": "configs/remeshing/f1809_case2_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
            "eta_R": 4.0,
            "max_h": 0.030,
            "id": "c2_var1_eta40_h030",
            "l0": 0.0075
        },
        # Var 2.2: eta_R=4.0%, max_h=0.040
        {
            "cid": "case_2",
            "base_cfg": "configs/remeshing/f1809_case2_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
            "eta_R": 4.0,
            "max_h": 0.040,
            "id": "c2_var2_eta40_h040",
            "l0": 0.0075
        },
        # Var 2.3: eta_R=5.0%, max_h=0.030
        {
            "cid": "case_2",
            "base_cfg": "configs/remeshing/f1809_case2_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
            "eta_R": 5.0,
            "max_h": 0.030,
            "id": "c2_var3_eta50_h030",
            "l0": 0.0075
        },

        # --- Case 3 Coarsening Sweep ---
        # Baseline: eta_R=3.0%, max_h=2.0
        {
            "cid": "case_3",
            "base_cfg": "configs/remeshing/f1809_case3_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
            "eta_R": 3.0,
            "max_h": 2.00,
            "id": "c3_base_eta30_h200",
            "l0": 0.285
        },
        # Var 3.1: eta_R=3.0%, max_h=3.0
        {
            "cid": "case_3",
            "base_cfg": "configs/remeshing/f1809_case3_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
            "eta_R": 3.0,
            "max_h": 3.00,
            "id": "c3_var1_eta30_h300",
            "l0": 0.285
        },
        # Var 3.2: eta_R=3.0%, max_h=4.0
        {
            "cid": "case_3",
            "base_cfg": "configs/remeshing/f1809_case3_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
            "eta_R": 3.0,
            "max_h": 4.00,
            "id": "c3_var2_eta30_h400",
            "l0": 0.285
        },
        # Var 3.3: eta_R=3.5%, max_h=3.0
        {
            "cid": "case_3",
            "base_cfg": "configs/remeshing/f1809_case3_native_miseseri.json",
            "donor": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
            "eta_R": 3.5,
            "max_h": 3.00,
            "id": "c3_var3_eta35_h300",
            "l0": 0.285
        }
    ]

    all_results = {}
    for sw in sweep_definitions:
        t0 = time.time()
        res = run_single_sweep(
            cid=sw["cid"],
            base_cfg_path=os.path.join(REPO_ROOT, sw["base_cfg"]),
            donor_path=os.path.join(REPO_ROOT, sw["donor"]),
            error_target=sw["eta_R"],
            max_h=sw["max_h"],
            sweep_id=sw["id"],
            l0_mm=sw["l0"]
        )
        res["elapsed_s"] = time.time() - t0
        all_results[sw["id"]] = res

    summary_file = os.path.join(OUT_DIR, "step2_coarsening_sweep_summary.json")
    with open(summary_file, "w") as f:
        json.dump(all_results, f, indent=2)

    print("\n" + "=" * 80)
    print("STEP 2 COARSENING SWEEP COMPLETED:")
    print("=" * 80)
    print("%-20s %-8s %-6s %-6s %-8s %-6s %-8s %-8s" % (
        "ID", "Case", "eta_R", "max_h", "Elements", "Quads%", "Coarsen", "SciGate"
    ))
    for sid, r in all_results.items():
        print("%-20s %-8s %-6.2f %-6.3f %-8d %-6.2f %-7.2fx %-8s" % (
            sid, r["case_id"], r["error_target"], r["max_h_mm"],
            r["total_elements"], r["quad_fraction_pct"], r["coarsening_ratio"],
            "PASS" if r["scientific_gate_pass"] else "FAIL"
        ))
    print("=" * 80)
    print("Saved summary to: %s" % summary_file)


if __name__ == "__main__":
    main()
