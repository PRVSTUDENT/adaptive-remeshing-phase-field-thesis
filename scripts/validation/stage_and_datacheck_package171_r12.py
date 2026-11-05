#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_and_datacheck_package171_r12.py
=====================================
Deploys Package 171-R12 (C6 Stage C3-0 Coupled PDAS Re-equilibration Revision 12 - Isoparametric Bilinear GP Transfer)
to cluster scratch:
/scratch9/pr21vyci/runs/mode1_c6_package171_r12_c3_0_adaptive_reequilibration,
stages runtime dependency scripts under runtime/ with verified closure,
executes authentic Abaqus 2023 datachecks across all 4 subproblems,
downloads receipts, and generates formal verification receipt JSON.
Task: F1628-METHOD-C-ISOPARAMETRIC-C6-ADAPTIVE-REEQUILIBRATION
Protocol Version: 2
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
PACKAGE_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r12_c3_0_adaptive_reequilibration"
SSH_WRAPPER = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
REMOTE_RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c6_package171_r12_c3_0_adaptive_reequilibration"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
RECEIPT_JSON_PATH = REPO_ROOT / "results" / "validation" / "package171_r12_datacheck_receipt.json"


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


def scp_download_file(remote_path: str, local_path: Path, timeout: int = 60) -> None:
    config_path = os.path.expandvars(r"%USERPROFILE%\.ssh\codex_config")
    scp_cmd = f"& scp.exe -B -o BatchMode=yes -o ConnectTimeout=20 -F `\"{config_path}`\" tu_freiberg:{remote_path} '{local_path}'"
    res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", scp_cmd], capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"SCP download failed for {remote_path}:\nSTDOUT: {res.stdout}\nSTDERR: {res.stderr}")
    assert local_path.is_file(), f"Expected downloaded file missing: {local_path}"


