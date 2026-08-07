#!/usr/bin/env python3
"""
Validate F41 Runtime Audits

Validates evidence contract completeness for Stage F41 evidence directories.
"""

import json
import os
import sys

REQUIRED_EVIDENCE_FILES = [
    "F41_TOPOLOGY_MAP.json",
    "F41_CRACK_RECONSTRUCTION_AUDIT.json",
    "F41_CAE_RECONSTRUCTION_MATRIX.json",
    "F41_RECONSTRUCTION.returncode"
]

def main():
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    errors = []

    for fname in REQUIRED_EVIDENCE_FILES:
        fpath = os.path.join(evidence_dir, fname)
        if not os.path.exists(fpath):
            errors.append("Missing required evidence file: {0}".format(fname))

    if errors:
        print("F41_RUNTIME_AUDIT_VALIDATION_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("F41_RUNTIME_AUDIT_VALIDATION_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
