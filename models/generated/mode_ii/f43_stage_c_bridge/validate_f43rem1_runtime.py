#!/bin/python3
"""
Runtime Validator for F43REM1 Abaqus Native Remeshing Job.
Enforces fail-closed evaluation of scientific runtime success gates.
"""
import sys
import os
import json

def validate_f43rem1_runtime(evidence_dir):
    refined_deck = os.path.join(evidence_dir, "F43REFINED_standard.inp")
    exec_log = os.path.join(evidence_dir, "execution.log")
    
    if not os.path.exists(refined_deck):
        refined_deck = "F43REFINED_standard.inp"
    if not os.path.exists(exec_log):
        exec_log = "execution.log"

    results = {
        "terminal_success_marker_present": False,
        "refined_deck_generated": False,
        "refined_deck_size_bytes": 0,
        "cpe4_elements_present": False,
        "cpe3_elements_present": False,
        "overall_validation_passed": False
    }

    # Check terminal success marker F43REM1_RUNTIME_SUCCESS=true
    if os.path.exists(exec_log):
        with open(exec_log, "r") as f:
            log_content = f.read()
            if "F43REM1_RUNTIME_SUCCESS=true" in log_content:
                results["terminal_success_marker_present"] = True

    if os.path.exists(refined_deck):
        size = os.path.getsize(refined_deck)
        results["refined_deck_size_bytes"] = size
        if size > 100:  # Refined deck must be non-empty and hold real element structure
            results["refined_deck_generated"] = True
            with open(refined_deck, "r") as f:
                content = f.read()
                if "CPE4" in content or "cpe4" in content:
                    results["cpe4_elements_present"] = True
                if "CPE3" in content or "cpe3" in content:
                    results["cpe3_elements_present"] = True

    # MUST pass terminal success marker AND non-empty refined deck with valid continuum elements
    results["overall_validation_passed"] = (
        results["terminal_success_marker_present"] and
        results["refined_deck_generated"] and
        (results["cpe4_elements_present"] or results["cpe3_elements_present"])
    )

    out_status_path = os.path.join(evidence_dir, "F43REM1_VALIDATION_STATUS.json")
    with open(out_status_path, "w") as f:
        json.dump(results, f, indent=2)

    return results["overall_validation_passed"]

if __name__ == "__main__":
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    passed = validate_f43rem1_runtime(evidence_dir)
    sys.exit(0 if passed else 1)

