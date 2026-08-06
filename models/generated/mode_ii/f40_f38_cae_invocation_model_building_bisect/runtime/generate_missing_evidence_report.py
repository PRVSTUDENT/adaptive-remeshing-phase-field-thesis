#!/usr/bin/env python3
import json
import os
import sys
import datetime

EXPECTED_EVIDENCE_FILES = [
    "STATUS.json",
    "SCHEDULER_PROVENANCE.json",
    "F38_F39_INVOCATION_DELTA_AUDIT.json",
    "P00_KERNEL_STARTUP_AUDIT.json",
    "P01_IMPORTS_AUDIT.json",
    "P02_MODULE_LOADING_AUDIT.json",
    "P03_SOURCE_DECK_DISCOVERY_AUDIT.json",
    "P04_MODEL_FROM_INPUT_FILE_AUDIT.json",
    "P05_IMPORTED_MODEL_INVENTORY_AUDIT.json",
    "P06_GEOMETRY_CONVERSION_AUDIT.json",
    "P07_INDEPENDENT_MODEL_OWNERSHIP_AUDIT.json",
    "P08_ASSEMBLY_OPERATIONS_AUDIT.json",
    "P09_TOPOLOGY_MEASUREMENT_AUDIT.json",
    "P10_SETS_SURFACES_INVENTORY_AUDIT.json",
    "P11_STEP_OUTPUT_PROBING_AUDIT.json",
    "CAE_INVOCATION_CONTEXT_AUDIT.json",
    "CAE_PHASE_DIAGNOSTIC_MATRIX.json",
    "delta_auditor.returncode",
    "bisection_runner.returncode",
    "f38_entrypoint.returncode",
    "f38_matrix_validator.returncode",
    "runtime_validator.returncode",
    "first_failure.returncode"
]

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."

    actual_files_in_dir = set()
    if os.path.exists(target_dir):
        actual_files_in_dir = set(os.listdir(target_dir))

    missing_files = [f for f in EXPECTED_EVIDENCE_FILES if f not in actual_files_in_dir]
    existing_files = [f for f in EXPECTED_EVIDENCE_FILES if f in actual_files_in_dir]

    if "MISSING_EVIDENCE_REPORT.json" in missing_files:
        missing_files.remove("MISSING_EVIDENCE_REPORT.json")
    if "MISSING_EVIDENCE_REPORT.json" not in existing_files:
        existing_files.append("MISSING_EVIDENCE_REPORT.json")

    existing_files.sort()
    missing_files.sort()

    report = {
        "protocol_version": 1,
        "job_name": "M2RMBISECT1",
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "missing_count": len(missing_files),
        "missing_files": missing_files,
        "existing_files": existing_files,
        "status": "complete" if len(missing_files) == 0 else "incomplete"
    }

    report_path = os.path.join(target_dir, "MISSING_EVIDENCE_REPORT.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("MISSING_EVIDENCE_REPORT_GENERATED: missing_count={}".format(len(missing_files)))
    return 0 if len(missing_files) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
