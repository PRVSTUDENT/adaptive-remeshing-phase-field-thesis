# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1822_control_verification.py
===================================================
Task F1822: MINIMUM_MAXIMUM Control Verification.
Executes the UNIFORM_ERROR 3.0% control on Case 1 using the verified
PK_CASE1_MULTISTATE_RECOVERY.odb donor under the enhanced framework (0578156E...).
Captures and commits the authentic .rpy journal, mesh INP, and receipt.
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil
import time
import subprocess
import glob

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

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "266_f1822_uniform_error_control")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1822_case1_uniform_error_3pct.json")
DONOR_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb")
EXPECTED_DONOR_SHA = "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117"


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


def cleanup_local_rpy():
    for p in glob.glob(os.path.join(REPO_ROOT, "abaqus.rpy*")):
        try:
            os.remove(p)
        except Exception:
            pass


def capture_rpy_journal(target_file):
    rpy_files = glob.glob(os.path.join(REPO_ROOT, "abaqus.rpy*"))
    if not rpy_files:
        raise RuntimeError("FAIL_CLOSED: No abaqus.rpy journal generated!")
    rpy_files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    freshest = rpy_files[0]
    shutil.copyfile(freshest, target_file)
    with open(target_file, "r") as f:
        content = f.read()
    if "UNIFORM_ERROR" not in content:
        raise RuntimeError("FAIL_CLOSED: Journal %s does not contain 'UNIFORM_ERROR'!" % target_file)
    print("  Captured authentic journal: %s (%d bytes)" % (os.path.basename(target_file), os.path.getsize(target_file)))
    return target_file


def run_control_in_cae():
    """Inner worker executed inside Abaqus CAE noGUI."""
    print("\n" + "=" * 80)
    print("TASK F1822: UNIFORM_ERROR 3.0% CONTROL VERIFICATION FOR CASE 1")
    print("  Executing RemeshingRule with sizingMethod=UNIFORM_ERROR, errorTarget=3.0%")
    print("  Donor: %s" % DONOR_PATH)
    print("  Output dir: %s" % OUT_DIR)
    print("=" * 80)

    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    actual_donor_sha = compute_sha256(DONOR_PATH)
    if actual_donor_sha != EXPECTED_DONOR_SHA:
        raise RuntimeError("Donor hash mismatch! Expected: %s, Actual: %s" % (EXPECTED_DONOR_SHA, actual_donor_sha))

    with open(CONFIG_PATH, "r") as f:
        cfg_data = json.load(f)

    cfg = AdaptiveConfig(cfg_data)
    adapter = get_geometry_adapter(cfg)

    job_name = "PK_F1822_CASE1_UE3_CONTROL"
    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, DONOR_PATH, OUT_DIR, output_job_name=job_name + "_PHYS"
    )

    target_phys_inp = os.path.join(OUT_DIR, job_name + "_PHYS.inp")
    if phys_inp != target_phys_inp:
        if os.path.exists(target_phys_inp):
            os.remove(target_phys_inp)
        shutil.copyfile(phys_inp, target_phys_inp)
        phys_inp = target_phys_inp

    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=0.0075, adapter=adapter)
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
    total_nodes = audit["total_nodes"]
    nominal_field_dofs = total_nodes * 3

    # Full ligament coverage
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp)
    lig_elems = []
    for eid, conn in list(quads.items()) + list(tris.items()):
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(p[0] for p in pts) / len(pts)
        cy = py_sum(p[1] for p in pts) / len(pts)
        if 0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52:
            n = len(pts)
            area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
            h = math.sqrt(area)
            lig_elems.append(h)
    n_lig = len(lig_elems)
    n_lig_half = py_sum(1 for h in lig_elems if h <= 0.0075 / 2.0 + 1e-9)
    scientific_gate_val = (float(n_lig_half) / n_lig * 100.0) if n_lig > 0 else 0.0
    scientific_gate_status = "PASS" if scientific_gate_val >= 95.0 else "FAIL"

    # Width metrics
    segments = [((0.5, 0.5), (1.0, 0.5))]
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

    fine_elements = []
    for eid, conn in list(quads.items()) + list(tris.items()):
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(p[0] for p in pts) / len(pts)
        cy = py_sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
        h = math.sqrt(area)
        if h <= 0.0075 / 2.0 + 1e-9:
            d = min(point_to_segment_dist(cx, cy, s[0][0], s[0][1], s[1][0], s[1][1]) for s in segments)
            fine_elements.append((cx, cy, h, d))

    n_fine = len(fine_elements)
    n_3l0 = py_sum(1 for e in fine_elements if e[3] <= 3.0 * 0.0075 + 1e-9)
    f_3l0 = (float(n_3l0) / n_fine * 100.0) if n_fine > 0 else 0.0

    res = {
        "case_id": "case_1",
        "name": "Case 1: Mode-I Edge-Cracked Plate (UNIFORM_ERROR 3.0% Control)",
        "sizing_method": "UNIFORM_ERROR",
        "error_target_pct": 3.0,
        "physical_mesh_path": to_repo_rel(phys_inp),
        "physical_mesh_sha256": phys_sha,
        "physical_mesh_body_sha256": phys_body_sha,
        "physical_mesh_size_bytes": phys_size,
        "total_elements": total_el,
        "quad_elements": quad_el,
        "tri_elements": tri_el,
        "quad_fraction_pct": quad_pct,
        "total_nodes": total_nodes,
        "nominal_field_dofs": nominal_field_dofs,
        "min_det_j": min_j,
        "max_aspect_ratio": max_ar,
        "min_corner_angle_deg": audit["min_corner_angle_deg"],
        "max_corner_angle_deg": audit["max_corner_angle_deg"],
        "coarsening_ratio": coarsening_ratio,
        "scientific_gate_name": "SCIENTIFIC_GATE_FULL_LIGAMENT",
        "scientific_gate_value": scientific_gate_val,
        "scientific_gate_status": scientific_gate_status,
        "width_metrics": {
            "fine_elements_count": n_fine,
            "fine_elements_pct_of_total": (100.0 * n_fine / total_el) if total_el > 0 else 0.0,
            "within_3l0_count": n_3l0,
            "pct_within_3l0": f_3l0
        }
    }

    print("  CONTROL RESULTS: Total Elements = %d (Quads: %d = %.2f%%, Tris: %d)" % (
        total_el, quad_el, quad_pct, tri_el
    ))
    print("  Body SHA-256: %s" % phys_body_sha)
    print("  Min det(J): %.2e, Max AR: %.2f" % (min_j, max_ar))
    print("  Coarsening Ratio: %.2fx" % coarsening_ratio)
    print("  Full Ligament Gate: %.2f%% (%s)" % (scientific_gate_val, scientific_gate_status))

    receipt_path = os.path.join(OUT_DIR, "f1822_control_receipt.json")
    with open(receipt_path, "w") as f:
        json.dump(res, f, indent=2)

    return res


