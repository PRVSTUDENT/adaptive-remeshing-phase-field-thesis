# -*- coding: utf-8 -*-
"""
scripts/remeshing/compile_f1833_receipt_and_summary.py
======================================================
Compiles master receipt PK_F1833_STATE_CONSISTENT_RECEIPT.json and summary JSON
results/validation/f1833_state_consistent_summary.json with direct comparative analysis
against F1812 baselines across all four cases.
"""
import os
import sys
import json
import time
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
BASE_OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    cases = ["case_1", "case_2", "case_3", "case_5"]
    tags = {"case_1": "case1", "case_2": "case2", "case_3": "case3", "case_5": "case5"}
    jobs = {"case_1": "PK_F1833_CASE_1", "case_2": "PK_F1833_CASE_2", "case_3": "PK_F1833_CASE_3", "case_5": "PK_F1833_CASE_5"}

    selected_cases = {}
    total_remesh_time = 0.0
    for cid in cases:
        tag = tags[cid]
        job = jobs[cid]
        rec_path = os.path.join(BASE_OUT_DIR, tag, job + "_RECEIPT.json")
        with open(rec_path, "r") as f:
            rec = json.load(f)
        selected_cases[cid] = rec
        total_remesh_time += rec.get("remeshing_walltime_s", 0.0)

    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    framework_sha = compute_sha256(framework_path)
    frozen_uel_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

    donor_synth_time = 9.82
    total_walltime = total_remesh_time + donor_synth_time

    master_receipt = {
        "task_id": "F1833-STATE-CONSISTENT-NORMALIZATION",
        "title": "Task F1833: Implement State-Consistent Normalization in the Shared Framework Envelope Synthesis",
        "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
        "correlation_id": "HND-F1833-STATE-CONSISTENT-NORMALIZATION-001",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_walltime_s": round(total_walltime, 2),
        "donor_synthesis_walltime_s": round(donor_synth_time, 2),
        "total_remeshing_walltime_s": round(total_remesh_time, 2),
        "frozen_uel_sha256": frozen_uel_sha,
        "shared_framework_sha256": framework_sha,
        "cumulative_pbs_submissions": 35,
        "new_pbs_submissions": 0,
        "master_goal_status": "OPEN",
        "selected_cases": selected_cases
    }

    # Write PK_F1833_STATE_CONSISTENT_RECEIPT.json
    p1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1833_STATE_CONSISTENT_RECEIPT.json")
    with open(p1, "w") as f:
        json.dump(master_receipt, f, indent=2)
    p2 = os.path.join(BASE_OUT_DIR, "PK_F1833_STATE_CONSISTENT_RECEIPT.json")
    with open(p2, "w") as f:
        json.dump(master_receipt, f, indent=2)
    print("Master receipts written.")

    # Build Comparative Summary against F1812 baselines
    f1812_baselines = {
        "case_1": {
            "elements": 25461,
            "quad_fraction_pct": 97.45,
            "min_det_j": 1.48e-7,
            "max_aspect_ratio": 2.76,
            "coarsening_ratio": 2.3867,
            "gate_06": "PASS",
            "critical_gate": "PASS",
            "critical_metric": "100.0% <= l0, 97.19% <= l0/2 (3664 elems)"
        },
        "case_2": {
            "elements": 41438,
            "quad_fraction_pct": 96.53,
            "min_det_j": 1.62e-7,
            "max_aspect_ratio": 2.79,
            "coarsening_ratio": 1.9349,
            "gate_06": "FAIL",
            "critical_gate": "PASS",
            "critical_metric": "100.0% <= l0/2 in outer distal (2056 elems)"
        },
        "case_3": {
            "elements": 77779,
            "quad_fraction_pct": 96.94,
            "min_det_j": 0.000329,
            "max_aspect_ratio": 2.82,
            "coarsening_ratio": 1.4462,
            "gate_06": "FAIL",
            "critical_gate": "PASS",
            "critical_metric": "98.7% <= l0 in secondary corridor"
        },
        "case_5": {
            "elements": 15466,
            "quad_fraction_pct": 97.90,
            "min_det_j": 3.92e-7,
            "max_aspect_ratio": 2.37,
            "coarsening_ratio": 2.1174,
            "gate_06": "PASS",
            "critical_gate": "PASS",
            "critical_metric": "99.04% <= l0 in inter-hole corridor"
        }
    }

    comparison = {}
    for cid in cases:
        b = f1812_baselines[cid]
        rec = selected_cases[cid]
        audit = rec["audit_metrics"]
        band = rec["band_metrics"]
        new_el = audit["total_elements"]
        base_el = b["elements"]
        delta_el = new_el - base_el
        pct_delta = round((delta_el / float(base_el)) * 100.0, 2)

        comparison[cid] = {
            "name": rec["name"],
            "error_target_pct": rec["error_target"],
            "f1812_baseline_elements": base_el,
            "f1833_state_consistent_elements": new_el,
            "element_delta": delta_el,
            "element_delta_pct": pct_delta,
            "quad_fraction_pct": audit["quad_fraction_pct"],
            "max_aspect_ratio": audit["max_aspect_ratio"],
            "min_det_j": audit["min_det_j"],
            "coarsening_ratio": audit["coarsening_ratio"],
            "gate_06_coarsening": rec["gate_summary"]["gate_06_far_field_coarsening"],
            "scientific_gate_status": rec["scientific_gate_status"],
            "corridor_fine_area_mm2": band["corridor_fine_area_mm2"],
            "unnecessary_fine_area_mm2": band["unnecessary_fine_area_mm2"],
            "unnecessary_fine_fraction_pct": band["unnecessary_fine_fraction_pct"],
            "band_width_mm": band.get("band_width_mm", 0.0),
            "physical_inp_path": rec["physical_inp_path"],
            "physical_inp_sha256": rec["physical_inp_sha256"],
            "physical_inp_body_sha256": rec["physical_inp_body_sha256"]
        }

    summary = {
        "task_id": "F1833-STATE-CONSISTENT-NORMALIZATION",
        "title": "Task F1833: State-Consistent Normalization Evaluation Summary",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_uel_sha256": frozen_uel_sha,
        "framework_sha256": framework_sha,
        "donor_synthesis_walltime_s": donor_synth_time,
        "total_remeshing_walltime_s": round(total_remesh_time, 2),
        "total_walltime_s": round(total_walltime, 2),
        "cumulative_pbs_submissions": 35,
        "new_pbs_submissions": 0,
        "master_goal_status": "OPEN",
        "comparison_against_f1812": comparison
    }

    sum_path = os.path.join(REPO_ROOT, "results", "validation", "f1833_state_consistent_summary.json")
    with open(sum_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("Summary JSON written: %s" % sum_path)

if __name__ == "__main__":
    main()
