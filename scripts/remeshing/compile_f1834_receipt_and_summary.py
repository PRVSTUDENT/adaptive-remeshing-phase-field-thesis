# -*- coding: utf-8 -*-
"""
scripts/remeshing/compile_f1834_receipt_and_summary.py
======================================================
Task F1834: Compiles master receipt PK_F1834_BLOWUP_GUARD_RECEIPT.json and summary JSON
results/validation/f1834_blowup_guard_summary.json with direct comparative analysis
against F1812 and F1833 baselines across all tested load-threshold ratios.
"""
import os
import sys
import json
import time
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
F1834_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "274_f1834_blowup_guard")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main(selected_tag="thresh_050"):
    sweep_summary_path = os.path.join(F1834_BASE, "threshold_sweep_summary.json")
    if not os.path.exists(sweep_summary_path):
        raise RuntimeError("Missing threshold_sweep_summary.json at %s" % sweep_summary_path)

    with open(sweep_summary_path, "r") as f:
        sweep_data = json.load(f)

    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    framework_sha = compute_sha256(framework_path)
    frozen_uel_sha = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

    # Load receipts for the selected candidate tag
    cases = ["case_1", "case_2", "case_3", "case_5"]
    tags = {"case_1": "case1", "case_2": "case2", "case_3": "case3", "case_5": "case5"}
    jobs = {
        "case_1": f"PK_F1834_C1_{selected_tag.upper()}",
        "case_2": f"PK_F1834_C2_{selected_tag.upper()}",
        "case_3": f"PK_F1834_C3_{selected_tag.upper()}",
        "case_5": f"PK_F1834_C5_{selected_tag.upper()}"
    }

    selected_cases = {}
    total_remesh_time = 0.0
    for cid in cases:
        tag = tags[cid]
        job = jobs[cid]
        rec_path = os.path.join(F1834_BASE, selected_tag, tag, job + "_RECEIPT.json")
        with open(rec_path, "r") as f:
            rec = json.load(f)
        selected_cases[cid] = rec
        total_remesh_time += rec.get("remeshing_walltime_s", 0.0)

    donor_synth_time = 8.77
    total_walltime = total_remesh_time + donor_synth_time

    master_receipt = {
        "task_id": "F1834-EARLY-STATE-BLOWUP-GUARD",
        "title": "Task F1834: Diagnose the Early-State Eta Blowup and Test a Load-Threshold Guard",
        "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
        "correlation_id": "HND-F1834-EARLY-STATE-BLOWUP-GUARD-001",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "selected_candidate_tag": selected_tag,
        "total_walltime_s": round(total_walltime, 2),
        "donor_synthesis_walltime_s": round(donor_synth_time, 2),
        "total_remeshing_walltime_s": round(total_remesh_time, 2),
        "frozen_uel_sha256": frozen_uel_sha,
        "shared_framework_sha256": framework_sha,
        "cumulative_pbs_submissions": 35,
        "new_pbs_submissions": 0,
        "master_goal_status": "OPEN",
        "sweep_summary": sweep_data,
        "selected_cases": selected_cases
    }

    p1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1834_BLOWUP_GUARD_RECEIPT.json")
    with open(p1, "w") as f:
        json.dump(master_receipt, f, indent=2)
    p2 = os.path.join(F1834_BASE, "PK_F1834_BLOWUP_GUARD_RECEIPT.json")
    with open(p2, "w") as f:
        json.dump(master_receipt, f, indent=2)
    print("Master receipts written to %s and %s" % (p1, p2))

    # Baselines for comparison
    f1812_baselines = {
        "case_1": {"elements": 25461, "quad_pct": 97.45, "coarsening": 2.3867, "gate_06": "PASS", "gate_07": "PASS", "crit_gate": "PASS"},
        "case_2": {"elements": 41438, "quad_pct": 96.53, "coarsening": 1.9349, "gate_06": "FAIL", "gate_07": "PASS", "crit_gate": "PASS"},
        "case_3": {"elements": 77779, "quad_pct": 95.89, "coarsening": 1.4879, "gate_06": "FAIL", "gate_07": "PASS", "crit_gate": "PASS"},
        "case_5": {"elements": 15466, "quad_pct": 99.41, "coarsening": 2.2134, "gate_06": "PASS", "gate_07": "PASS", "crit_gate": "PASS"}
    }
    f1833_baselines = {
        "case_1": {"elements": 9234, "quad_pct": 97.14, "coarsening": 2.4550, "gate_06": "PASS", "gate_07": "PASS", "crit_gate": "FAIL"},
        "case_2": {"elements": 117181, "quad_pct": 97.22, "coarsening": 1.4070, "gate_06": "FAIL", "gate_07": "FAIL", "crit_gate": "PASS"},
        "case_3": {"elements": 130218, "quad_pct": 95.27, "coarsening": 1.4830, "gate_06": "FAIL", "gate_07": "FAIL", "crit_gate": "PASS"},
        "case_5": {"elements": 15466, "quad_pct": 99.41, "coarsening": 2.2134, "gate_06": "PASS", "gate_07": "PASS", "crit_gate": "PASS"}
    }

    summary_obj = {
        "task_id": "F1834-EARLY-STATE-BLOWUP-GUARD",
        "title": "Task F1834: Diagnose Early-State Eta Blowup and Test Load-Threshold Guard",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "frozen_uel_sha256": frozen_uel_sha,
        "shared_framework_sha256": framework_sha,
        "selected_candidate_tag": selected_tag,
        "sweep_summary": sweep_data,
        "f1812_baselines": f1812_baselines,
        "f1833_baselines": f1833_baselines,
        "selected_results": {}
    }

    for cid in cases:
        r = selected_cases[cid]
        m = r["audit_metrics"]
        b = r["band_metrics"]
        g = r["gate_summary"]
        el = m["total_elements"]
        base_1812_el = f1812_baselines[cid]["elements"]
        base_1833_el = f1833_baselines[cid]["elements"]
        summary_obj["selected_results"][cid] = {
            "name": r["name"],
            "elements": el,
            "delta_vs_f1812_pct": round((el - base_1812_el) / float(base_1812_el) * 100.0, 2),
            "delta_vs_f1833_pct": round((el - base_1833_el) / float(base_1833_el) * 100.0, 2),
            "quad_fraction_pct": m["quad_fraction_pct"],
            "min_det_j": m["min_det_j"],
            "max_aspect_ratio": m["max_aspect_ratio"],
            "coarsening_ratio": m["coarsening_ratio"],
            "gate_06": g["gate_06_far_field_coarsening"],
            "gate_07": g["gate_07_element_budget"],
            "scientific_gate": r["scientific_gate_status"],
            "corridor_fine_area_mm2": b.get("corridor_fine_area_mm2", 0.0),
            "unnecessary_fine_area_mm2": b.get("unnecessary_fine_area_mm2", 0.0),
            "unnecessary_fine_pct": b.get("unnecessary_fine_fraction_pct", 0.0),
            "band_width_mm": b.get("band_width_mm", 0.0),
            "critical_metrics": r["critical_metrics"]
        }

    sum_out = os.path.join(REPO_ROOT, "results", "validation", "f1834_blowup_guard_summary.json")
    with open(sum_out, "w") as f:
        json.dump(summary_obj, f, indent=2)
    print("Summary JSON written to: %s" % sum_out)

if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "thresh_050"
    main(tag)