def main():
    print("=" * 80)
    print("TASK F1822: LAUNCHING ABAQUS CAE FOR UNIFORM_ERROR 3.0% CONTROL")
    print("=" * 80)

    cleanup_local_rpy()
    abaqus_bat = r"C:\SIMULIA\Commands\abaqus.bat"

    cmd = [
        abaqus_bat, "cae",
        "noGUI=%s" % os.path.abspath(__file__),
        "--", "RUN_CAE"
    ]

    t0 = time.time()
    ret = subprocess.call(cmd, cwd=REPO_ROOT)
    dt = time.time() - t0

    if ret != 0:
        print("ERROR: Abaqus CAE failed with exit code %d" % ret)
        sys.exit(ret)

    journal_dest = os.path.join(OUT_DIR, "case_1_ue3_control_abaqus.rpy")
    capture_rpy_journal(journal_dest)
    journal_sha = compute_sha256(journal_dest)

    receipt_file = os.path.join(OUT_DIR, "f1822_control_receipt.json")
    with open(receipt_file, "r") as f:
        cdata = json.load(f)
    cdata["execution_time_seconds"] = dt

    master_receipt = {
        "receipt_version": "1.0",
        "task_id": "F1822-MINIMUM-MAXIMUM-CONTROL-VERIFICATION",
        "correlation_id": "HND-F1822-MINMAX-CONTROL-VERIFICATION-001",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "control_experiment": {
            "case_id": "case_1",
            "benchmark_name": "Case 1: Mode-I Edge-Cracked Plate",
            "sizing_method": "UNIFORM_ERROR",
            "error_target_pct": 3.0,
            "min_element_size_mm": 0.001,
            "max_element_size_mm": 0.020,
            "refinement_factor": 10,
            "coarsening_factor": "DEFAULT_LIMIT",
            "donor_odb_path": to_repo_rel(DONOR_PATH),
            "donor_odb_sha256": EXPECTED_DONOR_SHA,
            "config_path": to_repo_rel(CONFIG_PATH),
            "config_sha256": compute_sha256(CONFIG_PATH),
            "framework_sha256": compute_sha256(os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py"))
        },
        "results": cdata,
        "journal": {
            "journal_path": to_repo_rel(journal_dest),
            "journal_size_bytes": os.path.getsize(journal_dest),
            "journal_sha256": journal_sha
        },
        "comparison_against_minmax": {
            "uniform_error_3pct": {
                "total_elements": cdata["total_elements"],
                "body_sha256": cdata["physical_mesh_body_sha256"]
            },
            "minimum_maximum_bias7": {
                "total_elements": 63210,
                "body_sha256": "B15F948C820F7A773D61D62651638800ED525ABC3E538412A383E8E36AD6DB9E"
            },
            "shas_match": (cdata["physical_mesh_body_sha256"] == "B15F948C820F7A773D61D62651638800ED525ABC3E538412A383E8E36AD6DB9E"),
            "element_delta": 63210 - cdata["total_elements"]
        }
    }

    master_receipt_path = os.path.join(OUT_DIR, "PK_F1822_CONTROL_VERIFICATION_RECEIPT.json")
    with open(master_receipt_path, "w") as f:
        json.dump(master_receipt, f, indent=2)

    print("\n" + "=" * 80)
    print("TASK F1822 CONTROL VERIFICATION COMPLETE")
    print("  Control Mesh: %s" % cdata["physical_mesh_path"])
    print("  Total Elements: %d" % cdata["total_elements"])
    print("  Body SHA-256:   %s" % cdata["physical_mesh_body_sha256"])
    print("  Comparison vs MINIMUM_MAXIMUM (63,210 el, B15F948C...):")
    print("    Delta = %+d elements" % (63210 - cdata["total_elements"]))
    print("    Body SHAs Match = %s" % master_receipt["comparison_against_minmax"]["shas_match"])
    print("  Receipt: %s" % master_receipt_path)
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[-1] == "RUN_CAE":
        run_control_in_cae()
    else:
        main()
