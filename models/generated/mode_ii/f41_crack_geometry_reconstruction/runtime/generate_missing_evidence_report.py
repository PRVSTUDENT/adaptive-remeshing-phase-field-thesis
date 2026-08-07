#!/usr/bin/env python3
import json
import os
import sys

EXPECTED_FILES = [
    "F41_TOPOLOGY_MAP.json",
    "F41_CRACK_RECONSTRUCTION_AUDIT.json",
    "F41_CAE_RECONSTRUCTION_MATRIX.json",
    "f41_reconstruction.returncode"
]

def main():
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    missing = []
    existing = []

    for fname in EXPECTED_FILES:
        if os.path.exists(os.path.join(evidence_dir, fname)):
            existing.append(fname)
        else:
            missing.append(fname)

    report = {
        "protocol_version": 1,
        "job_name": "M2RMSTITCH1",
        "missing_count": len(missing),
        "missing_files": missing,
        "existing_files": existing,
        "status": "complete" if not missing else "incomplete"
    }

    out_path = os.path.join(evidence_dir, "MISSING_EVIDENCE_REPORT.json")
    with open(out_path, 'w') as f:
        json.dump(report, f, indent=2)

    return 0

if __name__ == "__main__":
    sys.exit(main())
