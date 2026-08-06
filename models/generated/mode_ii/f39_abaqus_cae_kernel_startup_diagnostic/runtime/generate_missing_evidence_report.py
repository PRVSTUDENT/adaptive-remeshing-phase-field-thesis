#!/usr/bin/env python3
import json
import os
import sys
import datetime

EXPECTED_EVIDENCE_FILES = [
    "STATUS.json",
    "ABAQUS_LAUNCHER_ENVIRONMENT_AUDIT.json",
    "CAE_KERNEL_STARTUP_AUDIT.json",
    "RUNTIME_FAILURE_AUDIT.json",
    "MISSING_EVIDENCE_REPORT.json",
    "python_probe.returncode",
    "cae_kernel.returncode",
    "runtime_validator.returncode",
    "collector.returncode",
    "first_failure.returncode",
    "module_list.txt",
    "abaqus_information_release.txt",
    "abaqus_information_system.txt",
    "resolved_abaqus_launcher.txt"
]

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    actual_files_in_dir = set()
    if os.path.exists(target_dir):
        actual_files_in_dir = set(os.listdir(target_dir))

    missing_files = [f for f in EXPECTED_EVIDENCE_FILES if f not in actual_files_in_dir]
    existing_files = [f for f in EXPECTED_EVIDENCE_FILES if f in actual_files_in_dir]

    # Include self (MISSING_EVIDENCE_REPORT.json) in existing_files since it is being generated now
    if "MISSING_EVIDENCE_REPORT.json" in missing_files:
        missing_files.remove("MISSING_EVIDENCE_REPORT.json")
    if "MISSING_EVIDENCE_REPORT.json" not in existing_files:
        existing_files.append("MISSING_EVIDENCE_REPORT.json")
    existing_files.sort()
    missing_files.sort()

    report = {
        "protocol_version": 1,
        "job_name": "M2RMKERN1",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "missing_count": len(missing_files),
        "missing_files": missing_files,
        "existing_files": existing_files,
        "status": "complete" if len(missing_files) == 0 else "incomplete"
    }

    report_path = os.path.join(target_dir, "MISSING_EVIDENCE_REPORT.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print("MISSING_EVIDENCE_REPORT_GENERATED: missing_count={}".format(len(missing_files)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
