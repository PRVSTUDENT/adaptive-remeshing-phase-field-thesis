# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1812_single_target.py
============================================
Task F1812: Universal Framework Crack-Path Refinement Runner.
Executes a single benchmark case at a specified error target within a fresh,
isolated Abaqus CAE session:
- Loads benchmark configuration
- Overrides error_target to the specified value
- Executes native Abaqus adaptiveRemesh() via frozen reusable_2d_adaptive_framework.py
- Generates target physical mesh .inp
- Performs complete finite element quality audit
- Computes case-specific critical metrics (full ligament bins, outer ligament, dual corridors)
- Writes audit receipt JSON using repo-relative paths
- Copies replay journal abaqus.rpy
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
        },
        "case_2": {
            "name": "Case 2: Plate with an Off-Axis Hole (Method A.2 Multi-State Recovery)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2", "PK_HOLE_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
            "l0_mm": 0.0075,
        },
        "case_3": {
            "name": "Case 3: Notched Plate with Hole and Pins (Method A.2 Multi-State Recovery)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3", "SEC43_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
            "l0_mm": 0.285,
        },
        "case_5": {
            "name": "Case 5: Plate with Seven Holes (Table 6 Parity)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
            "expected_donor_sha": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E",
            "l0_mm": 0.0080,
        }
    }

    meta = cases_meta[cid]
    cname = meta["name"]
    cfg_file = meta["config_path"]
    donor_p = meta["donor_path"]
    exp_donor_sha = meta["expected_donor_sha"]
    l0 = meta["l0_mm"]

    print("=" * 80)
    print("RUNNING %s AT ERROR TARGET %.2f%%" % (cname.upper(), error_target))
    print("Output directory: %s" % out_dir)
    print("Job name:         %s" % job_name)
    print("=" * 80)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # Verify donor exists and match SHA
    if not os.path.exists(donor_p):
        raise RuntimeError("Donor file does not exist: %s" % donor_p)
    actual_donor_sha = compute_sha256(donor_p)
    if actual_donor_sha != exp_donor_sha:
        raise RuntimeError("Donor hash mismatch! Expected: %s, Actual: %s" % (exp_donor_sha, actual_donor_sha))
    print("Donor ODB verified: %s (SHA: %s)" % (os.path.basename(donor_p), actual_donor_sha))

    # Load configuration
    with open(cfg_file, "r") as f:
        cfg_data = json.load(f)
    cfg = AdaptiveConfig(cfg_data)
    cfg.error_target = float(error_target)
    adapter = get_geometry_adapter(cfg)

    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, donor_p, out_dir, output_job_name=job_name + "_PHYS"
    )
    print("Generated physical mesh: %s" % phys_inp)

    target_phys_inp = os.path.join(out_dir, job_name + "_ADAPT_PHYS.inp")
    if phys_inp != target_phys_inp:
        if os.path.exists(target_phys_inp):
            os.remove(target_phys_inp)
        shutil.copyfile(phys_inp, target_phys_inp)
        phys_inp = target_phys_inp

    # Audit mesh
    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=l0, adapter=adapter)

    phys_sha = compute_sha256(phys_inp)
    phys_body_sha = compute_body_sha256(phys_inp)
    phys_size = os.path.getsize(phys_inp)

    total_el = audit["total_elements"]
    quad_el = audit["quad_count"]
    tri_el = audit["tri_count"]
    quad_pct = audit["quad_fraction_pct"]
    min_j = audit["min_det_j"]
    max_ar = audit["max_aspect_ratio"]
    coarsening_ratio = audit.get("refinement_ratio_far_to_core", 1.0)

    print("  [AUDIT] Elements: %d (Quads: %d, Tris: %d, Quad %%: %.2f%%)" % (total_el, quad_el, tri_el, quad_pct))
    print("  [AUDIT] Min signed det(J): %g, Max AR: %.3f, Coarsening: %.2fx" % (min_j, max_ar, coarsening_ratio))

    crit_metrics = {}
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp)

    scientific_gate = "UNKNOWN"
    scientific_gate_name = "NONE"

    if cid == "case_1":
        scientific_gate_name = "SCIENTIFIC_GATE_FULL_LIGAMENT"
        lig_elems = []
        outer_elems = []
        bin_elems = {
            "bin_1": [], # 0.50 - 0.55
            "bin_2": [], # 0.55 - 0.60
            "bin_3": [], # 0.60 - 0.70
            "bin_4": [], # 0.70 - 0.80
            "bin_5": [], # 0.80 - 0.90
            "bin_6": []  # 0.90 - 1.00
        }
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                lig_elems.append(h)
                if cx < 0.55:
                    bin_elems["bin_1"].append(h)
                elif cx < 0.60:
                    bin_elems["bin_2"].append(h)
                elif cx < 0.70:
                    bin_elems["bin_3"].append(h)
                elif cx < 0.80:
                    bin_elems["bin_4"].append(h)
                elif cx < 0.90:
                    bin_elems["bin_5"].append(h)
                    outer_elems.append(h)
                else:
                    bin_elems["bin_6"].append(h)
                    outer_elems.append(h)

        n_lig = len(lig_elems)
        pct_lig_l0 = (float(py_sum(1 for h in lig_elems if h <= l0 + 1e-9)) / n_lig * 100.0) if n_lig > 0 else 0.0
        pct_lig_l0_half = (float(py_sum(1 for h in lig_elems if h <= l0 / 2.0 + 1e-9)) / n_lig * 100.0) if n_lig > 0 else 0.0

        n_outer = len(outer_elems)
        pct_outer_l0_half = (float(py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)) / n_outer * 100.0) if n_outer > 0 else 0.0

        bins_audit = {}
        for b_name in sorted(bin_elems.keys()):
            b_list = bin_elems[b_name]
            nb = len(b_list)
            nb_l0 = py_sum(1 for h in b_list if h <= l0 + 1e-9)
            nb_half = py_sum(1 for h in b_list if h <= l0 / 2.0 + 1e-9)
            pct_b_l0 = (float(nb_l0) / nb * 100.0) if nb > 0 else 0.0
            pct_b_half = (float(nb_half) / nb * 100.0) if nb > 0 else 0.0
            min_h_b = min(b_list) * 1000.0 if nb > 0 else 0.0
            bins_audit[b_name] = {
                "count": nb,
                "pct_le_l0": pct_b_l0,
                "pct_le_l0_half": pct_b_half,
                "min_h_um": min_h_b
            }

        scientific_gate = "PASS" if (pct_lig_l0 >= 99.9 and pct_lig_l0_half >= 90.0) else "FAIL"
        crit_metrics = {
            "ligament_elements": n_lig,
            "ligament_pct_le_l0": pct_lig_l0,
            "ligament_pct_le_l0_half": pct_lig_l0_half,
            "outer_ligament_count": n_outer,
            "outer_ligament_pct_le_l0_half": pct_outer_l0_half,
            "bins": bins_audit
        }
        print("  [CRITICAL] Full Ligament: %d, %%<=l0: %.2f%%, %%<=l0/2: %.2f%%, Outer %%<=l0/2: %.2f%% (Gate: %s)" % (
            n_lig, pct_lig_l0, pct_lig_l0_half, pct_outer_l0_half, scientific_gate
        ))

    elif cid == "case_2":
        scientific_gate_name = "SCIENTIFIC_GATE_OUTER_DISTAL"
        distal_elems = []
        bin_elems = {1: [], 2: [], 3: [], 4: [], 5: []}
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                distal_elems.append(h)
                if cx < 0.80:
                    bin_elems[1].append(h)
                elif cx < 0.85:
                    bin_elems[2].append(h)
                elif cx < 0.90:
                    bin_elems[3].append(h)
                elif cx < 0.95:
                    bin_elems[4].append(h)
                else:
                    bin_elems[5].append(h)

        n_dist = len(distal_elems)
        n_dist_l0 = py_sum(1 for h in distal_elems if h <= l0 + 1e-9)
        n_dist_l0_half = py_sum(1 for h in distal_elems if h <= l0 / 2.0 + 1e-9)
        pct_dist_l0 = (float(n_dist_l0) / n_dist * 100.0) if n_dist > 0 else 0.0
        pct_dist_l0_half = (float(n_dist_l0_half) / n_dist * 100.0) if n_dist > 0 else 0.0

        bins_audit = {}
        for b_idx in range(1, 6):
            b_list = bin_elems[b_idx]
            nb = len(b_list)
            nb_half = py_sum(1 for h in b_list if h <= l0 / 2.0 + 1e-9)
            pct_b_half = (float(nb_half) / nb * 100.0) if nb > 0 else 0.0
            min_h_b = min(b_list) * 1000.0 if nb > 0 else 0.0
            bins_audit["bin_%d" % b_idx] = {
                "count": nb,
                "pct_le_l0_half": pct_b_half,
                "min_h_um": min_h_b
            }

        outer_elems = bin_elems[4] + bin_elems[5]
        n_outer = len(outer_elems)
        n_outer_half = py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)
        pct_outer_half = (float(n_outer_half) / n_outer * 100.0) if n_outer > 0 else 0.0

        scientific_gate = "PASS" if pct_outer_half >= 50.0 else "FAIL"

        crit_metrics = {
            "distal_elements": n_dist,
            "distal_pct_le_l0": pct_dist_l0,
            "distal_pct_le_l0_half": pct_dist_l0_half,
            "bins": bins_audit,
            "combined_outer_ligament_count": n_outer,
            "combined_outer_ligament_pct_le_l0_half": pct_outer_half
        }
        print("  [CRITICAL] Outer Ligament Elements: %d, %% <= l0/2: %.2f%% (Gate: %s)" % (
            n_outer, pct_outer_half, scientific_gate
        ))

    elif cid == "case_3":
        scientific_gate_name = "SCIENTIFIC_GATE_SECONDARY_CORRIDOR"
        prim_elems = []
        sec_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            if 10.0 <= cx <= 36.5 and 45.0 <= cy <= 75.0:
                prim_elems.append(h)
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
                sec_elems.append(h)

        n_prim = len(prim_elems)
        n_prim_l0 = py_sum(1 for h in prim_elems if h <= l0 + 1e-9)
        pct_prim_l0 = (float(n_prim_l0) / n_prim * 100.0) if n_prim > 0 else 0.0

        n_sec = len(sec_elems)
        n_sec_l0 = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
        pct_sec_l0 = (float(n_sec_l0) / n_sec * 100.0) if n_sec > 0 else 0.0

        scientific_gate = "PASS" if pct_sec_l0 >= 90.0 else "FAIL"

        crit_metrics = {
            "primary_corridor_elements": n_prim,
            "primary_pct_le_l0": pct_prim_l0,
            "secondary_corridor_elements": n_sec,
            "secondary_pct_le_l0": pct_sec_l0
        }
        print("  [CRITICAL] Secondary Corridor: %d, %% <= l0: %.2f%% (Gate: %s)" % (
            n_sec, pct_sec_l0, scientific_gate
        ))

    elif cid == "case_5":
        scientific_gate_name = "SCIENTIFIC_GATE_INTER_HOLE"
        inter_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.15 <= cx <= 0.85 and 0.45 <= cy <= 0.65:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                inter_elems.append(h)

        n_inter = len(inter_elems)
        n_inter_l0 = py_sum(1 for h in inter_elems if h <= l0 + 1e-9)
        pct_inter_l0 = (float(n_inter_l0) / n_inter * 100.0) if n_inter > 0 else 0.0

        scientific_gate = "PASS" if pct_inter_l0 >= 95.0 else "FAIL"

        crit_metrics = {
            "upper_corridor_elements": n_inter,
            "upper_pct_le_l0": pct_inter_l0
        }
        print("  [CRITICAL] Inter-Hole Corridor: %d, %% <= l0: %.2f%% (Gate: %s)" % (
            n_inter, pct_inter_l0, scientific_gate
        ))

    # Standard gates evaluation
    gate_01 = "PASS" if audit["non_positive_jacobians"] == 0 else "FAIL"
    gate_02 = "PASS" if quad_pct >= 90.0 else "FAIL"
    gate_03 = "PASS" if max_ar <= 4.0 else "FAIL"
    gate_04 = "PASS" if (audit["min_corner_angle_deg"] >= 20.0 and audit["max_corner_angle_deg"] <= 160.0) else "FAIL"
    gate_05 = "PASS" if scientific_gate == "PASS" else "FAIL"
    gate_06 = "PASS" if coarsening_ratio >= 2.0 else "FAIL"
    # Gate 7 element budget: <=30000 for standard cases, or <=80000 for complex multi-hole Case 3
    el_budget = 80000 if cid == "case_3" or cid == "case_2" else 30000
    gate_07 = "PASS" if total_el <= el_budget else "FAIL"

    receipt = {
        "case_id": cid,
        "name": cname,
        "error_target": float(error_target),
        "job_name": job_name,
        "donor_path": to_repo_rel(donor_p),
        "donor_sha256": actual_donor_sha,
        "physical_mesh_path": to_repo_rel(phys_inp),
        "physical_mesh_sha256": phys_sha,
        "physical_mesh_body_sha256": phys_body_sha,
        "physical_mesh_size_bytes": phys_size,
        "audit": audit,
        "critical_metrics": crit_metrics,
        "gates": {
            "GATE_01_ZERO_NONPOSITIVE_JACOBIANS": gate_01,
            "GATE_02_QUAD_FRACTION_GE_90PCT": gate_02,
            "GATE_03_MAX_ASPECT_RATIO_LE_4": gate_03,
            "GATE_04_CORNER_ANGLES_20_TO_160_DEG": gate_04,
            "GATE_05_CRITICAL_BAND_RESOLUTION": gate_05,
            "GATE_06_FAR_FIELD_COARSENING_GE_2X": gate_06,
            "GATE_07_TOTAL_ELEMENTS_BUDGET": gate_07,
            scientific_gate_name: scientific_gate
        },
        "scientific_gate": scientific_gate
    }

    receipt_file = os.path.join(out_dir, job_name + "_RECEIPT.json")
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Receipt written: %s" % to_repo_rel(receipt_file))

    # Copy replay journal if present
    rpy_name = "abaqus.rpy"
    if os.path.exists(rpy_name):
        dest_rpy = os.path.join(out_dir, job_name + "_abaqus.rpy")
        shutil.copyfile(rpy_name, dest_rpy)
        print("Replay journal archived: %s" % to_repo_rel(dest_rpy))


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: abaqus cae noGUI=run_f1812_single_target.py -- <cid> <error_target> <out_dir> <job_name>")
        sys.exit(1)
    c_arg = sys.argv[-4]
    t_arg = float(sys.argv[-3])
    out_arg = sys.argv[-2]
    jname_arg = sys.argv[-1]
    run_target(c_arg, t_arg, out_arg, jname_arg)