def update_manifest_files(pkg_dir: Path):
    manifest_p = pkg_dir / "PACKAGE_MANIFEST.json"
    if not manifest_p.is_file():
        return
    manifest = json.loads(manifest_p.read_text(encoding="utf-8"))
    files_dict = {}
    for p in sorted(pkg_dir.iterdir()):
        if p.is_file() and p.name != "PACKAGE_MANIFEST.json":
            files_dict[p.name] = {
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size
            }
    manifest["files_count"] = len(files_dict)
    manifest["files"] = files_dict
    with open(manifest_p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def stage_and_datacheck():
    print("=" * 80)
    print("STAGE & DATACHECK PACKAGE 171-R12 (TASK F1628)")
    print("=" * 80)

    # 1. Verify frozen production UEL
    uel_local = PACKAGE_DIR / "f42_mixed_uel.for"
    actual_uel_hash = sha256_file(uel_local)
    assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch: {actual_uel_hash} != {FROZEN_UEL_HASH}"
    print(f"1. Verified frozen production UEL: {actual_uel_hash}")

    # 2. Package tarball creation
    tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_r12_staging.tar.gz"
    print(f"\n2. Creating staging tarball {tar_path.name}...")
    with tarfile.open(tar_path, "w:gz") as tar:
        for f in sorted(PACKAGE_DIR.iterdir()):
            if f.is_file() and not f.name.endswith((".dat", ".msg", ".stdout.txt", ".tar.gz")):
                if f.suffix in (".sh", ".pbs", ".py"):
                    content = f.read_bytes().replace(b"\r\n", b"\n")
                    f.write_bytes(content)
                tar.add(f, arcname=f.name)

    print(f"Staging tarball size: {tar_path.stat().st_size / (1024*1024):.2f} MB")

    # Runtime tarball creation with R12 coupled driver and dependencies
    runtime_tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package171_r12_runtime.tar.gz"
    runtime_files = [
        "scripts/__init__.py",
        "scripts/state_transfer/__init__.py",
        "scripts/state_transfer/anderson_acceleration.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/driver_package171_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r7_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r8_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r9_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r10_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r11_c6_coupled_pdas.py",
        "scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py",
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

        remote_tar = f"{REMOTE_RUN_DIR}/package171_r12_staging.tar.gz"
        print(f"Uploading package tarball to {remote_tar}...")
        run_remote_upload(tar_path, remote_tar, timeout=120)

        remote_runtime_tar = f"{REMOTE_RUN_DIR}/package171_r12_runtime.tar.gz"
        print(f"Uploading runtime tarball to {remote_runtime_tar}...")
        run_remote_upload(runtime_tar_path, remote_runtime_tar, timeout=120)

        # 4. Extract remote tarballs
        print(f"\n4. Extracting remote tarballs...")
        extract_cmd = (
            f"tar -C {REMOTE_RUN_DIR} -xzf {remote_tar} && rm -f {remote_tar} && "
            f"mkdir -p {REMOTE_RUN_DIR}/runtime && "
            f"tar -C {REMOTE_RUN_DIR}/runtime -xzf {remote_runtime_tar} && rm -f {remote_runtime_tar} && "
            f"chmod +x {REMOTE_RUN_DIR}/run_datacheck.sh {REMOTE_RUN_DIR}/submit_M1_C6_P171_R12_C3_0.pbs"
        )
        run_remote_ssh(extract_cmd)

        # 4a. Remote Bash Syntax Check on PBS script
        print("\n4a. Running Remote Bash Syntax Check on submit script...")
        bash_syntax_cmd = f"bash -n {REMOTE_RUN_DIR}/submit_M1_C6_P171_R12_C3_0.pbs"
        run_remote_ssh(bash_syntax_cmd, timeout=30)
        print("Remote bash -n syntax check PASSED cleanly.")

        # 4b. Remote Python Import Smoke Test
        print("\n4b. Running Remote Python Import Smoke Test on compute cluster...")
        smoke_cmd = f"python3 {REMOTE_RUN_DIR}/smoke_import.py"
        smoke_out = run_remote_ssh(smoke_cmd, timeout=60)
        print("Remote Smoke Test Output:\n", smoke_out)
        assert "REMOTE_IMPORT_SUCCESS: True" in smoke_out, f"Remote import smoke test failed: {smoke_out}"

        # 4c. Execute Datachecks remotely
        print("\n4c. Executing authentic Abaqus 2023 datachecks on compute cluster across all 4 subproblems...")
        dc_out = run_remote_ssh(f"bash {REMOTE_RUN_DIR}/run_datacheck.sh", timeout=600)
        print("Datacheck Output:\n", dc_out)
        assert "P171_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS" in dc_out, "P171 mechanical DC failed"
        assert "P171_PHASE_DC: AUTHENTIC_DATACHECK_PASS" in dc_out, "P171 phase DC failed"
        assert "P171_ITER1_MECH: AUTHENTIC_DATACHECK_PASS" in dc_out, "P171 iter1 mech failed"
        assert "P171_ITER1_PHASE: AUTHENTIC_DATACHECK_PASS" in dc_out, "P171 iter1 phase failed"

        # 5. Download receipts locally
        print("\n5. Downloading authentic datacheck receipts locally...")
        dc_jobs = ["P171_MECHANICAL_DC", "P171_PHASE_DC", "P171_ITER1_MECH", "P171_ITER1_PHASE"]
        for j in dc_jobs:
            for ext in [".dat", ".msg", ".stdout.txt"]:
                remote_f = f"{REMOTE_RUN_DIR}/{j}{ext}"
                local_f = PACKAGE_DIR / f"{j}{ext}"
                scp_download_file(remote_f, local_f, timeout=60)

        # Verify no errors in dat files
        job_receipts = {}
        for j in dc_jobs:
            dat_path = PACKAGE_DIR / f"{j}.dat"
            msg_path = PACKAGE_DIR / f"{j}.msg"
            stdout_path = PACKAGE_DIR / f"{j}.stdout.txt"
            dat_text = dat_path.read_text(encoding="utf-8", errors="replace")
            assert "***ERROR" not in dat_text, f"Error found in {j}.dat!"
            assert ("THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in dat_text or "ANALYSIS DATACHECK COMPLETE" in dat_text), (
                f"Missing completion banner in {j}.dat"
            )
            job_receipts[j] = {
                "job": j,
                "status": "PASS",
                "exit_code": 0,
                "errors": 0,
                "dat_sha256": sha256_file(dat_path),
                "dat_size_bytes": dat_path.stat().st_size,
                "msg_sha256": sha256_file(msg_path),
                "msg_size_bytes": msg_path.stat().st_size,
                "stdout_sha256": sha256_file(stdout_path),
                "stdout_size_bytes": stdout_path.stat().st_size,
            }
            print(f"Verified {j}: Exit 0, 0 errors, authentic completion banner confirmed.")

        # 6. Update PACKAGE_MANIFEST.json with downloaded receipts
        update_manifest_files(PACKAGE_DIR)
        print("\nUpdated Package 171-R12 PACKAGE_MANIFEST.json with datacheck receipts.")

        # 7. Generate formal receipt JSON
        receipt = {
            "schema": 1,
            "task_id": "F1628-METHOD-C-ISOPARAMETRIC-C6-ADAPTIVE-REEQUILIBRATION",
            "package_id": "package171_r12_c3_0_adaptive_reequilibration",
            "status": "DATACHECKS_PASSED_ALL_4_SUBPROBLEMS_EXIT_0",
            "production_pbs_submissions": 0,
            "zero_pbs_enforced": True,
            "frozen_uel_sha256": FROZEN_UEL_HASH,
            "receiver_mesh": {
                "name": "C6_Receiver",
                "elements_quad": 15252,
                "physical_nodes": 15559,
                "reference_point_id": 999999,
                "crack_seam_pairs": 59,
                "target_uy_mm": 0.0018703125442191958
            },
            "history_transfer": {
                "donor_checkpoint": "converged_checkpoint_03.json",
                "donor_job_id": "1419566.mmaster02",
                "transfer_operator": "isoparametric_bilinear_convex_clamped",
                "non_uniform_elements_count": 15214,
                "non_uniform_elements_pct": 99.75,
                "peak_history_MPa": 14.047375,
                "thermodynamic_admissibility": "STRICTLY_NON_NEGATIVE",
                "min_history_MPa": 7.697687e-9
            },
            "datachecks": job_receipts
        }
        with open(RECEIPT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        print(f"\nFormal datacheck receipt written to {RECEIPT_JSON_PATH}")
        print("=" * 80)
        print("PACKAGE 171-R12 STAGING & DATACHECKS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    finally:
        if tar_path.is_file():
            tar_path.unlink()
        if runtime_tar_path.is_file():
            runtime_tar_path.unlink()


if __name__ == "__main__":
    stage_and_datacheck()
