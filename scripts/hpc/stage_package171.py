#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package171.py
===================
Deploys Package 171 (C6 Stage C3-0 Coupled PDAS Re-equilibration) to cluster scratch:
/scratch9/pr21vyci/runs/mode1_c6_package171_c3_0_reequilibration,
stages runtime dependency scripts under runtime/,
executes compute-node datachecks on P171_MECHANICAL_DC.inp and P171_PHASE_DC.inp,
retrieves DAT/MSG files, and verifies authentic datacheck completion.
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
PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_c3_0_reequilibration"
SSH_WRAPPER = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c6_package171_c3_0_reequilibration"
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


def run_remote_download(remote_path: str, local_path: Path, timeout: int = 180) -> None:
    config_path = Path(os.environ["USERPROFILE"]) / ".ssh" / "codex_config"
    cmd = [
        "scp.exe",
        "-B",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=20",
        "-F", str(config_path),
        f"tu_freiberg:{remote_path}",
        str(local_path)
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Remote download failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")


def stage_and_datacheck():
    print("=== Stage Package 171 to Cluster Scratch ===")

    # 1. Verify frozen UEL
    uel_local = PACKAGE_DIR / "f42_mixed_uel.for"
    actual_uel_hash = sha256_file(uel_local)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"1. Verified frozen production UEL: {actual_uel_hash}")

    # 2. Package tarball creation
    tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_staging.tar.gz"
    print(f"\n2. Creating staging tarball {tar_path.name}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in PACKAGE_DIR.iterdir():
            if f.is_file() and not f.name.endswith(".dat"):
                tar.add(f, arcname=f.name)

    print(f"Staging tarball size: {tar_path.stat().st_size / (1024*1024):.2f} MB")

    # Runtime tarball creation
    runtime_tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_runtime.tar.gz"
    runtime_files = [
        "scripts/__init__.py",
        "scripts/state_transfer/__init__.py",
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
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

        remote_tar = f"{REMOTE_RUN_DIR}/package171_staging.tar.gz"
        print(f"Uploading package tarball to {remote_tar}...")
        run_remote_upload(tar_path, remote_tar, timeout=120)

        remote_runtime_tar = f"{REMOTE_RUN_DIR}/package171_runtime.tar.gz"
        print(f"Uploading runtime tarball to {remote_runtime_tar}...")
        run_remote_upload(runtime_tar_path, remote_runtime_tar, timeout=120)

        # 4. Extract remote tarballs
        print(f"\n4. Extracting remote tarballs...")
        extract_cmd = (
            f"tar -C {REMOTE_RUN_DIR} -xzf {remote_tar} && rm -f {remote_tar} && "
            f"mkdir -p {REMOTE_RUN_DIR}/runtime && "
            f"tar -C {REMOTE_RUN_DIR}/runtime -xzf {remote_runtime_tar} && rm -f {remote_runtime_tar} && "
            f"chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh {REMOTE_RUN_DIR}/submit_M1_C6_P171_C3_0.pbs"
        )
        run_remote_ssh(extract_cmd)

        # 5. Execute Datacheck on Cluster
        print("\n5. Executing Abaqus compute-node datacheck on cluster...")
        dc_out = run_remote_ssh(f"{REMOTE_RUN_DIR}/run_datacheck.sh", timeout=300)
        print("Datacheck Output:\n", dc_out)
        assert "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS" in dc_out, "Mechanical datacheck did not pass"
        assert "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS" in dc_out, "Phase datacheck did not pass"

        # 6. Retrieve DAT and MSG files
        print("\n6. Downloading generated DAT and MSG files...")
        local_mech_dat = PACKAGE_DIR / "P171_MECHANICAL_DC.dat"
        local_mech_msg = PACKAGE_DIR / "P171_MECHANICAL_DC.msg"
        local_phase_dat = PACKAGE_DIR / "P171_PHASE_DC.dat"
        local_phase_msg = PACKAGE_DIR / "P171_PHASE_DC.msg"

        run_remote_download(f"{REMOTE_RUN_DIR}/P171_MECHANICAL_DC.dat", local_mech_dat, timeout=60)
        run_remote_download(f"{REMOTE_RUN_DIR}/P171_MECHANICAL_DC.msg", local_mech_msg, timeout=60)
        run_remote_download(f"{REMOTE_RUN_DIR}/P171_PHASE_DC.dat", local_phase_dat, timeout=60)
        run_remote_download(f"{REMOTE_RUN_DIR}/P171_PHASE_DC.msg", local_phase_msg, timeout=60)

        mech_dat_hash = sha256_file(local_mech_dat)
        phase_dat_hash = sha256_file(local_phase_dat)
        print(f"Downloaded Mechanical DAT ({local_mech_dat.stat().st_size} bytes, SHA-256: {mech_dat_hash})")
        print(f"Downloaded Phase DAT ({local_phase_dat.stat().st_size} bytes, SHA-256: {phase_dat_hash})")

        # 7. Finalize local manifests with DAT file hashes
        print("\n7. Finalizing manifests with DAT hashes...")
        pkg_manifest_path = PACKAGE_DIR / "PACKAGE_MANIFEST.json"
        with open(pkg_manifest_path, "r", encoding="utf-8") as f:
            pm = json.load(f)
        pm["files"]["P171_MECHANICAL_DC.dat"] = mech_dat_hash.lower()
        pm["files"]["P171_PHASE_DC.dat"] = phase_dat_hash.lower()
        with open(pkg_manifest_path, "w", encoding="utf-8") as f:
            json.dump(pm, f, indent=2)

        auth_path = PACKAGE_DIR / "M1_C6_PACKAGE171_AUTHORIZATION.json"
        with open(auth_path, "r", encoding="utf-8") as f:
            am = json.load(f)
        am["files"]["P171_MECHANICAL_DC.dat"] = mech_dat_hash.lower()
        am["files"]["P171_PHASE_DC.dat"] = phase_dat_hash.lower()
        am["files"]["PACKAGE_MANIFEST.json"] = sha256_file(pkg_manifest_path).lower()
        with open(auth_path, "w", encoding="utf-8") as f:
            json.dump(am, f, indent=2)

        exec_manifest_path = PACKAGE_DIR / "EXECUTION_MANIFEST.json"
        with open(exec_manifest_path, "w", encoding="utf-8") as f:
            json.dump(am, f, indent=2)

        # 8. Upload finalized manifests to remote cluster
        print("\n8. Uploading finalized manifests to remote cluster...")
        run_remote_upload(pkg_manifest_path, f"{REMOTE_RUN_DIR}/PACKAGE_MANIFEST.json", timeout=60)
        run_remote_upload(auth_path, f"{REMOTE_RUN_DIR}/M1_C6_PACKAGE171_AUTHORIZATION.json", timeout=60)
        run_remote_upload(exec_manifest_path, f"{REMOTE_RUN_DIR}/EXECUTION_MANIFEST.json", timeout=60)

        # 9. Remote file verification
        print("\n9. Verifying remote staging files...")
        out = run_remote_ssh(f"ls -la {REMOTE_RUN_DIR}")
        print("Remote directory contents:\n" + out)
        print("\n=== Package 171 Staging and Datacheck Complete ===")
        return {
            "status": "DATACHECK_COMPLETE",
            "mech_dat_sha256": mech_dat_hash,
            "phase_dat_sha256": phase_dat_hash,
            "auth_sha256": sha256_file(auth_path)
        }
    finally:
        if tar_path.is_file():
            tar_path.unlink()
        if runtime_tar_path.is_file():
            runtime_tar_path.unlink()


if __name__ == "__main__":
    stage_and_datacheck()
