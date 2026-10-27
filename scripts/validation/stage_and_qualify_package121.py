#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_and_qualify_package121.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Stages Package 121 (Increment-88 C3 Same-Mesh Control) files on cluster scratch,
verifies remote SHA256 checksums, and runs Abaqus 2023 interactive datacheck.
"""

import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/121_c3_inc88_samemesh_control"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c3_inc88_samemesh_control"
PREV_REMOTE = "/scratch9/pr21vyci/runs/mode1_c4_inc88_holdout_diagnostic"

files_to_verify = [
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_c3_inc88_samemesh_control.py",
    "f42_unified_12dof_active_set_uel.for",
    "job_notifications.sh",
    "M1_C3_INC88_SAMEMESH_CONTROL.inp",
    "M1_C3_INC88_SAMEMESH_AUTHORIZATION.json",
    "nodal_displacements_initial.csv",
    "PACKAGE_MANIFEST.json",
    "run_c3_inc88_samemesh_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"
]

files_to_upload = [
    "active_set_boundary_cards.inc",
    "d_lower_bounds.csv",
    "driver_c3_inc88_samemesh_control.py",
    "M1_C3_INC88_SAMEMESH_CONTROL.inp",
    "M1_C3_INC88_SAMEMESH_AUTHORIZATION.json",
    "nodal_displacements_initial.csv",
    "PACKAGE_MANIFEST.json",
    "run_c3_inc88_samemesh_datacheck.sh",
    "stage_a_all_d0_boundary_cards.inc",
    "submit_M1_C3_INC88_SAMEMESH_CONTROL.pbs"
]

def run_remote(cmd):
    res = subprocess.run([
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        r".\.agents\scripts\Invoke-GuardedSsh.ps1",
        "-RemoteCommand", cmd
    ], capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Remote command failed:\n{cmd}\nStderr: {res.stderr}\nStdout: {res.stdout}")
    return res.stdout

def main():
    print(f"Creating remote run directory: {REMOTE_DIR}")
    cmd_init = f"mkdir -p {REMOTE_DIR} && cp {PREV_REMOTE}/f42_unified_12dof_active_set_uel.for {PREV_REMOTE}/job_notifications.sh {REMOTE_DIR}/"
    run_remote(cmd_init)

    print(f"Uploading Package 121 files to {REMOTE_DIR}...")
    for f in files_to_upload:
        src = str(PKG_DIR / f)
        dst = f"tu_freiberg:{REMOTE_DIR}/{f}"
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"SCP failed for {f}: {res.stderr}")
        print(f"  Uploaded: {f}")

    print("Setting execution permissions on scripts...")
    run_remote(f"chmod +x {REMOTE_DIR}/*.sh {REMOTE_DIR}/*.pbs {REMOTE_DIR}/*.py")

    print("Verifying all remote SHA256 checksums...")
    for f in files_to_verify:
        local_hash = hashlib.sha256((PKG_DIR / f).read_bytes()).hexdigest().lower()
        cmd = f"sha256sum {REMOTE_DIR}/{f}"
        out = run_remote(cmd)
        remote_out = out.strip().split()
        if not remote_out:
            raise RuntimeError(f"Empty remote output for sha256 of {f}")
        remote_hash = remote_out[0].lower()
        if local_hash != remote_hash:
            raise ValueError(f"Checksum mismatch for {f}!\n  Local:  {local_hash}\n  Remote: {remote_hash}")
        print(f"  Checksum PASS: {f} ({local_hash[:16]}...)")

    print("\nExecuting Abaqus 2023 interactive datacheck...")
    cmd_dc = f"bash {REMOTE_DIR}/run_c3_inc88_samemesh_datacheck.sh"
    dc_out = run_remote(cmd_dc)
    print("Datacheck output summary:")
    for line in dc_out.splitlines()[-15:]:
        print(" ", line)

    print("\nRetrieving datacheck outputs...")
    for f in ["M1_C3_SM_INC88_DC.dat", "M1_C3_SM_INC88_DC.msg"]:
        src = f"tu_freiberg:{REMOTE_DIR}/{f}"
        dst = str(PKG_DIR / f)
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"  Downloaded: {f}")
        else:
            print(f"  Note: {f} not present or download failed: {res.stderr}")

    print("\nPackage 121 staged and datacheck completed successfully!")

if __name__ == "__main__":
    main()
