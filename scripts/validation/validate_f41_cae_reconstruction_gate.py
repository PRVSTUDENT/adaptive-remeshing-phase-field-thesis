#!/usr/bin/env python3
"""
F41 Static Gate Validator

Validates code formatting, package manifest integrity, PBS directives, line endings,
and prohibited patterns across Stage F41 package files.
"""

import ast
import hashlib
import json
import os
import sys

F41_PACKAGE_DIR = os.path.normpath("models/generated/mode_ii/f41_crack_geometry_reconstruction")
REQUIRED_FILES = [
    "M2RMSTITCH1.pbs",
    "PACKAGE_MANIFEST.json",
    "SHA256SUMS",
    "F41_SHA256SUMS",
    "runtime/source_deck.inp",
    "runtime/f41_crack_topology_extractor.py",
    "runtime/f41_cae_reconstruction_matrix.py",
    "runtime/run_f41_cae_reconstruction.py",
    "runtime/validate_f41_matrix_results.py",
    "runtime/validate_f41_runtime_audits.py",
    "runtime/generate_missing_evidence_report.py"
]

def main():
    errors = []

    if not os.path.exists(F41_PACKAGE_DIR):
        print("F41_STATIC_GATE_FAILED: F41 package directory missing")
        return 1

    # Check required files
    for rel_f in REQUIRED_FILES:
        full_p = os.path.join(F41_PACKAGE_DIR, rel_f)
        if not os.path.exists(full_p):
            errors.append("Missing required file: {0}".format(rel_f))

    if errors:
        print("F41_STATIC_GATE_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    # Check PBS directives in M2RMSTITCH1.pbs
    pbs_path = os.path.join(F41_PACKAGE_DIR, "M2RMSTITCH1.pbs")
    with open(pbs_path, 'r') as f:
        pbs_content = f.read()

    if "\r\n" in pbs_content:
        errors.append("M2RMSTITCH1.pbs contains CRLF line endings (must be LF)")
    if "#PBS -N M2RMSTITCH1" not in pbs_content:
        errors.append("M2RMSTITCH1.pbs missing '#PBS -N M2RMSTITCH1'")
    if "#PBS -q entry_imfdfkmq" not in pbs_content:
        errors.append("M2RMSTITCH1.pbs missing '#PBS -q entry_imfdfkmq'")
    if "select=1:ncpus=1:mpiprocs=1:ompthreads=1:mem=8gb" not in pbs_content:
        errors.append("M2RMSTITCH1.pbs resource specification mismatch")
    if "walltime=00:30:00" not in pbs_content:
        errors.append("M2RMSTITCH1.pbs walltime mismatch")

    # Check Python syntax for runtime files
    for root, dirs, fnames in os.walk(os.path.join(F41_PACKAGE_DIR, "runtime")):
        for fn in fnames:
            if fn.endswith(".py"):
                fp = os.path.join(root, fn)
                with open(fp, 'r') as f:
                    content = f.read()
                try:
                    ast.parse(content, filename=fp)
                except SyntaxError as exc:
                    errors.append("SyntaxError in {0}: {1}".format(fn, exc))

    # Verify SHA256SUMS manifest matches
    manifest_path = os.path.join(F41_PACKAGE_DIR, "F41_SHA256SUMS")
    if os.path.exists(manifest_path):
        with open(manifest_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    expected_hash, rel_path = parts[0], parts[1]
                    if "__pycache__" in rel_path or rel_path.endswith(".pyc"):
                        continue
                    file_p = os.path.join(F41_PACKAGE_DIR, rel_path)

                    if os.path.exists(file_p):
                        with open(file_p, 'rb') as fp:
                            actual_hash = hashlib.sha256(fp.read()).hexdigest()
                        if actual_hash != expected_hash:
                            errors.append("SHA256 mismatch for {0}".format(rel_path))

    if errors:
        print("F41_STATIC_GATE_FAILED:")
        for err in errors:
            print("  - " + err)
        return 1

    print("F41_STATIC_GATE_PASSED")
    return 0

if __name__ == "__main__":
    sys.exit(main())
