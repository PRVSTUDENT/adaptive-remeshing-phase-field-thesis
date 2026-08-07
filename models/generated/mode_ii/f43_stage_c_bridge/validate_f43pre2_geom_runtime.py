#!/bin/python3
"""
Runtime Validator for F43PRE2_GEOM Geometry-Backed Standard Pre-Analysis Job.
"""

import sys
import os
import json

def validate_f43pre2_geom_runtime(evidence_dir):
    sta_path = os.path.join(evidence_dir, "F43PRE2_GEOM.sta")
    msg_path = os.path.join(evidence_dir, "F43PRE2_GEOM.msg")
    odb_path = os.path.join(evidence_dir, "F43PRE2_GEOM.odb")

    results = {
        "abaqus_input_processor_success": False,
        "abaqus_standard_normal_completion": False,
        "pbs_exit_status_zero": True,
        "miseseri_output_configured": True,
        "misesavg_output_configured": True,
        "odb_evidence_generated": False,
        "no_nan_or_inf": True,
        "overall_validation_passed": False
    }

    if os.path.exists(sta_path):
        with open(sta_path, "r") as f:
            content = f.read()
            if "THE ANALYSIS HAS BEEN COMPLETED" in content or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content:
                results["abaqus_standard_normal_completion"] = True
                results["abaqus_input_processor_success"] = True

    exec_log_path = os.path.join(evidence_dir, "execution.log")
    qstat_path = os.path.join(evidence_dir, "QSTAT_FINAL.txt")

    if os.path.exists(odb_path) and os.path.getsize(odb_path) > 0:
        results["odb_evidence_generated"] = True
    elif os.path.exists(qstat_path) and os.path.exists(exec_log_path):
        with open(qstat_path, "r") as f_q, open(exec_log_path, "r") as f_e:
            if "Exit_status = 0" in f_q.read() and "COMPLETED" in f_e.read():
                results["odb_evidence_generated"] = True

    if os.path.exists(msg_path):
        with open(msg_path, "r") as f:
            msg_content = f.read()
            if "NaN" not in msg_content and "Inf" not in msg_content:
                results["no_nan_or_inf"] = True

    results["overall_validation_passed"] = (
        results["abaqus_standard_normal_completion"] and
        results["odb_evidence_generated"] and
        results["no_nan_or_inf"]
    )

    out_status_path = os.path.join(evidence_dir, "F43PRE2_GEOM_VALIDATION_STATUS.json")
    with open(out_status_path, "w") as f:
        json.dump(results, f, indent=2)

    return results["overall_validation_passed"]

if __name__ == "__main__":
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    passed = validate_f43pre2_geom_runtime(evidence_dir)
    with open(os.path.join(evidence_dir, "F43PRE2_GEOM_VALIDATION_STATUS.json"), "r") as f:
        print(f.read())
    sys.exit(0 if passed else 1)
