# Python 2 and 3 compatible missing evidence report generator for F31
# Inspects target evidence directory, verifies all required evidence files,
# and outputs MISSING_EVIDENCE_REPORT.json.
from __future__ import print_function
import sys
import os
import json

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_report_path = os.path.join(target_dir, 'MISSING_EVIDENCE_REPORT.json')

    required_files = [
        "SOURCE_MODEL_INVENTORY.json",
        "INSTANCE_REPLACEMENT_API_AUDIT.json",
        "MODEL_ENTITY_REBINDING_AUDIT.json",
        "SLIT_GEOMETRY_AUDIT.json",
        "SLIT_MESH_TOPOLOGY_AUDIT.json",
        "GEOMETRY_BACKED_MODEL_AUDIT.json",
        "GENERATED_INPUT_AUDIT.json",
        "COMPATIBILITY_AUDIT.json",
        "EXECUTION_COUNTERS.json",
        "START_NOTIFICATION_RESULT.json",
        "TERMINAL_NOTIFICATION_RESULT.json",
        "REDACTION_AUDIT.json",
        "STATUS.json",
        "compatibility.returncode",
        "cae_builder.returncode",
        "generated_input_validator.returncode",
        "runtime_validator.returncode",
        "collector.returncode",
        "first_failure.returncode"
    ]

    missing_files = []
    present_files = []

    for fname in required_files:
        fpath = os.path.join(target_dir, fname)
        if os.path.exists(fpath):
            present_files.append(fname)
        else:
            missing_files.append(fname)

    all_evidence_present = (len(missing_files) == 0)

    report = {
        "protocol_version": 1,
        "task_id": "F31-INVALIDATE-F30-AND-REPAIR-M2RMBUILD5-STATIC-GATE",
        "target_directory": os.path.abspath(target_dir),
        "required_file_count": len(required_files),
        "present_file_count": len(present_files),
        "missing_file_count": len(missing_files),
        "present_files": present_files,
        "missing_files": missing_files,
        "all_evidence_present": all_evidence_present
    }

    with open(output_report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print("Missing evidence report generated at: " + str(output_report_path))
    if not all_evidence_present:
        print("WARNING: Missing evidence files: " + str(missing_files))

if __name__ == '__main__':
    main()
