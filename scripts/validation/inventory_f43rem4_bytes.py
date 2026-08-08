#!/usr/bin/env python3
"""
Inventory Execution-Critical F43REM4 Bytes and Verify Zero-Difference Relative to Preparation Commit da46210.
"""

import sys
import os
import hashlib
import json
import subprocess

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

EXECUTION_CRITICAL_FILES = [
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_pk1.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_pk5.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/remesh_sensitivity_config_mm.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_BATCH_MANIFEST.json",
    "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_BATCH_AUTHORIZATION.json",
    "scripts/validation/run_real_abaqus_f43rem4_probes.py",
    "scripts/validation/run_f43rem4_real_kernel_probe_hpc.sh",
    "tests/unit/test_f43rem4_batch_contract.py",
    "scripts/validation/evaluate_gate_c1_scientific_integrity.py",
    "models/generated/mode_ii/f43_stage_c_bridge/build_mode_ii_native_cae.py",
]

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def get_git_file_content_at_commit(commit, rel_path):
    cmd = ["git", "show", f"{commit}:{rel_path}"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return res.stdout

def main():
    target_p = "da46210cbf2e34f71a545c51b12e3f6351f5502c"
    print("=== INVENTORYING EXECUTION-CRITICAL F43REM4 BYTES AT P =", target_p, "===")

    hashes_p = {}
    hashes_current = {}
    differences = []

    for rel_path in EXECUTION_CRITICAL_FILES:
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        cur_sha = sha256_file(full_path)
        hashes_current[rel_path] = cur_sha

        content_p = get_git_file_content_at_commit(target_p, rel_path)
        sha_p = hashlib.sha256(content_p).hexdigest()
        hashes_p[rel_path] = sha_p

        print(f"File: {rel_path}")
        print(f"  P_SHA256:       {sha_p}")
        print(f"  Current_SHA256: {cur_sha}")

        if cur_sha != sha_p:
            differences.append(rel_path)

    execution_bytes_unchanged = (len(differences) == 0)
    print("\nExecution-critical differences relative to final P:", differences)
    print("execution_bytes_unchanged_from_final_P:", execution_bytes_unchanged)

    inventory_report = {
        "target_P_sha": target_p,
        "execution_bytes_unchanged_from_final_P": execution_bytes_unchanged,
        "differences": differences,
        "execution_critical_file_hashes_at_P": hashes_p,
    }

    out_json = os.path.join(
        PROJECT_ROOT,
        "models",
        "generated",
        "mode_ii",
        "f43_stage_c_bridge",
        "remesh_sensitivity_batch",
        "F43REM4_EXECUTION_BYTES_INVENTORY.json",
    )
    with open(out_json, "w") as f:
        json.dump(inventory_report, f, indent=2)

    print("Wrote inventory report to:", out_json)

    if not execution_bytes_unchanged:
        sys.exit(1)

if __name__ == "__main__":
    main()
