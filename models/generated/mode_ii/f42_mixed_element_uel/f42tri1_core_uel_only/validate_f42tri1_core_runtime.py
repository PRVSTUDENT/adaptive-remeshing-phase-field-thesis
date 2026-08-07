#!/usr/bin/env python3
"""
Runtime Validator for F42TRI1_CORE Execution Evidence
"""
import sys
import os
import json

def validate_runtime(evidence_dir):
    log_path = os.path.join(evidence_dir, "F42TRI1_CORE.log")
    dat_path = os.path.join(evidence_dir, "F42TRI1_CORE.dat")
    sta_path = os.path.join(evidence_dir, "F42TRI1_CORE.sta")

    report = {
        "job_completed_successfully": False,
        "u3_jtype3_verified": False,
        "u4_jtype4_verified": False,
        "integration_points_visited": 0,
        "errors": []
    }

    if not os.path.exists(evidence_dir):
        report["errors"].append(f"Evidence directory not found: {evidence_dir}")
        print(json.dumps(report, indent=2))
        sys.exit(1)

    if os.path.exists(log_path):
        with open(log_path, 'r') as f:
            content = f.read()
            if "COMPLETED SUCCESSFULLY" in content.upper() or "THE ANALYSIS HAS BEEN COMPLETED" in content.upper():
                report["job_completed_successfully"] = True
            if "DIAG F42TRI1_CORE U3" in content:
                report["u3_jtype3_verified"] = True
            if "DIAG F42TRI1_CORE U4" in content:
                report["u4_jtype4_verified"] = True

    output_report_path = os.path.join(evidence_dir, "F42TRI1_CORE_RUNTIME_VALIDATION.json")
    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Validation report saved to {output_report_path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: validate_f42tri1_core_runtime.py <evidence_dir>")
        sys.exit(1)
    validate_runtime(sys.argv[1])
