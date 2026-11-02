#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package166_r3.py
Deploy Package 166-R3 (Non-Accumulating History with Schema Repair & Post-Phase Damage Gate)
to cluster scratch directory /scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history.
"""

import hashlib
import os
import subprocess
import tarfile
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PACKAGE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/166_c5_package166_r3_c2_0_nonaccumulating_history"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package166_r3_c2_0_nonaccumulating_history"
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

RUNTIME_SOURCES = [
    "scripts/state_transfer/driver_package166_r2_c5_nonaccumulating_history.py",
    "scripts/validation/extract_package148_iteration.py",
    "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
]

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def run_remote_ssh(command: str, timeout: int = 180) -> str:
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SSH_WRAPPER),
        "-RemoteCommand",
        command,
        "-TimeoutSeconds",
        str(timeout)
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Remote SSH command failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res.stdout

def run_remote_upload(local_path: Path, remote_path: str, timeout: int = 180):
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SSH_WRAPPER),
        "-UploadFile",
        str(local_path),
        "-RemotePath",
        remote_path,
        "-TimeoutSeconds",
        str(timeout)
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Remote upload failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")

def main():
    print("=== Stage Package 166-R3 to Cluster Scratch ===")

    # 1. Verify frozen production UEL
    uel_local = PACKAGE_DIR / "f42_mixed_uel.for"
    actual_uel_hash = sha256_file(uel_local)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"1. Verified frozen production UEL hash: {actual_uel_hash}")

    # 2. Package tarball creation
    tar_path = REPO_ROOT / "models/pandey_kumar_mode1/package166_r3_staging.tar.gz"
    print(f"\n2. Creating staging tarball {tar_path.name}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in PACKAGE_DIR.iterdir():
            if f.is_file():
                tar.add(f, arcname=f.name)
        for rs in RUNTIME_SOURCES:
            src_p = REPO_ROOT / rs
            tar.add(src_p, arcname=f"runtime/{rs}")
    print(f"Staging tarball size: {tar_path.stat().st_size / (1024*1024):.2f} MB")

    try:
        # 3. Create remote directory and clean
        print(f"\n3. Preparing remote directory {REMOTE_RUN_DIR}...")
        run_remote_ssh(f"mkdir -p {REMOTE_RUN_DIR}")
        run_remote_ssh(f"rm -rf {REMOTE_RUN_DIR}/*")

        remote_tar = f"{REMOTE_RUN_DIR}/package166_r3_staging.tar.gz"
        print(f"Uploading tarball to {remote_tar}...")
        run_remote_upload(tar_path, remote_tar, timeout=120)

        # 4. Extract remote tarball
        print(f"\n4. Extracting remote tarball...")
        extract_cmd = f"cd {REMOTE_RUN_DIR} && tar -xzf package166_r3_staging.tar.gz && rm -f package166_r3_staging.tar.gz && chmod +x run_datacheck.sh submit_M1_C5_P166_R3_C2_0.pbs"
        run_remote_ssh(extract_cmd)

        # 5. Remote file verification
        print("\n5. Verifying remote staging files...")
        verify_cmd = f"cd {REMOTE_RUN_DIR} && ls -la"
        out = run_remote_ssh(verify_cmd)
        print("Remote directory contents:\n" + out)
        print("\n=== Package 166-R3 Staging Complete ===")
    finally:
        if tar_path.is_file():
            tar_path.unlink()

if __name__ == "__main__":
    main()
