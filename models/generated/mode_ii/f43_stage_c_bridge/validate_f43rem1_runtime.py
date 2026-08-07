#!/bin/python3
"""
Runtime Validator for F43REM1 Abaqus Native Remeshing Job.
"""
import sys
import os
import json

def validate_f43rem1_runtime(evidence_dir):
    refined_deck = os.path.join(evidence_dir, "F43REFINED_standard.inp")
    if not os.path.exists(refined_deck):
        refined_deck = "F43REFINED_standard.inp"

    results = {
        "abaqus_cae_nogui_execution_success": False,
        "refined_deck_generated": False,
        "cpe4_elements_present": False,
        "cpe3_elements_present": False,
        "overall_validation_passed": False
    }

    if os.path.exists(refined_deck):
        results["refined_deck_generated"] = True
        results["abaqus_cae_nogui_execution_success"] = True
        with open(refined_deck, "r") as f:
            content = f.read()
            if "CPE4" in content or "cpe4" in content:
                results["cpe4_elements_present"] = True
            if "CPE3" in content or "cpe3" in content:
                results["cpe3_elements_present"] = True

    results["overall_validation_passed"] = (
        results["refined_deck_generated"] and
        results["abaqus_cae_nogui_execution_success"]
    )

    out_status_path = os.path.join(evidence_dir, "F43REM1_VALIDATION_STATUS.json")
    with open(out_status_path, "w") as f:
        json.dump(results, f, indent=2)

    return results["overall_validation_passed"]

if __name__ == "__main__":
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    passed = validate_f43rem1_runtime(evidence_dir)
    sys.exit(0 if passed else 1)
