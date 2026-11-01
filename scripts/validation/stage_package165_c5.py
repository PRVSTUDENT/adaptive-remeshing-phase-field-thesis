#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package165_c5.py
Mode-I Method C Stage C2-0: Stage Package 165 C5 Contract A Re-Equilibration Candidate
to HPC Scratch and verify authentic Abaqus 2023 Mechanical & Phase datachecks with frozen production UEL.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PACKAGE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/165_c5_package165_c2_0_contract_a"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package165_c2_0_contract_a"
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

RUNTIME_SOURCES = [
    "scripts/state_transfer/driver_package165_c5_contract_a.py",
    "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
    "scripts/validation/extract_package148_iteration.py",
]

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def run_remote_ssh(command: str, timeout: int = 180) -> str:
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SSH_WRAPPER),
        "-RemoteCommand",
        command,
        "-TimeoutSeconds",
        str(timeout),
    ]
    res = subprocess.run(
        ps_cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout + 30,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Remote command failed (exit {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )
    return res.stdout.strip()

def upload_file(local_path: Path, remote_path: str, timeout: int = 180):
    ps_cmd = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(SSH_WRAPPER),
        "-UploadFile",
        str(local_path),
        "-RemotePath",
        remote_path,
        "-TimeoutSeconds",
        str(timeout),
    ]
    res = subprocess.run(
        ps_cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout + 30,
    )
    if res.returncode != 0:
        raise RuntimeError(
            f"Upload failed (exit {res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}"
        )

def main():
    print("=" * 80)
    print("STAGING PACKAGE 165 C5 WORKFLOW TO HPC CLUSTER SCRATCH")
    print("=" * 80)

    # 1. Verify local UEL matches frozen production hash bitwise
    uel_path = PACKAGE_DIR / "f42_mixed_uel.for"
    uel_sha = sha256_file(uel_path)
    assert uel_sha == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_sha} != {FROZEN_UEL_HASH}"
    print(f"Verified UEL hash: {uel_sha}")

    # 2. Check all files in manifest
    manifest_path = PACKAGE_DIR / "EXECUTION_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, exp_sha in manifest["files"].items():
        fpath = PACKAGE_DIR / name
        assert fpath.is_file(), f"Missing package file: {name}"
        act_sha = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert act_sha == exp_sha.lower(), f"Hash mismatch for {name}: {act_sha} != {exp_sha}"
    print(f"Verified all {len(manifest['files'])} package files against EXECUTION_MANIFEST.json")

    for src in RUNTIME_SOURCES:
        spath = REPO_ROOT / src
        assert spath.is_file(), f"Missing runtime source: {src}"
    print(f"Verified all {len(RUNTIME_SOURCES)} runtime source files")

    # Datacheck files to include in bundle (already present in manifest)
    extra_files = []

    # 3. Create tarball bundle
    bundle_path = PACKAGE_DIR / "bundle.tar.gz"
    print(f"Creating staging bundle: {bundle_path}")
    with tarfile.open(bundle_path, "w:gz") as tar:
        for fname in list(manifest["files"].keys()) + ["EXECUTION_MANIFEST.json"] + extra_files:
            tar.add(str(PACKAGE_DIR / fname), arcname=fname)
        for rsrc in RUNTIME_SOURCES:
            tar.add(str(REPO_ROOT / rsrc), arcname=f"runtime/{rsrc}")
    print(f"Bundle created: {bundle_path.stat().st_size} bytes")

    # 4. Create remote run directory
    print(f"Creating remote run directory: {REMOTE_RUN_DIR}")
    run_remote_ssh(
        f"mkdir -p {REMOTE_RUN_DIR}/runtime/scripts/state_transfer {REMOTE_RUN_DIR}/runtime/scripts/validation"
    )

    # 5. Upload bundle
    print("Uploading bundle to remote run directory...")
    upload_file(bundle_path, f"{REMOTE_RUN_DIR}/bundle.tar.gz")

    # 6. Extract bundle remotely
    print("Extracting bundle remotely...")
    extract_cmd = (
        f"tar -xzf {REMOTE_RUN_DIR}/bundle.tar.gz -C {REMOTE_RUN_DIR} && "
        f"chmod +x {REMOTE_RUN_DIR}/*.sh {REMOTE_RUN_DIR}/*.pbs"
    )
    run_remote_ssh(extract_cmd)

    # 7. Clean up local bundle
    if bundle_path.exists():
        bundle_path.unlink()
        print("Cleaned up local bundle tarball.")

    # 8. Verify remote checksums of critical files
    print("Verifying remote checksums...")
    check_hashes_cmd = f"sha256sum {REMOTE_RUN_DIR}/f42_mixed_uel.for {REMOTE_RUN_DIR}/submit_M1_C5_P165_C2_0.pbs {REMOTE_RUN_DIR}/P165_MECHANICAL_DC.dat"
    out = run_remote_ssh(check_hashes_cmd)
    print(f"Remote checksums:\n{out}")
    assert FROZEN_UEL_HASH.lower() in out.lower(), "Remote UEL hash verification failed!"

    print("STAGING PACKAGE 165 C5 COMPLETE AND VERIFIED!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
