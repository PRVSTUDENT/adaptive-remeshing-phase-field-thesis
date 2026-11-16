# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1823_step3_targeted_donors.py
===================================================
Task F1823 Step 3: Targeted Donor Investigation (Selective, Not Blanket).
Investigates which omitted donor state supplies the missing coverage for Cases 2 and 3:
  - Case 2:
      Baseline: All 4 states (1: Initiation, 2: Hole Arrest, 3: Distal Nucleation, 4: Outer Propagation)
      Var 2.A: Omit State 1 (States 2, 3, 4) -> Test notch initiation redundancy
      Var 2.B: Omit State 3 (States 1, 2, 4) -> Test distal nucleation necessity
      Var 2.C: Omit State 4 (States 1, 2, 3) -> Test outer boundary propagation necessity
  - Case 3:
      Baseline: All 3 states (1: Initiation, 2: Hole Arrest, 3: Secondary Propagation)
      Var 3.A: Omit State 1 (States 2, 3) -> Test primary notch initiation necessity
      Var 3.B: Omit State 2 (States 1, 3) -> Test central hole arrest redundancy / elimination
      Var 3.C: Omit State 3 (States 1, 2) -> Test secondary propagation necessity
  - Controls:
      Case 1 Control: Method A.2 5-state baseline (eta_R = 4.5%, hmax = 0.020)
      Case 5 Control: Table 6 coarse baseline (eta_R = 5.68%, hmax = 0.030)

For every configuration, computes:
  1. Finite element quality (quad fraction >= 90%, min det(J) > 0, max AR <= 4.0)
  2. Gate 06 far-field coarsening ratio
  3. Scientific gate(s) pass %
  4. Width metrics: fine elements within 2*l0, 3*l0, 5*l0 of crack path, specifically reporting f_3l0.
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from abaqus import mdb
from abaqusConstants import *

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    get_geometry_adapter,
    py_sum
)

STEP3_BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "267_f1823_investigation", "step3_donors")
DONOR_DIR = os.path.join(STEP3_BASE_DIR, "donors")

C2_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2")
C3_SRC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3")

C1_BASELINE_DONOR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb")
C5_COARSE_DONOR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb")

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
        return {"n_fine": 0, "n_2l0": 0, "n_3l0": 0, "n_5l0": 0, "f_2l0": 0.0, "f_3l0": 0.0, "f_5l0": 0.0}
        
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
        notch_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            if 0.90 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                outer_elems.append(h)
            if 0.50 <= cx <= 0.65 and 0.50 <= cy <= 0.65:
                notch_elems.append(h)
        n_tot = len(outer_elems)
        n_fine = py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        
        n_notch_tot = len(notch_elems)
        n_notch_fine = py_sum(1 for h in notch_elems if h <= l0 / 2.0 + 1e-9)
        cov_notch = (float(n_notch_fine) / n_notch_tot * 100.0) if n_notch_tot > 0 else 0.0
        
        return {
            "gate": "SCIENTIFIC_GATE_OUTER_DISTAL",
            "val": cov,
            "pass": cov >= 99.9,
            "threshold": "100.00%",
            "extra_gate": "NOTCH_TO_HOLE_CORRIDOR",
            "extra_val": cov_notch
        }
        
    elif case_id == "case_3":
        l0 = 0.285
        sec_elems = []
        prim_elems = []
        for eid, conn in all_elems:
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 75.0:
                sec_elems.append(h)
            if 10.0 <= cx <= 36.5 and 50.0 <= cy <= 75.0:
                prim_elems.append(h)
        n_tot = len(sec_elems)
        n_fine = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
        cov = (float(n_fine) / n_tot * 100.0) if n_tot > 0 else 0.0
        
        n_prim_tot = len(prim_elems)
        n_prim_fine = py_sum(1 for h in prim_elems if h <= l0 + 1e-9)
        cov_prim = (float(n_prim_fine) / n_prim_tot * 100.0) if n_prim_tot > 0 else 0.0
        
        return {
            "gate": "SCIENTIFIC_GATE_SECONDARY_CORRIDOR",
            "val": cov,
            "pass": cov >= 90.0,
            "threshold": ">= 90.0%",
            "extra_gate": "PRIMARY_NOTCH_CORRIDOR",
            "extra_val": cov_prim
        }
        
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

