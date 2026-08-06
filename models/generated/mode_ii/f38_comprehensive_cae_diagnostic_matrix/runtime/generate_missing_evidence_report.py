from __future__ import print_function
import sys
import os
import json

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    output_report_path = os.path.join(target_dir, 'MISSING_EVIDENCE_REPORT.json')

    required_files = [
        "CAE_INVOCATION_CONTEXT_AUDIT.json",
        "CAE_PHASE_DIAGNOSTIC_MATRIX.json",
        "STATUS.json",
        "python_probe.returncode",
        "cae_diagnostic.returncode",
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
        "task_id": "F38-CLOSE-M2RMBUILD11-AND-PREPARE-COMPREHENSIVE-CAE-DIAGNOSTIC",
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

if __name__ == '__main__':
    main()
