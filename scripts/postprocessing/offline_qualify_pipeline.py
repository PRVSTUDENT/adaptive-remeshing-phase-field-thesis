#!/usr/bin/env python3
"""
Offline Software Qualification Runner for Dual Validation Postprocessing Pipeline:
Tests and qualifies the extraction and evaluation algorithms against preserved historical HPC evidence:
  - 1389686.mmaster02 (M2CORR_H1_FREEU2_FULL_U050)
  - 1389687.mmaster02 (M2CORR_H2_FREEU2_FULL_U050)
  - 1389684.mmaster02 (M2CORR_PK10R1_CONTINUOUS_U050)
  - 1389715.mmaster02 (M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R2)
"""

import os
import sys
import json
from pathlib import Path

# Add script directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent.parent
sys.path.insert(0, str(SCRIPT_DIR))

from evaluate_m2corr_pk10r2_topology import evaluate_pk10r2_topology
from evaluate_m2corr_pk10r1_samemesh_r6 import evaluate_r6_restart

def main():
    print("================================================================================")
    print("OFFLINE SOFTWARE QUALIFICATION OF DUAL VALIDATION EVALUATION PIPELINE")
    print("================================================================================")
    
    evidence_base = ROOT / "models/generated/mode_ii"
    output_dir = ROOT / "runs/hpc/mode_ii_control_batch/evidence"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    qualification_results = {
        "suite_name": "OFFLINE_PIPELINE_SOFTWARE_QUALIFICATION",
        "tests": []
    }
    
    # --------------------------------------------------------------------------
    # Test 1: Topology Evaluator against Accepted H1 Reference (1389686)
    # --------------------------------------------------------------------------
    print("\n--- Test 1: Topology Evaluator against Accepted H1 Reference (1389686) ---")
    h1_dir = evidence_base / "production_verification_batch/M2CORR_H1_FREEU2_FULL_U050"
    if h1_dir.exists():
        out_json = output_dir / "QUALIFICATION_H1_1389686_TOPOLOGY_REPORT.json"
        res_h1 = evaluate_pk10r2_topology(str(h1_dir), output_json=str(out_json))
        
        extracted_k0 = res_h1.get("stiffness_metrics", {}).get("k0_kN_mm")
        extracted_peak_rf = res_h1.get("peak_metrics", {}).get("peak_rf1_kN")
        extracted_peak_u = res_h1.get("peak_metrics", {}).get("peak_u1_mm")
        
        expected_k0 = 529.67
        expected_peak_rf = 0.29957
        expected_peak_u = 0.000627
        
        diff_k0_pct = abs(extracted_k0 - expected_k0) / expected_k0 * 100.0 if extracted_k0 else 999.0
        diff_rf_pct = abs(extracted_peak_rf - expected_peak_rf) / expected_peak_rf * 100.0 if extracted_peak_rf else 999.0
        
        test1_pass = (diff_k0_pct < 0.1 and diff_rf_pct < 0.1)
        print(f"H1 K0: extracted={extracted_k0:.2f}, expected={expected_k0:.2f} (diff: {diff_k0_pct:.2f}%)")
        print(f"H1 Peak RF1: extracted={extracted_peak_rf:.5f}, expected={expected_peak_rf:.5f} (diff: {diff_rf_pct:.2f}%)")
        print(f"Test 1 Software Reproduction: {'PASS' if test1_pass else 'FAIL'}")
        
        qualification_results["tests"].append({
            "test_id": "TEST_01_TOPOLOGY_H1_1389686",
            "target": "M2CORR_H1_FREEU2_FULL_U050 (1389686.mmaster02)",
            "expected": {"k0_kN_mm": expected_k0, "peak_rf1_kN": expected_peak_rf, "peak_u1_mm": expected_peak_u},
            "extracted": {"k0_kN_mm": extracted_k0, "peak_rf1_kN": extracted_peak_rf, "peak_u1_mm": extracted_peak_u},
            "relative_difference_pct": {"k0": diff_k0_pct, "peak_rf1": diff_rf_pct},
            "reproduction_status": "PASS" if test1_pass else "FAIL"
        })

    # --------------------------------------------------------------------------
    # Test 2: Topology Evaluator against Accepted H2 Reference (1389687)
    # --------------------------------------------------------------------------
    print("\n--- Test 2: Topology Evaluator against Accepted H2 Reference (1389687) ---")
    h2_dir = evidence_base / "production_verification_batch/M2CORR_H2_FREEU2_FULL_U050"
    if h2_dir.exists():
        out_json = output_dir / "QUALIFICATION_H2_1389687_TOPOLOGY_REPORT.json"
        res_h2 = evaluate_pk10r2_topology(str(h2_dir), output_json=str(out_json))
        
        extracted_k0 = res_h2.get("stiffness_metrics", {}).get("k0_kN_mm")
        extracted_peak_rf = res_h2.get("peak_metrics", {}).get("peak_rf1_kN")
        extracted_peak_u = res_h2.get("peak_metrics", {}).get("peak_u1_mm")
        
        expected_k0 = 529.01
        expected_peak_rf = 0.29483
        expected_peak_u = 0.000616
        
        diff_k0_pct = abs(extracted_k0 - expected_k0) / expected_k0 * 100.0 if extracted_k0 else 999.0
        diff_rf_pct = abs(extracted_peak_rf - expected_peak_rf) / expected_peak_rf * 100.0 if extracted_peak_rf else 999.0
        
        test2_pass = (diff_k0_pct < 0.1 and diff_rf_pct < 0.1)
        print(f"H2 K0: extracted={extracted_k0:.2f}, expected={expected_k0:.2f} (diff: {diff_k0_pct:.2f}%)")
        print(f"H2 Peak RF1: extracted={extracted_peak_rf:.5f}, expected={expected_peak_rf:.5f} (diff: {diff_rf_pct:.2f}%)")
        print(f"Test 2 Software Reproduction: {'PASS' if test2_pass else 'FAIL'}")
        
        qualification_results["tests"].append({
            "test_id": "TEST_02_TOPOLOGY_H2_1389687",
            "target": "M2CORR_H2_FREEU2_FULL_U050 (1389687.mmaster02)",
            "expected": {"k0_kN_mm": expected_k0, "peak_rf1_kN": expected_peak_rf, "peak_u1_mm": expected_peak_u},
            "extracted": {"k0_kN_mm": extracted_k0, "peak_rf1_kN": extracted_peak_rf, "peak_u1_mm": extracted_peak_u},
            "relative_difference_pct": {"k0": diff_k0_pct, "peak_rf1": diff_rf_pct},
            "reproduction_status": "PASS" if test2_pass else "FAIL"
        })

    # --------------------------------------------------------------------------
    # Test 3: Topology Evaluator against Defective PK10R1 Baseline (1389684)
    # --------------------------------------------------------------------------
    print("\n--- Test 3: Topology Evaluator against Defective PK10R1 Baseline (1389684) ---")
    pk10_dir = evidence_base / "production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050"
    if pk10_dir.exists():
        out_json = output_dir / "QUALIFICATION_PK10R1_1389684_TOPOLOGY_REPORT.json"
        res_pk10 = evaluate_pk10r2_topology(str(pk10_dir), output_json=str(out_json))
        
        extracted_k0 = res_pk10.get("stiffness_metrics", {}).get("k0_kN_mm")
        extracted_peak_rf = res_pk10.get("peak_metrics", {}).get("peak_rf1_kN")
        
        expected_k0 = 639.80
        expected_peak_rf = 0.38324
        
        diff_k0_pct = abs(extracted_k0 - expected_k0) / expected_k0 * 100.0 if extracted_k0 else 999.0
        diff_rf_pct = abs(extracted_peak_rf - expected_peak_rf) / expected_peak_rf * 100.0 if extracted_peak_rf else 999.0
        
        test3_pass = (diff_k0_pct < 0.1 and diff_rf_pct < 0.1)
        print(f"PK10R1 K0: extracted={extracted_k0:.2f}, expected={expected_k0:.2f} (diff: {diff_k0_pct:.2f}%)")
        print(f"PK10R1 Peak RF1: extracted={extracted_peak_rf:.5f}, expected={expected_peak_rf:.5f} (diff: {diff_rf_pct:.2f}%)")
        print(f"PK10R1 Classification: {res_pk10.get('topology_classification')}")
        print(f"Test 3 Software Reproduction: {'PASS' if test3_pass else 'FAIL'}")
        
        qualification_results["tests"].append({
            "test_id": "TEST_03_TOPOLOGY_PK10R1_1389684",
            "target": "M2CORR_PK10R1_CONTINUOUS_U050 (1389684.mmaster02)",
            "expected": {"k0_kN_mm": expected_k0, "peak_rf1_kN": expected_peak_rf},
            "extracted": {"k0_kN_mm": extracted_k0, "peak_rf1_kN": extracted_peak_rf},
            "relative_difference_pct": {"k0": diff_k0_pct, "peak_rf1": diff_rf_pct},
            "topology_classification": res_pk10.get("topology_classification"),
            "reproduction_status": "PASS" if test3_pass else "FAIL"
        })

    # --------------------------------------------------------------------------
    # Test 4: Restart Evaluator against Same-Mesh Restart R2 Run (1389715)
    # --------------------------------------------------------------------------
    print("\n--- Test 4: Restart Evaluator against Same-Mesh Restart R2 Run (1389715) ---")
    r2_dir = evidence_base / "production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R2"
    if r2_dir.exists():
        out_json = output_dir / "QUALIFICATION_RESTART_R2_1389715_REPORT.json"
        res_r2 = evaluate_r6_restart(str(r2_dir), output_json=str(out_json))
        
        handoff_rf1 = res_r2.get("handoff_metrics", {}).get("handoff_rf1_kN")
        mech_jump_pct = res_r2.get("mechanical_release_metrics", {}).get("rf1_jump_pct")
        healing_detected = res_r2.get("phase_release_metrics", {}).get("phase_healing_detected")
        
        # In R2: handoff ~ 0.3063 kN, mech jump ~ +5.93%, healing detected (damage dropped to 0)
        test4_pass = (handoff_rf1 is not None and mech_jump_pct > 5.0 and healing_detected is True)
        print(f"R2 Handoff RF1: {handoff_rf1:.5f} kN")
        print(f"R2 Mech Release Jump: {mech_jump_pct:.2f}% (Expected > 5.0%)")
        print(f"R2 Phase Healing Detected: {healing_detected} (Expected True)")
        print(f"Test 4 Software Reproduction: {'PASS' if test4_pass else 'FAIL'}")
        
        qualification_results["tests"].append({
            "test_id": "TEST_04_RESTART_R2_1389715",
            "target": "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R2 (1389715.mmaster02)",
            "extracted": {
                "handoff_rf1_kN": handoff_rf1,
                "mech_release_jump_pct": mech_jump_pct,
                "phase_healing_detected": healing_detected
            },
            "reproduction_status": "PASS" if test4_pass else "FAIL"
        })

    # Save overall qualification results
    summary_path = output_dir / "DUAL_VALIDATION_PIPELINE_SOFTWARE_QUALIFICATION_SUMMARY.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(qualification_results, f, indent=2)
    print(f"\nSaved qualification suite summary to: {summary_path}")

if __name__ == "__main__":
    main()