def get_synthesized_donors():
    donors = {
        "c2_omit_s1": os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S1.odb"),
        "c2_omit_s3": os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S3.odb"),
        "c2_omit_s4": os.path.join(DONOR_DIR, "PK_C2_DONOR_OMIT_S4.odb"),
        "c3_omit_s1": os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S1.odb"),
        "c3_omit_s2": os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S2.odb"),
        "c3_omit_s3": os.path.join(DONOR_DIR, "SEC43_C3_DONOR_OMIT_S3.odb"),
    }
    for k, p in donors.items():
        if not os.path.exists(p):
            raise RuntimeError("Missing synthesized donor: %s" % p)
    return donors

def run_targeted_investigation():
    print("=" * 80)
    print("TASK F1823 STEP 3: TARGETED DONOR INVESTIGATION")
    print("=" * 80)
    
    synthesized_donors = get_synthesized_donors()
    
    c2_base_donor = os.path.join(C2_SRC_DIR, "PK_HOLE_MULTISTATE_RECOVERY.odb")
    c3_base_donor = os.path.join(C3_SRC_DIR, "SEC43_MULTISTATE_RECOVERY.odb")
    
    investigation_matrix = [
        # --- Regression Controls ---
        {
            "id": "c1_ctrl_5states",
            "case_id": "case_1",
            "desc": "Case 1 Control: All 5 States (States 1 to 5)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json"),
            "donor_path": C1_BASELINE_DONOR,
            "error_target": 4.5,
            "max_h": 0.020,
            "min_h": 0.0015,
            "l0": 0.0075,
            "segments": [((0.5, 0.5), (1.0, 0.5))],
            "omitted_state": "NONE (Control)"
        },
        {
            "id": "c5_ctrl_coarse",
            "case_id": "case_5",
            "desc": "Case 5 Control: Table 6 Coarse Donor",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "donor_path": C5_COARSE_DONOR,
            "error_target": 5.68,
            "max_h": 0.030,
            "min_h": 0.0015,
            "l0": 0.0080,
            "segments": [
                ((0.0, 0.40), (0.15, 0.40)),
                ((0.15, 0.40), (0.30, 0.60)),
                ((0.30, 0.60), (0.50, 0.55)),
                ((0.50, 0.55), (0.70, 0.60)),
                ((0.70, 0.60), (0.85, 0.50))
            ],
            "omitted_state": "NONE (Control)"
        },
        
        # --- Case 2 Targeted Donor Tests ---
        {
            "id": "c2_base_4states",
            "case_id": "case_2",
            "desc": "Case 2 Baseline: All 4 States (1: Preanalysis, 2: Arrest, 3: Distal Nuc, 4: Outer Prop)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": c2_base_donor,
            "error_target": 4.0,
            "max_h": 0.020,
            "min_h": 0.0015,
            "l0": 0.0075,
            "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))],
            "omitted_state": "NONE (All 4 States: 1+2+3+4)"
        },
        {
            "id": "c2_omit_state1",
            "case_id": "case_2",
            "desc": "Case 2 Omit State 1: States 2+3+4 (Test notch initiation redundancy)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": synthesized_donors["c2_omit_s1"],
            "error_target": 4.0,
            "max_h": 0.020,
            "min_h": 0.0015,
            "l0": 0.0075,
            "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))],
            "omitted_state": "State 1 (Initiation)"
        },
        {
            "id": "c2_omit_state3",
            "case_id": "case_2",
            "desc": "Case 2 Omit State 3: States 1+2+4 (Test distal nucleation necessity)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": synthesized_donors["c2_omit_s3"],
            "error_target": 4.0,
            "max_h": 0.020,
            "min_h": 0.0015,
            "l0": 0.0075,
            "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))],
            "omitted_state": "State 3 (Distal Nucleation)"
        },
        {
            "id": "c2_omit_state4",
            "case_id": "case_2",
            "desc": "Case 2 Omit State 4: States 1+2+3 (Test outer propagation necessity)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": synthesized_donors["c2_omit_s4"],
            "error_target": 4.0,
            "max_h": 0.020,
            "min_h": 0.0015,
            "l0": 0.0075,
            "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))],
            "omitted_state": "State 4 (Outer Propagation)"
        },

        # --- Case 3 Targeted Donor Tests ---
        {
            "id": "c3_base_3states",
            "case_id": "case_3",
            "desc": "Case 3 Baseline: All 3 States (1: Initiation, 2: Hole Arrest, 3: Secondary Prop)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": c3_base_donor,
            "error_target": 3.0,
            "max_h": 2.0,
            "min_h": 0.080,
            "l0": 0.285,
            "segments": [((30.0, 60.0), (50.0, 60.0)), ((50.0, 60.0), (65.0, 60.0))],
            "omitted_state": "NONE (All 3 States: 1+2+3)"
        },
        {
            "id": "c3_omit_state1",
            "case_id": "case_3",
            "desc": "Case 3 Omit State 1: States 2+3 (Test primary notch initiation necessity)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": synthesized_donors["c3_omit_s1"],
            "error_target": 3.0,
            "max_h": 2.0,
            "min_h": 0.080,
            "l0": 0.285,
            "segments": [((30.0, 60.0), (50.0, 60.0)), ((50.0, 60.0), (65.0, 60.0))],
            "omitted_state": "State 1 (Initiation)"
        },
        {
            "id": "c3_omit_state2",
            "case_id": "case_3",
            "desc": "Case 3 Omit State 2: States 1+3 (Test central hole arrest redundancy / elimination)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": synthesized_donors["c3_omit_s2"],
            "error_target": 3.0,
            "max_h": 2.0,
            "min_h": 0.080,
            "l0": 0.285,
            "segments": [((30.0, 60.0), (50.0, 60.0)), ((50.0, 60.0), (65.0, 60.0))],
            "omitted_state": "State 2 (Hole Arrest)"
        },
        {
            "id": "c3_omit_state3",
            "case_id": "case_3",
            "desc": "Case 3 Omit State 3: States 1+2 (Test secondary propagation necessity)",
            "config_template": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": synthesized_donors["c3_omit_s3"],
            "error_target": 3.0,
            "max_h": 2.0,
            "min_h": 0.080,
            "l0": 0.285,
            "segments": [((30.0, 60.0), (50.0, 60.0)), ((50.0, 60.0), (65.0, 60.0))],
            "omitted_state": "State 3 (Secondary Propagation)"
        }
    ]
    
    results = {}
    t0_all = time.time()
    
    for item in investigation_matrix:
        exp_id = item["id"]
        cid = item["case_id"]
        desc = item["desc"]
        cfg_template = item["config_template"]
        donor_p = item["donor_path"]
        eta_r = item["error_target"]
        max_h = item["max_h"]
        min_h = item["min_h"]
        l0 = item["l0"]
        segments = item["segments"]
        omitted_s = item["omitted_state"]
        
        print("\n" + "-" * 70)
        print("RUNNING: %s (%s)" % (exp_id, desc))
        print("  Case: %s, eta_R: %.2f%%, max_h: %.4f mm, min_h: %.4f mm" % (cid, eta_r, max_h, min_h))
        print("  Donor: %s (SHA: %s)" % (os.path.basename(donor_p), compute_sha256(donor_p)[:16]))
        print("-" * 70)
        
        exp_dir = os.path.join(STEP3_BASE_DIR, exp_id)
        if not os.path.exists(exp_dir):
            os.makedirs(exp_dir)
            
        with open(cfg_template, "r") as f_cfg:
            cfg_dict = json.load(f_cfg)
            
        cfg_dict["remeshing_rule"]["error_target"] = eta_r
        cfg_dict["remeshing_rule"]["max_element_size_mm"] = max_h
        cfg_dict["remeshing_rule"]["min_element_size_mm"] = min_h
        cfg_dict["indicator_options"]["donor_path"] = donor_p
        if "max_frame_index" in item:
            cfg_dict["max_frame_index"] = item["max_frame_index"]
            cfg_dict["indicator_options"]["max_frame_index"] = item["max_frame_index"]
        cfg_dict["deck_options"]["output_directory"] = exp_dir
        
        cfg = AdaptiveConfig(cfg_dict)
        cfg.error_target = eta_r
        cfg.max_h = max_h
        adapter = get_geometry_adapter(cfg)
        
        job_name = "PK_F1823_DONOR_" + exp_id.upper()
        unique_model_name = "Model_F1823_D_" + exp_id
        
        t0 = time.time()
        phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
            cfg, donor_p, exp_dir, model_name=unique_model_name, output_job_name=job_name + "_PHYS"
        )
        elapsed = time.time() - t0
        
        # Finite element quality audit
        mesh_audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=l0, adapter=adapter)
        total_el, quads, tris = count_mesh_elements(phys_inp)
        quad_fraction = float(quads) / total_el if total_el > 0 else 0.0
        body_sha = compute_body_sha256(phys_inp)
        file_sha = compute_sha256(phys_inp)
        
        # Scientific gate audit
        gate_res = audit_case_gates(cid, phys_inp)
        
        # Width metrics
        width_res = compute_width_metrics(phys_inp, l0, segments)
        
        coarsening_ratio = mesh_audit.get("refinement_ratio_far_to_core", 1.0)
        gate_06_pass = coarsening_ratio >= 2.0
        
        print("  -> Completed in %.1fs: %d elements (%d quads, %d tris)" % (
            elapsed, total_el, quads, tris))
        print("  -> Quad fraction: %.2f%%, min det(J): %.2e, max AR: %.2f" % (
            quad_fraction * 100.0, mesh_audit["min_det_j"], mesh_audit["max_aspect_ratio"]))
        print("  -> Coarsening ratio: %.2fx (Gate 06: %s)" % (
            coarsening_ratio, "PASS" if gate_06_pass else "FAIL"))
        print("  -> %s: %.2f%% (%s, threshold: %s)" % (
            gate_res["gate"], gate_res["val"], "PASS" if gate_res["pass"] else "FAIL", gate_res["threshold"]))
        if "extra_gate" in gate_res:
            print("  -> %s: %.2f%%" % (gate_res["extra_gate"], gate_res["extra_val"]))
        print("  -> Width metrics: %d fine elems, within-3*l0: %d (%.2f%%)" % (
            width_res["n_fine"], width_res["n_3l0"], width_res["f_3l0"]))
        print("  -> Body SHA: %s" % body_sha)
        
        results[exp_id] = {
            "case_id": cid,
            "desc": desc,
            "omitted_state": omitted_s,
            "error_target": eta_r,
            "max_h_mm": max_h,
            "min_h_mm": min_h,
            "l0_mm": l0,
            "elements": total_el,
            "quads": quads,
            "tris": tris,
            "quad_fraction": quad_fraction,
            "min_det_j": mesh_audit["min_det_j"],
            "max_ar": mesh_audit["max_aspect_ratio"],
            "coarsening_ratio": coarsening_ratio,
            "gate_06_pass": gate_06_pass,
            "scientific_gate": gate_res,
            "width_metrics": width_res,
            "phys_inp": os.path.relpath(phys_inp, REPO_ROOT).replace("\\", "/"),
            "body_sha256": body_sha,
            "file_sha256": file_sha,
            "donor_path": os.path.relpath(donor_p, REPO_ROOT).replace("\\", "/"),
            "donor_sha256": compute_sha256(donor_p),
            "runtime_s": elapsed
        }

    total_time = time.time() - t0_all
    out_summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_runtime_s": total_time,
        "investigations": results
    }
    
    summary_path = os.path.join(STEP3_BASE_DIR, "step3_targeted_donors_summary.json")
    with open(summary_path, "w") as f_sum:
        json.dump(out_summary, f_sum, indent=2)
        
    print("\n" + "=" * 80)
    print("ALL 10 STEP 3 TARGETED DONOR CONFIGURATIONS COMPLETE (Total: %.1fs)" % total_time)
    print("Summary JSON saved: %s" % summary_path)
    print("=" * 80)

if __name__ == "__main__":
    run_targeted_investigation()
