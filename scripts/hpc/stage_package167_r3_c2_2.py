#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_package167_r3_c2_2.py
Deploy Package 167-R3 (Stage C2-2 +5 nm Forward Continuation on C5 Mesh)
to cluster scratch directory /scratch9/pr21vyci/runs/mode1_c5_package167_r3_c2_2_continuation,
execute compute-node datachecks on representative runtime-generated mechanical and phase decks,
retrieve datacheck DAT files, and finalize manifests.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import hashlib
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PACKAGE_DIR = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c5_package167_r3_c2_2_continuation"
SSH_WRAPPER = REPO_ROOT / ".agents/scripts/Invoke-GuardedSsh.ps1"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_02_HASH = "8201D8200A12C8A493ABA8550DA7D66DB9301C2389A9EA1409BCB5B9E57B4FEA"

RUNTIME_SOURCES = [
    "scripts/state_transfer/driver_package167_c5_continuation.py",
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
    res = subprocess.run(ps_cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
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
    res = subprocess.run(ps_cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError(f"Remote upload failed ({res.returncode}):\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")


def run_remote_download(remote_path: str, local_path: Path, timeout: int = 180):
    config_path = Path(os.environ["USERPROFILE"]) / ".ssh/codex_config"
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
    print("=== Stage Package 167-R3 to Cluster Scratch ===")

    # 1. Assemble base files and initial manifests
    from scripts.state_transfer.build_package167_r3_continuation import build_c2_2_r3_package
    b_res = build_c2_2_r3_package()
    print("Package 167-R3 initial assembly:", b_res["status"])

    # 1a. Verify frozen production UEL
    uel_local = PACKAGE_DIR / "f42_mixed_uel.for"
    actual_uel_hash = sha256_file(uel_local)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"1a. Verified frozen production UEL hash: {actual_uel_hash}")

    # 1b. Verify Checkpoint 02
    chkpt_local = PACKAGE_DIR / "initial_checkpoint_02.json"
    actual_chkpt_hash = sha256_file(chkpt_local)
    assert actual_chkpt_hash == CHECKPOINT_02_HASH, f"Checkpoint 02 hash mismatch: {actual_chkpt_hash} != {CHECKPOINT_02_HASH}"
    print(f"1b. Verified authentic Checkpoint 02 hash: {actual_chkpt_hash}")

    # 1c. Verify transitive runtime import closure
    from scripts.validation.verify_package167_runtime_imports import verify_transitive_closure, ENTRY_POINTS
    closure = verify_transitive_closure(RUNTIME_SOURCES, ENTRY_POINTS)
    assert closure["closure_complete"], f"Runtime import closure incomplete: {closure['missing']}"
    print("1c. Verified complete transitive runtime import closure for Package 167-R3.")

    # 2. Package tarball creation
    tar_path = REPO_ROOT / "models/pandey_kumar_mode1/package167_r3_staging.tar.gz"
    print(f"\n2. Creating staging tarball {tar_path.name}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in PACKAGE_DIR.iterdir():
            if f.is_file() and not f.name.endswith(".dat"):
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

        remote_tar = f"{REMOTE_RUN_DIR}/package167_r3_staging.tar.gz"
        print(f"Uploading tarball to {remote_tar}...")
        run_remote_upload(tar_path, remote_tar, timeout=120)

        # 4. Extract remote tarball
        print(f"\n4. Extracting remote tarball...")
        extract_cmd = f"tar -C {REMOTE_RUN_DIR} -xzf {remote_tar} && rm -f {remote_tar} && chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh {REMOTE_RUN_DIR}/submit_M1_C5_P167_R3_C2_2.pbs"
        run_remote_ssh(extract_cmd)

        # 5. Execute Abaqus Datachecks on Remote Cluster for both representative runtime subproblems
        print("\n5. Executing Mechanical and Phase Abaqus datachecks on cluster...")
        dc_mech_out = run_remote_ssh(f"{REMOTE_RUN_DIR}/run_datacheck.sh mechanical", timeout=300)
        print("Mechanical Datacheck Output:\n", dc_mech_out)
        assert "AUTHENTIC_DATACHECK_PASS" in dc_mech_out, "Mechanical datacheck failed"

        dc_phase_out = run_remote_ssh(f"{REMOTE_RUN_DIR}/run_datacheck.sh phase", timeout=300)
        print("Phase Datacheck Output:\n", dc_phase_out)
        assert "AUTHENTIC_DATACHECK_PASS" in dc_phase_out, "Phase datacheck failed"

        # 6. Retrieve DAT files to local directory
        print("\n6. Downloading generated DAT files...")
        local_mech_dat = PACKAGE_DIR / "P167_R3_MECHANICAL_DC.dat"
        local_phase_dat = PACKAGE_DIR / "P167_R3_PHASE_DC.dat"
        run_remote_download(f"{REMOTE_RUN_DIR}/P167_R3_MECHANICAL_DC.dat", local_mech_dat, timeout=60)
        run_remote_download(f"{REMOTE_RUN_DIR}/P167_R3_PHASE_DC.dat", local_phase_dat, timeout=60)
        print(f"Downloaded P167_R3_MECHANICAL_DC.dat ({local_mech_dat.stat().st_size} bytes)")
        print(f"Downloaded P167_R3_PHASE_DC.dat ({local_phase_dat.stat().st_size} bytes)")

        # 7. Finalize local manifests with DAT file hashes
        print("\n7. Finalizing manifests with DAT hashes...")
        build_c2_2_r3_package()

        # 8. Upload finalized manifests to remote cluster
        print("\n8. Uploading finalized manifests to remote cluster...")
        run_remote_upload(PACKAGE_DIR / "PACKAGE_MANIFEST.json", f"{REMOTE_RUN_DIR}/PACKAGE_MANIFEST.json", timeout=60)
        run_remote_upload(PACKAGE_DIR / "EXECUTION_MANIFEST.json", f"{REMOTE_RUN_DIR}/EXECUTION_MANIFEST.json", timeout=60)

        # 9. Remote file verification
        print("\n9. Verifying remote staging files...")
        verify_cmd = f"ls -la {REMOTE_RUN_DIR} && ls -la {REMOTE_RUN_DIR}/runtime/scripts/state_transfer"
        out = run_remote_ssh(verify_cmd)
        print("Remote directory contents:\n" + out)
        print("\n=== Package 167-R3 Staging and Datachecks Complete ===")
    finally:
        if tar_path.is_file():
            tar_path.unlink()


if __name__ == "__main__":
    stage_and_datacheck()
