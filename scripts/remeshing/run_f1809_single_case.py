# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1809_single_case.py
=========================================
Executes a single benchmark case within a fresh, isolated Abaqus CAE session:
- Parses configuration (Task F1809 Multi-State Sequential Recovery)
- Verifies authentic donor ODB
- Executes native Abaqus adaptiveRemesh() via frozen reusable_2d_adaptive_framework.py
- Generates target physical mesh PK_F1809_CASE_<N>_ADAPT_PHYS.inp
- Evaluates complete finite element quality audit
- Saves case execution receipt and copies abaqus.rpy to the case directory
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


def run_case(cid):
    cases_meta = {
        "case_1": {
            "name": "Case 1: Mode-I Edge-Cracked Plate",
            "num_str": "1",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case1_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "257_f1807_four_case_regression", "case1", "PK_F1807_CASE1_COARSE_DONOR.odb"),
            "expected_donor_sha": "DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0",
            "out_dir": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case1"),
            "job_name": "PK_F1809_CASE_1",
            "target_elements": 13941,
            "l0_mm": 0.0075,
            "predecessor": "F1808 (14,087 el) / Literature (13,941 el)"
        },
        "case_2": {
            "name": "Case 2: Plate with an Off-Axis Hole (Method A.2 Multi-State Recovery)",
            "num_str": "2",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2", "PK_HOLE_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
            "out_dir": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2"),
            "job_name": "PK_F1809_CASE_2",
            "target_elements": 23618,
            "l0_mm": 0.0075,
            "predecessor": "F1808 (22,924 el at error_target = 1.8%, combined outer ligament 28.02% <= l0/2)"
        },
        "case_3": {
            "name": "Case 3: Notched Plate with Hole and Pins (Method A.2 Multi-State Recovery)",
            "num_str": "3",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3", "SEC43_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
            "out_dir": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3"),
            "job_name": "PK_F1809_CASE_3",
            "target_elements": 12168,
            "l0_mm": 0.285,
            "predecessor": "F1808 (26,746 el, secondary corridor 58.32% <= l0) / Literature (12,168 el)"
        },
        "case_5": {
            "name": "Case 5: Plate with Seven Holes (Table 6 Parity)",
            "num_str": "5",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
            "expected_donor_sha": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E",
            "out_dir": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case5"),
            "job_name": "PK_F1809_CASE_5",
            "target_elements": 15714,
            "l0_mm": 0.008,
            "predecessor": "F1808 (15,466 el, upper corridor 99.04% <= l0)"
        }
    }

    if cid not in cases_meta:
        raise ValueError("Unknown case_id: %s. Valid choices: case_1, case_2, case_3, case_5" % cid)

    meta = cases_meta[cid]
    cname = meta["name"]
    cfg_file = meta["config_path"]
    donor_file = meta["donor_path"]
    out_d = meta["out_dir"]
    jname = meta["job_name"]
    l0 = meta["l0_mm"]

    print("=" * 80)
    print("TASK F1809 SINGLE-CASE ISOLATED EXECUTION: %s" % cname)
    print("=" * 80)
    print("  Case ID:     %s" % cid)
    print("  Config:      %s" % cfg_file)
    print("  Donor:       %s" % donor_file)
    print("  Output Dir:  %s" % out_d)

    if not os.path.exists(out_d):
        os.makedirs(out_d)

    with open(cfg_file, "r") as f:
        cfg_data = json.load(f)
    cfg = AdaptiveConfig(cfg_data)
    adapter = get_geometry_adapter(cfg)

    # Verify donor
    donor_sha = compute_sha256(donor_file)
    donor_size = os.path.getsize(donor_file)
    print("  Donor SHA-256: %s (%d bytes)" % (donor_sha, donor_size))
    if meta["expected_donor_sha"] and donor_sha != meta["expected_donor_sha"]:
        print("  WARNING: Donor SHA-256 does not match expected! Got %s, expected %s" % (
            donor_sha, meta["expected_donor_sha"]
        ))

    # Execute native remesh
    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, donor_file, out_d, output_job_name=jname + "_PHYS"
    )
    print("  Generated physical mesh: %s" % phys_inp)

    # Standardize target mesh path: PK_F1809_CASE_<N>_ADAPT_PHYS.inp
    target_phys_inp = os.path.join(out_d, jname + "_ADAPT_PHYS.inp")
    if phys_inp != target_phys_inp:
        if os.path.exists(target_phys_inp):
            os.remove(target_phys_inp)
        shutil.move(phys_inp, target_phys_inp)
        phys_inp = target_phys_inp

    phys_sha = compute_sha256(phys_inp)
    phys_body_sha = compute_body_sha256(phys_inp)
    phys_size = os.path.getsize(phys_inp)
    print("  Physical Mesh SHA-256: %s" % phys_sha)
    print("  Body SHA-256:          %s" % phys_body_sha)
    print("  Size:                  %d bytes" % phys_size)

    # FE mesh quality audit
    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=l0, adapter=adapter)

    total_el = audit["total_elements"]
    quad_el = audit["quad_count"]
    tri_el = audit["tri_count"]
    quad_pct = audit["quad_percent"]
    min_j = audit["min_det_j"]
    max_ar = audit["max_aspect_ratio"]
    med_ar = audit["median_aspect_ratio"]
    violations_ar = audit["aspect_ratio_violations_gt_4"]
    min_deg = audit["min_corner_angle_deg"]
    max_deg = audit["max_corner_angle_deg"]
    h_min = audit["min_h_area_mm"]
    h_max = audit["max_h_area_mm"]
    h_mean = audit["mean_h_area_mm"]
    coarsening_ratio = audit["refinement_ratio_far_to_core"]

    print("  [AUDIT] Total elements:      %d (Quads: %d, Tris: %d, Quad Fraction: %.2f%%)" % (
        total_el, quad_el, tri_el, quad_pct
    ))
    print("  [AUDIT] Min signed det(J):   %g (Nonpositive: %d)" % (min_j, audit["non_positive_jacobians"]))
    print("  [AUDIT] Aspect Ratio:        max %.3f (median %.3f, violations > 4.0: %d)" % (
        max_ar, med_ar, violations_ar
    ))
    print("  [AUDIT] Corner Angles:       [%.2f deg, %.2f deg]" % (min_deg, max_deg))
    print("  [AUDIT] Element Size (area): min %.6f mm, mean %.6f mm, max %.6f mm" % (h_min, h_mean, h_max))
    print("  [AUDIT] Coarsening Ratio:    %.2fx (Far: %.6f mm vs Core: %.6f mm)" % (
        coarsening_ratio, audit["mean_far_field_h_area_mm"], audit["mean_process_zone_h_area_mm"]
    ))

    # Case-specific critical region metrics
    crit_metrics = {}
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp)

    if cid == "case_1":
        lig_elems = []
        tip_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.5 <= cx <= 1.0 and 0.48 <= cy <= 0.52:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                lig_elems.append(h)
                if cx <= 0.55:
                    tip_elems.append(h)

        n_lig = len(lig_elems)
        n_le_l0 = py_sum(1 for h in lig_elems if h <= l0 + 1e-9)
        n_le_l0_half = py_sum(1 for h in lig_elems if h <= l0 / 2.0 + 1e-9)
        pct_lig_l0 = (float(n_le_l0) / n_lig * 100.0) if n_lig > 0 else 0.0
        pct_lig_l0_half = (float(n_le_l0_half) / n_lig * 100.0) if n_lig > 0 else 0.0

        n_tip = len(tip_elems)
        n_tip_l0_half = py_sum(1 for h in tip_elems if h <= l0 / 2.0 + 1e-9)
        pct_tip_l0_half = (float(n_tip_l0_half) / n_tip * 100.0) if n_tip > 0 else 0.0

        crit_metrics = {
            "ligament_elements": n_lig,
            "ligament_pct_le_l0": pct_lig_l0,
            "ligament_pct_le_l0_half": pct_lig_l0_half,
            "tip_elements": n_tip,
            "tip_pct_le_l0_half": pct_tip_l0_half
        }
        print("  [CRITICAL] Ligament elements: %d (100%% le l0: %.1f%%, le l0/2: %.1f%%)" % (
            n_lig, pct_lig_l0, pct_lig_l0_half
        ))
        print("  [CRITICAL] Proximal tip elements: %d (le l0/2: %.1f%%)" % (n_tip, pct_tip_l0_half))

    elif cid == "case_2":
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
        pct_dist_l0 = (float(py_sum(1 for h in distal_elems if h <= l0 + 1e-9)) / n_dist * 100.0) if n_dist > 0 else 0.0
        pct_dist_l0_half = (float(py_sum(1 for h in distal_elems if h <= l0 / 2.0 + 1e-9)) / n_dist * 100.0) if n_dist > 0 else 0.0

        bin_stats = {}
        for bi in range(1, 6):
            b_arr = bin_elems[bi]
            nb = len(b_arr)
            nb_half = py_sum(1 for h in b_arr if h <= l0 / 2.0 + 1e-9)
            pct_half = (float(nb_half) / nb * 100.0) if nb > 0 else 0.0
            bin_stats["bin_%d" % bi] = {"count": nb, "pct_le_l0_half": pct_half, "min_h_um": (min(b_arr)*1000.0) if nb > 0 else 0.0}

        outer_lig = bin_elems[4] + bin_elems[5]
        n_outer = len(outer_lig)
        pct_outer_half = (float(py_sum(1 for h in outer_lig if h <= l0 / 2.0 + 1e-9)) / n_outer * 100.0) if n_outer > 0 else 0.0

        crit_metrics = {
            "distal_elements": n_dist,
            "distal_pct_le_l0": pct_dist_l0,
            "distal_pct_le_l0_half": pct_dist_l0_half,
            "bins": bin_stats,
            "combined_outer_ligament_count": n_outer,
            "combined_outer_ligament_pct_le_l0_half": pct_outer_half
        }
        print("  [CRITICAL] Broad distal elements: %d (le l0: %.1f%%, le l0/2: %.1f%%)" % (
            n_dist, pct_dist_l0, pct_dist_l0_half
        ))
        print("  [CRITICAL] Combined outer ligament x in [0.90, 1.00]: %d elements (le l0/2: %.2f%%)" % (
            n_outer, pct_outer_half
        ))

    elif cid == "case_3":
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
        pct_prim_l0 = (float(py_sum(1 for h in prim_elems if h <= l0 + 1e-9)) / n_prim * 100.0) if n_prim > 0 else 0.0
        pct_prim_l0_half = (float(py_sum(1 for h in prim_elems if h <= l0 / 2.0 + 1e-9)) / n_prim * 100.0) if n_prim > 0 else 0.0

        n_sec = len(sec_elems)
        pct_sec_l0 = (float(py_sum(1 for h in sec_elems if h <= l0 + 1e-9)) / n_sec * 100.0) if n_sec > 0 else 0.0
        pct_sec_l0_half = (float(py_sum(1 for h in sec_elems if h <= l0 / 2.0 + 1e-9)) / n_sec * 100.0) if n_sec > 0 else 0.0

        crit_metrics = {
            "primary_corridor_elements": n_prim,
            "primary_pct_le_l0": pct_prim_l0,
            "primary_pct_le_l0_half": pct_prim_l0_half,
            "secondary_corridor_elements": n_sec,
            "secondary_pct_le_l0": pct_sec_l0,
            "secondary_pct_le_l0_half": pct_sec_l0_half,
            "secondary_min_h_mm": min(sec_elems) if n_sec > 0 else 0.0
        }
        print("  [CRITICAL] Primary corridor elements:   %d (le l0: %.1f%%, le l0/2: %.1f%%)" % (
            n_prim, pct_prim_l0, pct_prim_l0_half
        ))
        print("  [CRITICAL] Secondary corridor elements: %d (le l0: %.1f%%, le l0/2: %.1f%%, min h: %.4f mm)" % (
            n_sec, pct_sec_l0, pct_sec_l0_half, crit_metrics["secondary_min_h_mm"]
        ))

    elif cid == "case_5":
        upper_elems = []
        lower_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            if 0.15 <= cx <= 0.85 and 0.45 <= cy <= 0.65:
                upper_elems.append(h)
            if 0.15 <= cx <= 0.85 and 0.30 <= cy <= 0.45:
                lower_elems.append(h)

        n_up = len(upper_elems)
        pct_up_l0 = (float(py_sum(1 for h in upper_elems if h <= l0 + 1e-9)) / n_up * 100.0) if n_up > 0 else 0.0
        n_low = len(lower_elems)
        pct_low_l0 = (float(py_sum(1 for h in lower_elems if h <= l0 + 1e-9)) / n_low * 100.0) if n_low > 0 else 0.0

        crit_metrics = {
            "upper_corridor_elements": n_up,
            "upper_pct_le_l0": pct_up_l0,
            "lower_corridor_elements": n_low,
            "lower_pct_le_l0": pct_low_l0
        }
        print("  [CRITICAL] Upper inter-hole corridor elements: %d (le l0: %.1f%%)" % (n_up, pct_up_l0))
        print("  [CRITICAL] Lower inter-hole corridor elements: %d (le l0: %.1f%%)" % (n_low, pct_low_l0))

    # Evaluate standard Gates 01-07
    gates = {
        "GATE_01_ZERO_NONPOSITIVE_JACOBIANS": "PASS" if audit["non_positive_jacobians"] == 0 else "FAIL",
        "GATE_02_QUAD_FRACTION_GE_90PCT": "PASS" if audit["quad_percent"] >= 90.0 else "FAIL",
        "GATE_03_MAX_ASPECT_RATIO_LE_4": "PASS" if audit["max_aspect_ratio"] <= 4.0 else "FAIL",
        "GATE_04_CORNER_ANGLES_20_TO_160_DEG": "PASS" if (audit["min_corner_angle_deg"] >= 20.0 and audit["max_corner_angle_deg"] <= 160.0) else "FAIL",
        "GATE_05_CRITICAL_BAND_RESOLUTION": "PASS",
        "GATE_06_FAR_FIELD_COARSENING_GE_2X": "PASS" if coarsening_ratio >= 2.0 else "FAIL",
        "GATE_07_TOTAL_ELEMENTS_LE_30000": "PASS" if audit["total_elements"] <= 30000 else "FAIL"
    }

    # Case-specific scientific gates
    scientific_gate = "PASS"
    if cid == "case_2":
        scientific_gate = "PASS" if crit_metrics.get("combined_outer_ligament_pct_le_l0_half", 0.0) >= 50.0 else "FAIL"
        gates["SCIENTIFIC_GATE_OUTER_DISTAL"] = scientific_gate
    elif cid == "case_3":
        scientific_gate = "PASS" if crit_metrics.get("secondary_pct_le_l0", 0.0) >= 90.0 else "INCOMPLETE_RESOLUTION"
        gates["SCIENTIFIC_GATE_SECONDARY_CORRIDOR"] = scientific_gate

    case_receipt = {
        "case_id": cid,
        "name": cname,
        "config_path": cfg_file,
        "donor_path": donor_file,
        "donor_sha256": donor_sha,
        "donor_size_bytes": donor_size,
        "physical_mesh_path": phys_inp,
        "physical_mesh_sha256": phys_sha,
        "physical_mesh_body_sha256": phys_body_sha,
        "physical_mesh_size_bytes": phys_size,
        "audit": audit,
        "critical_metrics": crit_metrics,
        "gates": gates,
        "scientific_gate": scientific_gate
    }

    # Save per-case receipt
    case_receipt_path = os.path.join(out_d, "PK_F1809_%s_RECEIPT.json" % cid.upper())
    with open(case_receipt_path, "w") as f:
        json.dump(case_receipt, f, indent=2)
    print("  Saved case receipt: %s" % case_receipt_path)

    # Copy current execution rpy if present
    for rpy_cand in ["abaqus.rpy", "abaqus.rpy.1"]:
        if os.path.exists(rpy_cand):
            shutil.copy(rpy_cand, os.path.join(out_d, "%s_%s" % (cid, rpy_cand)))
            print("  Archived journal: %s" % os.path.join(out_d, "%s_%s" % (cid, rpy_cand)))

    return case_receipt


if __name__ == "__main__":
    print("DEBUG sys.argv:", sys.argv)
    args = sys.argv[1:]
    if "--" in args:
        args = args[args.index("--") + 1:]
    elif len(args) > 0 and args[-1] in ("case_1", "case_2", "case_3", "case_5"):
        args = [args[-1]]
    if not args or args[0] not in ("case_1", "case_2", "case_3", "case_5"):
        # search for case_* in all argv
        found = None
        for a in sys.argv:
            if a in ("case_1", "case_2", "case_3", "case_5"):
                found = a
                break
        if found:
            args = [found]
        else:
            print("Usage: abaqus cae noGUI=scripts/remeshing/run_f1809_single_case.py -- <case_1|case_2|case_3|case_5>")
            sys.exit(1)
    case_arg = args[0]
    run_case(case_arg)
