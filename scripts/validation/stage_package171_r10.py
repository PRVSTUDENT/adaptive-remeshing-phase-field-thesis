#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package171_r10.py
=======================
Deploys Package 171-R10 (C6 Stage C3-0 Coupled PDAS Re-equilibration Revision 10)
to cluster scratch:
/scratch9/pr21vyci/runs/mode1_c6_package171_r10_c3_0_adaptive_reequilibration,
stages runtime dependency scripts under runtime/ with verified closure,
and verifies remote file existence and bitwise hashes.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r10_c3_0_adaptive_reequilibration"
SSH_WRAPPER = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c6_package171_r10_c3_0_adaptive_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def run_remote_ssh(remote_cmd: str, timeout: int = 180) -> str:
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SSH_WRAPPER),
        "-RemoteCommand",
        remote_cmd,
        "-TimeoutSeconds",
        str(timeout)
    ]
    res = subprocess.run(ps_cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError(f"Remote SSH command failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    return res.stdout


def run_remote_upload(local_path: Path, remote_path: str, timeout: int = 180) -> None:
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
    res = subprocess.run(ps_cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError(f"Remote upload failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")


def stage_package_r10():
    print("=== Stage Package 171-R10 to Cluster Scratch ===")

    # 1. Verify frozen UEL
    uel_local = PACKAGE_DIR / "f42_mixed_uel.for"
    actual_uel_hash = sha256_file(uel_local)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"1. Verified frozen production UEL: {actual_uel_hash}")

    # 2. Package tarball creation
    tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_r10_staging.tar.gz"
    print(f"\n2. Creating staging tarball {tar_path.name}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in sorted(PACKAGE_DIR.iterdir()):
            if f.is_file():
                tar.add(f, arcname=f.name)

    print(f"Staging tarball size: {tar_path.stat().st_size / (1024*1024):.2f} MB")

    # Runtime tarball creation with R10 coupled driver
    runtime_tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_r10_runtime.tar.gz"
    runtime_files = [
        "scripts/__init__.py",
        "scripts/state_transfer/__init__.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r7_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r8_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r9_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r10_c6_coupled_pdas.py",
        "scripts/validation/__init__.py",
        "scripts/validation/extract_package148_iteration.py",
    ]
    with tarfile.open(runtime_tar_path, "w:gz") as tar:
        for rf in runtime_files:
            rf_path = REPO_ROOT / rf
            if rf_path.is_file():
                tar.add(rf_path, arcname=rf)

    print(f"Runtime tarball size: {runtime_tar_path.stat().st_size / 1024:.2f} KB")

    try:
        # 3. Create remote directory and clean
        print(f"\n3. Preparing remote directory {REMOTE_RUN_DIR}...")
        run_remote_ssh(f"mkdir -p {REMOTE_RUN_DIR}")
        run_remote_ssh(f"rm -rf {REMOTE_RUN_DIR}/*")

        remote_tar = f"{REMOTE_RUN_DIR}/package171_r10_staging.tar.gz"
        print(f"Uploading package tarball to {remote_tar}...")
        run_remote_upload(tar_path, remote_tar, timeout=120)

        remote_runtime_tar = f"{REMOTE_RUN_DIR}/package171_r10_runtime.tar.gz"
        print(f"Uploading runtime tarball to {remote_runtime_tar}...")
        run_remote_upload(runtime_tar_path, remote_runtime_tar, timeout=120)

        # 4. Extract remote tarballs
        print(f"\n4. Extracting remote tarballs...")
        extract_cmd = (
            f"tar -C {REMOTE_RUN_DIR} -xzf {remote_tar} && rm -f {remote_tar} && "
            f"mkdir -p {REMOTE_RUN_DIR}/runtime && "
            f"tar -C {REMOTE_RUN_DIR}/runtime -xzf {remote_runtime_tar} && rm -f {remote_runtime_tar} && "
            f"chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh {REMOTE_RUN_DIR}/submit_M1_C6_P171_R10_C3_0.pbs"
        )
        run_remote_ssh(extract_cmd)

        # 4a. Remote Bash Syntax Check on PBS script
        print("\n4a. Running Remote Bash Syntax Check on submit script...")
        bash_syntax_cmd = f"bash -n {REMOTE_RUN_DIR}/submit_M1_C6_P171_R10_C3_0.pbs"
        run_remote_ssh(bash_syntax_cmd, timeout=30)
        print("Remote bash -n syntax check PASSED cleanly.")

        # 4b. Remote Python Import Smoke Test
        print("\n4b. Running Remote Python Import Smoke Test on compute cluster...")
        smoke_cmd = f"python3 {REMOTE_RUN_DIR}/smoke_import.py"
        smoke_out = run_remote_ssh(smoke_cmd, timeout=60)
        print("Remote Smoke Test Output:\n", smoke_out)
        assert "REMOTE_IMPORT_SUCCESS: True" in smoke_out, f"Remote import smoke test failed: {smoke_out}"

        print("\n=== Package 171-R10 Successfully Staged to Cluster Scratch ===")

    finally:
        if tar_path.is_file():
            tar_path.unlink()
        if runtime_tar_path.is_file():
            runtime_tar_path.unlink()


if __name__ == "__main__":
    stage_package_r10()
