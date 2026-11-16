# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1818_receipt.py
===========================================
Compiles the definitive machine-readable receipt for Task F1818:
  models/pandey_kumar_mode1/263_f1816_multistep_narrowing/PK_F1818_CORRECTION_REASSESSMENT_RECEIPT.json
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

def to_rel(path):
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace("\\", "/")

def main():
    step1_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step1_minmax", "step1_minmax_summary.json")
    step2_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step2_envelope", "step2_envelope_summary.json")
    f1816_receipt = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "PK_F1816_MULTISTEP_NARROWING_RECEIPT.json")
    
    with open(step1_json, "r") as f:
        d1 = json.load(f)
    with open(step2_json, "r") as f:
        d2 = json.load(f)
        
    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    
    fig_png = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.png")
    fig_pdf = os.path.join(REPO_ROOT, "results", "figures", "fig_f1816_refinement_width_comparison.pdf")
    
    report_f1818 = os.path.join(REPO_ROOT, "docs", "validation", "F1818_CORRECTION_AND_REASSESSMENT_REPORT.md")
    report_f1816 = os.path.join(REPO_ROOT, "docs", "validation", "F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md")
    report_f1817 = os.path.join(REPO_ROOT, "docs", "validation", "F1817_EVIDENCE_COMPLETION_REPORT.md")
    
    receipt = {
        "task_id": "F1818-CORRECTION-AND-REASSESSMENT",
        "title": "Task F1818: Correction and Reassessment of F1816 Narrowing Conclusions",
        "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
        "correlation_id": "HND-F1818-CORRECTION-REASSESSMENT-001",
        "predecessor_correlation_id": "HND-F1817-EVIDENCE-COMPLETION-001",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "governing_objectives": {
            "master_goal_status": "OPEN",
            "research_priority": "ADAPTIVE_REMESHING_ONLY",
            "cumulative_pbs_submissions": 35,
            "new_pbs_submissions": 0,
            "frozen_production_uel_sha256": sha256_file(uel_path),
            "shared_framework_sha256": sha256_file(framework_path),
            "predeclared_adoption_rule": "F1812 baselines stand as best among tested configurations; MINIMUM_MAXIMUM sizing remains untested."
        },
        "reassessed_findings": {
            "correction_1_sizing_method_provenance": {
                "configured_in_script": "MINIMUM_MAXIMUM",
                "framework_execution": "UNIFORM_ERROR with errorTarget=3.0% (hardcoded in framework line 1922; config.sizing_method ignored)",
                "element_ballooning_cause": "Stricter error target (3.0% vs F1812's 4.5% in Case 1)",
                "status": "WITHDRAWN as MINIMUM_MAXIMUM finding; MINIMUM_MAXIMUM remains untested"
            },
            "correction_2_case3_secondary_gates": {
                "evaluation_corridor": "x in [36.5, 65.0] mm, y in [45.0, 65.0] mm, threshold h <= l0 = 0.285 mm",
                "variant_2b_reduced": {
                    "total_elements_in_corridor": 12964,
                    "refined_elements": 12300,
                    "coverage_pct": 94.87812403579142,
                    "gate_status": "PASS (>= 90.0%)",
                    "prior_value_defect": "Prior 87.61% caused by y in [45, 75] capturing unrefined bulk elements"
                },
                "variant_2a_overlapping": {
                    "total_elements_in_corridor": 11440,
                    "refined_elements": 10556,
                    "coverage_pct": 92.27272727272727,
                    "gate_status": "PASS (>= 90.0%)",
                    "prior_value_defect": "Prior 86.30% caused by y in [45, 75] capturing unrefined bulk elements"
                }
            },
            "correction_3_run_script_hashes": {
                "run_f1816_step1_master.py": {"size": 3557, "sha256": "0F33EFEBD4302D8FD1D6A7FC1E78CCC352AD187968D84082BFD91B4599D3FB53"},
                "run_f1816_step1_minmax.py": {"size": 15552, "sha256": "3B9253DF21A65FD13694EC3FA9C88A9C91EB73AD6AFDA519122A38F439B10229"},
                "run_f1816_step2_master.py": {"size": 15835, "sha256": "931E683CC4DF47C99CEB3AD33F97022A2E843606A76978DAD229A9D27C83AAC2"},
                "run_f1816_step2_single.py": {"size": 6032, "sha256": "95D6207C89410EB6B3D3CBC88C52F7CF112398D7DCBF8FDF99FBBD15A48D46DA"}
            },
            "pareto_optimum_reassessment": {
                "f1812_total_elements": 160144,
                "variant_2b_total_elements": 180242,
                "variant_2a_total_elements": 193310,
                "step1_total_elements": 258894,
                "f1812_status": "PARETO_OPTIMUM_AMONG_TESTED_CONFIGURATIONS",
                "variant_2b_rejection_reason": "Fails Case 1 full ligament gate (91.75% < 95.0%) and doubles Case 2 elements to 83,913",
                "variant_2a_rejection_reason": "Balloons Case 1 to 37,511 and Case 2 to 82,869 elements; dilutes localization",
                "minimum_maximum_status": "EXPLICITLY_UNTESTED_OPEN_QUESTION"
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
            "f1816_receipt": {
                "path": to_rel(f1816_receipt),
                "size_bytes": os.path.getsize(f1816_receipt),
                "sha256": sha256_file(f1816_receipt)
            },
            "f1816_report": {
                "path": to_rel(report_f1816),
                "size_bytes": os.path.getsize(report_f1816),
                "sha256": sha256_file(report_f1816)
            },
            "f1817_report": {
                "path": to_rel(report_f1817),
                "size_bytes": os.path.getsize(report_f1817),
                "sha256": sha256_file(report_f1817)
            },
            "f1818_report": {
                "path": to_rel(report_f1818),
                "size_bytes": os.path.getsize(report_f1818),
                "sha256": sha256_file(report_f1818)
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
    
    receipt_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "PK_F1818_CORRECTION_REASSESSMENT_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
        
    print("Compiled Task F1818 master receipt:")
    print("  Path:   %s" % receipt_path)
    print("  Size:   %d bytes" % os.path.getsize(receipt_path))
    print("  SHA256: %s" % sha256_file(receipt_path))

if __name__ == "__main__":
    main()
