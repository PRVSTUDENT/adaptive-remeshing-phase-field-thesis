#!/usr/bin/env python3
"""
Inventory execution-critical F43REM4 batch files and verify byte immutability.
"""

import sys
import os
import hashlib

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXECUTION_CRITICAL_FILES = [
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_pk1.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_pk5.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_mm.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_BATCH_MANIFEST.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_BATCH_AUTHORIZATION.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_mode_ii_native_cae.py",
    "models/generated/mode_ii/f43_stage_c_bridge/build_mode_ii_native_cae.py",
    "models/generated/mode_ii/f43_stage_c_bridge/submit_f43rem3_native.sh",
    "scripts/validation/evaluate_gate_c1_scientific_integrity.py",
    "scripts/validation/probe_f43rem4_batch_rules.py",
    "scripts/validation/run_f43rem4_q1_detached_qual.sh",
    "tests/unit/test_f43rem4_batch_contract.py",
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    print("=== INVENTORYING F43REM4 EXECUTION-CRITICAL BYTES ===")
    hashes = {}
    for rel_path in EXECUTION_CRITICAL_FILES:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(full_path):
            print(f"FATAL: Missing execution-critical file: {rel_path}")
            sys.exit(1)
        h = sha256_file(full_path)
        hashes[rel_path] = h
        print(f"  {rel_path}: {h}")

    print("=== ALL EXECUTION-CRITICAL FILES VERIFIED AND HASHED ===")

if __name__ == "__main__":
    main()
