# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1816_receipt.py
===========================================
Compiles the definitive machine-readable receipt for Task F1816:
  models/pandey_kumar_mode1/263_f1816_multistep_narrowing/PK_F1816_MULTISTEP_NARROWING_RECEIPT.json
Uses strict repo-relative paths throughout and computes direct disk SHA-256 hashes.
"""
from __future__ import print_function
import os
import sys
import json
import hashlib
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def sha256_body(filepath):
    h = hashlib.sha256()
    with open(filepath, "r") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()

def to_rel(path):
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace("\\", "/")

def main():
    step1_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step1_minmax", "step1_minmax_summary.json")
    step2_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "step2_envelope_summary.json")
    
    with open(step1_json, "r") as f:
        d1 = json.load(f)
    with open(step2_json, "r") as f:
        d2 = json.load(f)
        
    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    
    fig_png = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.png")
    fig_pdf = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.pdf")
    
    report_path = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")
    
    receipt = {
        "task_id": "F1816-MULTISTEP-REFINEMENT-NARROWING",
        "title": "Task F1816: Multi-Step Refinement Narrowing Across Four Canonical Benchmarks",
        "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
        "correlation_id": "HND-F1816-MULTISTEP-NARROWING-002",
        "predecessor_correlation_id": "HND-F1814-LABEL-CORRECTION-001",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "governing_objectives": {
            "master_goal_status": "OPEN",
            "research_priority": "ADAPTIVE_REMESHING_ONLY",
            "cumulative_pbs_submissions": 35,
            "new_pbs_submissions": 0,
            "frozen_production_uel_sha256": sha256_file(uel_path),
            "shared_framework_sha256": sha256_file(framework_path),
            "predeclared_adoption_rule": "Adopt modified framework ONLY if fine band narrows (>3*l0 concentration) while all 4 scientific gates PASS at F1812 thresholds; otherwise F1812 baselines stand."
        },
        "step1_sizing_method_investigation": {
            "method": "MINIMUM_MAXIMUM",
            "parameters": {
                "eta_max_pct": 1.0,
                "eta_min_pct": 5.0,
                "mesh_bias": 7
            },
            "findings": {
                "total_elements_all_cases": sum(c["total_elements"] for c in d1["cases"].values()),
                "element_count_delta_vs_f1812": "+61.7% (160,144 -> 258,894 elements)",
                "gate_07_budget_status": "FAIL on Cases 1, 3, 5",
                "gate_06_coarsening_status": "FAIL on all cases (1.53x - 1.87x < 2.0x)",
                "band_width_status": "WIDENED/DILUTED on all cases (Case 5 dropped from 29.31% to 9.19% within 3*l0)"
            },
            "decision": "REJECTED (Uniform error baseline retained)"
        },
        "step2_envelope_construction_investigation": {
            "variant_2b_reduced_envelope": {
                "description": "Reduced 2-state maximum error envelope: breach/arrest state + terminal state",
                "cases": d2["variant_2b_reduced"],
                "decision": "REJECTED (Fails scientific gates on Case 1 [91.75% < 95%] and Case 3 [87.61% < 90%]; doubles Case 2 mesh to 83,913 elements; fails to narrow band)"
            },
            "variant_2a_overlapping_rules": {
                "description": "Per-state overlapping native RemeshingRules in Abaqus CAE across distinct steps",
                "cases": d2["variant_2a_overlapping"],
                "decision": "REJECTED (Fails Case 3 secondary corridor gate [86.30% < 90%]; balloons Case 1 to 37,511 elements and Case 2 to 82,869 elements; dilutes band localization)"
            }
        },
        "step3_combine_and_validate_decision": {
            "adopted_framework_configuration": "F1812_BASELINES_ADOPTED_AS_PARETO_OPTIMUM",
            "total_canonical_elements": 160144,
            "scientific_gate_compliance": "100% PASS across Cases 1, 2, 3, 5",
            "physical_mechanism_conclusion": "The refinement width is governed by the boundary value problem stress decay length and cannot be artificially narrowed without losing crack-path coverage."
        },
        "four_benchmark_width_metrics_comparison": {
            "case_1": {
                "f1812_baseline": {"elements": 25461, "pct_within_3l0": 27.61, "gate_val": 97.19, "gate_status": "PASS"},
                "step1_minmax": {"elements": d1["cases"]["case_1"]["total_elements"], "pct_within_3l0": d1["cases"]["case_1"]["width_metrics"]["pct_within_3l0"], "gate_val": d1["cases"]["case_1"]["scientific_gate_value"], "gate_status": "PASS"},
                "step2b_reduced": {"elements": d2["variant_2b_reduced"]["case_1"]["elements"], "pct_within_3l0": d2["variant_2b_reduced"]["case_1"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2b_reduced"]["case_1"]["scientific_gate"]["val"], "gate_status": "FAIL"},
                "step2a_overlap": {"elements": d2["variant_2a_overlapping"]["case_1"]["elements"], "pct_within_3l0": d2["variant_2a_overlapping"]["case_1"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2a_overlapping"]["case_1"]["scientific_gate"]["val"], "gate_status": "PASS"}
            },
            "case_2": {
                "f1812_baseline": {"elements": 41438, "pct_within_3l0": 14.58, "gate_val": 100.00, "gate_status": "PASS"},
                "step1_minmax": {"elements": d1["cases"]["case_2"]["total_elements"], "pct_within_3l0": d1["cases"]["case_2"]["width_metrics"]["pct_within_3l0"], "gate_val": d1["cases"]["case_2"]["scientific_gate_value"], "gate_status": "PASS"},
                "step2b_reduced": {"elements": d2["variant_2b_reduced"]["case_2"]["elements"], "pct_within_3l0": d2["variant_2b_reduced"]["case_2"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2b_reduced"]["case_2"]["scientific_gate"]["val"], "gate_status": "PASS"},
                "step2a_overlap": {"elements": d2["variant_2a_overlapping"]["case_2"]["elements"], "pct_within_3l0": d2["variant_2a_overlapping"]["case_2"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2a_overlapping"]["case_2"]["scientific_gate"]["val"], "gate_status": "PASS"}
            },
            "case_3": {
                "f1812_baseline": {"elements": 77779, "pct_within_3l0": 0.49, "gate_val": 93.84, "gate_status": "PASS"},
                "step1_minmax": {"elements": d1["cases"]["case_3"]["total_elements"], "pct_within_3l0": d1["cases"]["case_3"]["width_metrics"]["pct_within_3l0"], "gate_val": d1["cases"]["case_3"]["scientific_gate_value"], "gate_status": "PASS"},
                "step2b_reduced": {"elements": d2["variant_2b_reduced"]["case_3"]["elements"], "pct_within_3l0": d2["variant_2b_reduced"]["case_3"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2b_reduced"]["case_3"]["scientific_gate"]["val"], "gate_status": "FAIL"},
                "step2a_overlap": {"elements": d2["variant_2a_overlapping"]["case_3"]["elements"], "pct_within_3l0": d2["variant_2a_overlapping"]["case_3"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2a_overlapping"]["case_3"]["scientific_gate"]["val"], "gate_status": "FAIL"}
            },
            "case_5": {
                "f1812_baseline": {"elements": 15466, "pct_within_3l0": 29.31, "gate_val": 99.04, "gate_status": "PASS"},
                "step1_minmax": {"elements": d1["cases"]["case_5"]["total_elements"], "pct_within_3l0": d1["cases"]["case_5"]["width_metrics"]["pct_within_3l0"], "gate_val": d1["cases"]["case_5"]["scientific_gate_value"], "gate_status": "PASS"},
                "step2b_reduced": {"elements": d2["variant_2b_reduced"]["case_5"]["elements"], "pct_within_3l0": d2["variant_2b_reduced"]["case_5"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2b_reduced"]["case_5"]["scientific_gate"]["val"], "gate_status": "PASS"},
                "step2a_overlap": {"elements": d2["variant_2a_overlapping"]["case_5"]["elements"], "pct_within_3l0": d2["variant_2a_overlapping"]["case_5"]["width_metrics"]["f_3l0"], "gate_val": d2["variant_2a_overlapping"]["case_5"]["scientific_gate"]["val"], "gate_status": "PASS"}
            }
        },
        "artifact_manifest": {
            "step1_summary": {
                "path": to_rel(step1_json),
                "size_bytes": os.path.getsize(step1_json),
                "sha256": sha256_file(step1_json)
            },
            "step2_summary": {
                "path": to_rel(step2_json),
                "size_bytes": os.path.getsize(step2_json),
                "sha256": sha256_file(step2_json)
            },
            "comparison_figure_png": {
                "path": to_rel(fig_png),
                "size_bytes": os.path.getsize(fig_png),
                "sha256": sha256_file(fig_png)
            },
            "comparison_figure_pdf": {
                "path": to_rel(fig_pdf),
                "size_bytes": os.path.getsize(fig_pdf),
                "sha256": sha256_file(fig_pdf)
            }
        }
    }
    
    receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "PK_F1816_MULTISTEP_NARROWING_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
        
    print("Compiled Task F1816 master receipt:")
    print("  Path:   %s" % receipt_path)
    print("  Size:   %d bytes" % os.path.getsize(receipt_path))
    print("  SHA256: %s" % sha256_file(receipt_path))

if __name__ == "__main__":
    main()
