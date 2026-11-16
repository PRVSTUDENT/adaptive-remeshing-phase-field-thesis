# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1816_step2_master.py
==========================================
Master orchestration for Step 2 of Task F1816: Envelope Construction.
Evaluates two envelope variants against the immutable F1812 baselines:
  - Variant 2a: Per-state overlapping native rules (multi-step donor ODB)
  - Variant 2b: Reduced 2-state envelope (breach/arrest state + terminal state)
Case 5 serves as unchanged regression control.

Computes:
  1. Finite element quality (quad fraction >= 90%, min det(J) > 0, max AR <= 4.0)
  2. Far-field coarsening ratio (Gate 06)
  3. Scientific resolution gates (Case 1 full ligament, Case 2 outer, Case 3 secondary, Case 5 inter-hole)
  4. Width metrics: fine elements (h <= l0/2) within 2*l0, 3*l0, 5*l0 of crack path.
"""
from __future__ import print_function
import os
import sys
import json
import math
import subprocess
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if os.path.join(REPO_ROOT, "scripts", "remeshing") not in sys.path:
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import (
    MeshQualityAuditEngine, AdaptiveConfig, get_geometry_adapter, py_sum
)

ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"
SINGLE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1816_step2_single.py")

BASE_STEP2_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope")
DONOR_DIR = os.path.join(BASE_STEP2_DIR, "donors")

C5_COARSE_DONOR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb")

CASES = {
    "case_1": {
        "name": "Case 1: Mode-I Edge-Cracked Plate",
        "error_target": 4.5,
        "l0": 0.0075,
        "segments": [((0.5, 0.5), (1.0, 0.5))],
        "donor_2a": os.path.join(DONOR_DIR, "PK_CASE1_MULTISTEP_RULES.odb"),
        "steps_2a": "RECOVERY_STEP,STATE_2,STATE_3,STATE_4,STATE_5",
        "donor_2b": os.path.join(DONOR_DIR, "PK_CASE1_2STATE_ENVELOPE.odb"),
        "steps_2b": "RECOVERY_STEP",
        "scientific_gate": "SCIENTIFIC_GATE_FULL_LIGAMENT",
        "f1812_baseline": {
            "elements": 25461, "f_3l0": 27.61, "gate_val": 97.19, "gate_pass": True, "coarsening": 2.39
        }
    },
    "case_2": {
        "name": "Case 2: Mode-I Plate with Off-Axis Hole",
        "error_target": 4.0,
        "l0": 0.0075,
        "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))],
        "donor_2a": os.path.join(DONOR_DIR, "PK_CASE2_MULTISTEP_RULES.odb"),
        "steps_2a": "RECOVERY_STEP,STATE_2,STATE_3,STATE_4",
        "donor_2b": os.path.join(DONOR_DIR, "PK_CASE2_2STATE_ENVELOPE.odb"),
        "steps_2b": "RECOVERY_STEP",
        "scientific_gate": "SCIENTIFIC_GATE_OUTER_DISTAL",
        "f1812_baseline": {
            "elements": 41438, "f_3l0": 14.58, "gate_val": 100.00, "gate_pass": True, "coarsening": 1.55
        }
    },
    "case_3": {
        "name": "Case 3: Notched Plate with Pins and Hole",
        "error_target": 3.0,
        "l0": 0.285,
        "segments": [((30.0, 60.0), (50.0, 60.0)), ((70.0, 60.0), (120.0, 60.0))],
        "donor_2a": os.path.join(DONOR_DIR, "PK_CASE3_MULTISTEP_RULES.odb"),
        "steps_2a": "RECOVERY_STEP,STATE_2,STATE_3",
        "donor_2b": os.path.join(DONOR_DIR, "PK_CASE3_2STATE_ENVELOPE.odb"),
        "steps_2b": "RECOVERY_STEP",
        "scientific_gate": "SCIENTIFIC_GATE_SECONDARY_CORRIDOR",
        "f1812_baseline": {
            "elements": 77779, "f_3l0": 0.49, "gate_val": 93.84, "gate_pass": True, "coarsening": 1.65
        }
    },
    "case_5": {
        "name": "Case 5: Plate with Seven Holes (Control)",
        "error_target": 5.68,
        "l0": 0.0080,
        "segments": [
            ((0.0, 0.40), (0.15, 0.40)),
            ((0.15, 0.40), (0.30, 0.60)),
            ((0.30, 0.60), (0.50, 0.55)),
            ((0.50, 0.55), (0.70, 0.60)),
            ((0.70, 0.60), (0.85, 0.50))
        ],
        "donor_2a": C5_COARSE_DONOR,
        "steps_2a": "Step-2",
        "donor_2b": C5_COARSE_DONOR,
        "steps_2b": "Step-2",
        "scientific_gate": "SCIENTIFIC_GATE_INTER_HOLE",
        "f1812_baseline": {
            "elements": 15466, "f_3l0": 29.31, "gate_val": 99.04, "gate_pass": True, "coarsening": 2.12
        }
    }
}

def point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)

def point_to_polyline_dist(px, py, segments):
    return min(point_to_segment_dist(px, py, s[0][0], s[0][1], s[1][0], s[1][1]) for s in segments)

def compute_width_metrics(inp_path, l0_mm, segments):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    fine_elements = []
    
    for eid, conn in list(quads.items()) + list(tris.items()):
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(p[0] for p in pts) / len(pts)
        cy = py_sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
        h = math.sqrt(area)
        
        if h <= l0_mm / 2.0 + 1e-9:
            d = point_to_polyline_dist(cx, cy, segments)
            fine_elements.append((cx, cy, h, d))
            
    n_fine = len(fine_elements)
    if n_fine == 0:
        return {"n_fine": 0, "f_2l0": 0.0, "f_3l0": 0.0, "f_5l0": 0.0}
        
    n_2l0 = py_sum(1 for e in fine_elements if e[3] <= 2.0 * l0_mm + 1e-9)
    n_3l0 = py_sum(1 for e in fine_elements if e[3] <= 3.0 * l0_mm + 1e-9)
    n_5l0 = py_sum(1 for e in fine_elements if e[3] <= 5.0 * l0_mm + 1e-9)
    
    return {
        "n_fine": n_fine,
        "n_2l0": n_2l0,
        "n_3l0": n_3l0,
        "n_5l0": n_5l0,
        "f_2l0": float(n_2l0) / n_fine * 100.0,
        "f_3l0": float(n_3l0) / n_fine * 100.0,
        "f_5l0": float(n_5l0) / n_fine * 100.0,
    }

def audit_case_gates(case_id, inp_path):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    all_elems = list(quads.items()) + list(tris.items())
    
    if case_id == "case_1":
        l0 = 0.0075
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
        n_fine = py_sum(1 for h in lig_elems if h <= l0 / 2.0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_FULL_LIGAMENT", "val": cov, "pass": cov >= 95.0, "threshold": ">= 95.0%"}
        
    elif case_id == "case_2":
        l0 = 0.0075
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
        n_fine = py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_OUTER_DISTAL", "val": cov, "pass": cov >= 99.9, "threshold": "100.00%"}
        
    elif case_id == "case_3":
        l0 = 0.285
        sec_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 75.0:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                sec_elems.append(h)
        n_tot = len(sec_elems)
        n_fine = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_SECONDARY_CORRIDOR", "val": cov, "pass": cov >= 90.0, "threshold": ">= 90.0%"}
        
    elif case_id == "case_5":
        l0 = 0.0080
        corridor_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.15 <= cx <= 0.85 and 0.40 <= cy <= 0.65:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                corridor_elems.append(h)
        n_tot = len(corridor_elems)
        n_fine = py_sum(1 for h in corridor_elems if h <= l0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        return {"gate": "SCIENTIFIC_GATE_INTER_HOLE", "val": cov, "pass": cov >= 90.0, "threshold": ">= 90.0%"}

def run_variant(variant_code, out_subdir):
    out_dir = os.path.join(BASE_STEP2_DIR, out_subdir)
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    results = {}
    print("\n" + "="*80)
    print("RUNNING VARIANT %s (%s)" % (variant_code.upper(), out_subdir))
    print("="*80)
    
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        cinfo = CASES[cid]
        donor_p = cinfo["donor_2a"] if variant_code == "2a" else cinfo["donor_2b"]
        steps_s = cinfo["steps_2a"] if variant_code == "2a" else cinfo["steps_2b"]
        job_name = "PK_F1816_V%s_%s" % (variant_code.upper(), cid.upper())
        
        param_dict = {
            "case_id": cid,
            "variant": variant_code,
            "donor_path": donor_p,
            "out_dir": out_dir,
            "error_target": cinfo["error_target"],
            "job_name": job_name,
            "step_names": [s.strip() for s in steps_s.split(",") if s.strip()]
        }
        param_path = os.path.join(out_dir, "params_%s_%s.json" % (variant_code, cid))
        with open(param_path, "w") as pf:
            json.dump(param_dict, pf, indent=2)
            
        phys_inp = os.path.join(out_dir, job_name + "_PHYS.inp")
        if not os.path.exists(phys_inp):
            print("\n>>> Launching %s under Variant %s..." % (cinfo["name"], variant_code))
            cmd = [
                ABAQUS_BAT, "cae", "noGUI=" + SINGLE_SCRIPT, "--", param_path
            ]
            t0 = time.time()
            ret = subprocess.call(cmd)
            elapsed = time.time() - t0
            print("  Exit code: %d (took %.2fs)" % (ret, elapsed))
            assert ret == 0, "Remeshing failed for %s under Variant %s" % (cid, variant_code)
        else:
            print("\n>>> Reusing existing physical mesh for %s under Variant %s: %s" % (cid, variant_code, phys_inp))
            
        assert os.path.exists(phys_inp), "Physical mesh not found: %s" % phys_inp
        
        # Audits
        cfg_map = {
            "case_1": "configs/remeshing/f1812_case1_native_miseseri.json",
            "case_2": "configs/remeshing/f1809_case2_native_miseseri.json",
            "case_3": "configs/remeshing/f1809_case3_native_miseseri.json",
            "case_5": "configs/remeshing/f1809_case5_native_miseseri.json"
        }
        with open(os.path.join(REPO_ROOT, cfg_map[cid]), "r") as cf:
            cdata = json.load(cf)
        cfg_obj = AdaptiveConfig(cdata)
        adapter_obj = get_geometry_adapter(cfg_obj)
        
        q_audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=cinfo["l0"], adapter=adapter_obj)
        w_audit = compute_width_metrics(phys_inp, cinfo["l0"], cinfo["segments"])
        g_audit = audit_case_gates(cid, phys_inp)
        
        coarsening_val = q_audit.get("refinement_ratio_far_to_core", 1.0)
        results[cid] = {
            "phys_inp": phys_inp,
            "elements": q_audit["total_elements"],
            "quads": q_audit["quad_count"],
            "tris": q_audit["tri_count"],
            "quad_fraction": q_audit["quad_percent"] / 100.0,
            "min_det_j": q_audit["min_signed_jacobian"],
            "max_ar": q_audit["max_aspect_ratio"],
            "coarsening_ratio": coarsening_val,
            "gate_06_pass": coarsening_val >= 2.0,
            "scientific_gate": g_audit,
            "width_metrics": w_audit,
            "f1812_baseline": cinfo["f1812_baseline"]
        }
        
        print("  Elements: %d (Quads: %.2f%%, min det(J): %.2e, max AR: %.2f)" % (
            q_audit["total_elements"], q_audit["quad_percent"],
            q_audit["min_signed_jacobian"], q_audit["max_aspect_ratio"]
        ))
        print("  Coarsening ratio (Gate 06): %.2fx (Pass: %s)" % (
            coarsening_val, coarsening_val >= 2.0
        ))
        print("  Scientific Gate: %s = %.2f%% (%s, Pass: %s)" % (
            g_audit["gate"], g_audit["val"], g_audit["threshold"], g_audit["pass"]
        ))
        print("  Fine Elements: %d | within 2*l0: %.2f%% | within 3*l0: %.2f%% | within 5*l0: %.2f%%" % (
            w_audit["n_fine"], w_audit["f_2l0"], w_audit["f_3l0"], w_audit["f_5l0"]
        ))
        print("  F1812 Baseline within 3*l0: %.2f%% (Delta: %+.2f percentage points)" % (
            cinfo["f1812_baseline"]["f_3l0"], w_audit["f_3l0"] - cinfo["f1812_baseline"]["f_3l0"]
        ))
        
    return results

def main():
    print("="*80)
    print("TASK F1816 STEP 2: ENVELOPE CONSTRUCTION MASTER EVALUATION")
    print("="*80)
    
    t_start = time.time()
    
    # Run Variant 2b (Reduced 2-State Envelope)
    res_2b = run_variant("2b", "variant_2b_reduced")
    
    # Run Variant 2a (Per-State Overlapping Native Rules)
    res_2a = run_variant("2a", "variant_2a_overlapping")
    
    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_runtime_s": time.time() - t_start,
        "variant_2b_reduced": res_2b,
        "variant_2a_overlapping": res_2a,
    }
    
    sum_path = os.path.join(BASE_STEP2_DIR, "step2_envelope_summary.json")
    with open(sum_path, "w") as f:
        json.dump(summary, f, indent=2)
        
    print("\n" + "="*80)
    print("STEP 2 EVALUATION SUMMARY TABLE")
    print("="*80)
    print("%-8s | %-12s | %-12s | %-12s | %-14s | %-14s | %-10s" % (
        "Case", "F1812 (El)", "Var 2b (El)", "Var 2a (El)", "F1812 3*l0(%)", "Var 2b 3*l0(%)", "Var 2a 3*l0(%)"
    ))
    print("-" * 95)
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        base_el = CASES[cid]["f1812_baseline"]["elements"]
        base_3l0 = CASES[cid]["f1812_baseline"]["f_3l0"]
        el_2b = res_2b[cid]["elements"]
        w_2b = res_2b[cid]["width_metrics"]["f_3l0"]
        el_2a = res_2a[cid]["elements"]
        w_2a = res_2a[cid]["width_metrics"]["f_3l0"]
        print("%-8s | %-12d | %-12d | %-12d | %-14.2f | %-14.2f | %-14.2f" % (
            cid, base_el, el_2b, el_2a, base_3l0, w_2b, w_2a
        ))
        
    print("\nSaved Step 2 summary to: %s" % sum_path)

if __name__ == "__main__":
    main()
