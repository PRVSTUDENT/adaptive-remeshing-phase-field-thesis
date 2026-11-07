#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_and_datacheck_same_mesh_controls.py
=========================================
Deploys and qualifies the paired same-mesh control experiment packages on compute cluster scratch:
- Package 172 (Arm 1: Control Old - Element-Averaged GP History, 6.35 MPa perturbation)
  Remote: /scratch9/pr21vyci/runs/mode1_c5_package172_old_control
- Package 173 (Arm 2: Control Corrected - Hardened Isoparametric GP History, < 1e-12 MPa error)
  Remote: /scratch9/pr21vyci/runs/mode1_c5_package173_corrected_control

Execution Policy:
- Strictly 0 production solver PBS submissions authorized under Task F1623 (zero_pbs_enforced = True).
- Executes authentic Abaqus 2023 interactive mechanical and phase datachecks on compute cluster.
- Verifies Exit 0, 0 errors, and authentic completion banners for all 8 subproblems (preliminary + dynamic iter1):
  * P172_MECHANICAL_DC, P172_PHASE_DC, P172_ITER1_MECH, P172_ITER1_PHASE
  * P173_MECHANICAL_DC, P173_PHASE_DC, P173_ITER1_MECH, P173_ITER1_PHASE
- Fetches authentic receipts (.dat, .msg, .stdout.txt) and generates formal JSON qualification receipt.
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
PKG172_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "172_c5_same_mesh_old_control"
PKG173_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "173_c5_same_mesh_corrected_control"
RECEIPT_PATH = REPO_ROOT / "results" / "validation" / "same_mesh_control_datacheck_receipt.json"
SSH_WRAPPER = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"

REMOTE_DIR_172 = "/scratch9/pr21vyci/runs/mode1_c5_package172_old_control"
REMOTE_DIR_173 = "/scratch9/pr21vyci/runs/mode1_c5_package173_corrected_control"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

RUNTIME_SOURCES = [
    "scripts/__init__.py",
    "scripts/state_transfer/__init__.py",
    "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
    "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
    "scripts/state_transfer/isoparametric_gp_transfer.py",
    "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
    "scripts/state_transfer/driver_same_mesh_control_pdas.py",
    "scripts/validation/extract_package148_iteration.py",
]


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
    manifest["files"] = files_dict
    with open(manifest_p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def stage_and_datacheck():
    print("=" * 80)
    print("STAGING & DATACHECKING PAIRED SAME-MESH CONTROLS (TASK F1627)")
    print("=" * 80)

    # 1. Verify frozen production UEL
    for pkg_dir, label in [(PKG172_DIR, "Package 172"), (PKG173_DIR, "Package 173")]:
        uel_path = pkg_dir / "f42_mixed_uel.for"
        assert uel_path.is_file(), f"f42_mixed_uel.for missing in {label}"
        uel_hash = sha256_file(uel_path)
        assert uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch in {label}: {uel_hash} != {FROZEN_UEL_HASH}"
        print(f"1. Verified frozen production UEL in {label}: {uel_hash}")

    # 2. Create staging tarballs
    tar172_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package172_staging.tar.gz"
    tar173_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "package173_staging.tar.gz"
    runtime_tar_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "same_mesh_controls_runtime.tar.gz"

    print(f"\n2. Creating staging tarballs...")
    with tarfile.open(tar172_path, "w:gz") as tar:
        for f in sorted(PKG172_DIR.iterdir()):
            if f.is_file() and not f.name.endswith((".dat", ".msg", ".stdout.txt")):
                tar.add(f, arcname=f.name)
    print(f"  Package 172 tarball: {tar172_path.stat().st_size / (1024*1024):.2f} MB")

    with tarfile.open(tar173_path, "w:gz") as tar:
        for f in sorted(PKG173_DIR.iterdir()):
            if f.is_file() and not f.name.endswith((".dat", ".msg", ".stdout.txt")):
                tar.add(f, arcname=f.name)
    print(f"  Package 173 tarball: {tar173_path.stat().st_size / (1024*1024):.2f} MB")

    with tarfile.open(runtime_tar_path, "w:gz") as tar:
        for rf in RUNTIME_SOURCES:
            rf_path = REPO_ROOT / rf
            if rf_path.is_file():
                tar.add(rf_path, arcname=rf)
    print(f"  Runtime tarball: {runtime_tar_path.stat().st_size / 1024:.2f} KB")

    try:
        results = {}

        # 3. Stage and Datacheck Arm 1: Package 172 (Control Old)
        print("\n" + "-" * 70)
        print("STAGE & DATACHECK: ARM 1 (PACKAGE 172 - CONTROL OLD)")
        print("-" * 70)
        run_remote_ssh(f"mkdir -p {REMOTE_DIR_172}")
        run_remote_ssh(f"rm -rf {REMOTE_DIR_172}/*")

        rem_tar_172 = f"{REMOTE_DIR_172}/package172_staging.tar.gz"
        rem_rt_172 = f"{REMOTE_DIR_172}/same_mesh_controls_runtime.tar.gz"
        print(f"Uploading {tar172_path.name}...")
        run_remote_upload(tar172_path, rem_tar_172, timeout=120)
        print(f"Uploading {runtime_tar_path.name}...")
        run_remote_upload(runtime_tar_path, rem_rt_172, timeout=120)

        extract_cmd_172 = (
            f"tar -C {REMOTE_DIR_172} -xzf {rem_tar_172} && rm -f {rem_tar_172} && "
            f"mkdir -p {REMOTE_DIR_172}/runtime && "
            f"tar -C {REMOTE_DIR_172}/runtime -xzf {rem_rt_172} && rm -f {rem_rt_172} && "
            f"chmod +x {REMOTE_DIR_172}/run_datacheck.sh {REMOTE_DIR_172}/submit_M1_C5_P172_OLD_CONTROL.pbs"
        )
        run_remote_ssh(extract_cmd_172)
        print("Remote extraction completed.")

        # Syntax check and smoke test
        run_remote_ssh(f"bash -n {REMOTE_DIR_172}/submit_M1_C5_P172_OLD_CONTROL.pbs", timeout=30)
        smoke_172 = run_remote_ssh(f"python3 {REMOTE_DIR_172}/smoke_import.py", timeout=60)
        assert "REMOTE_IMPORT_SUCCESS: True" in smoke_172, f"Smoke test failed for P172: {smoke_172}"
        print("Bash syntax and Python import smoke test passed.")

        # Execute datacheck
        print("Executing authentic Abaqus 2023 datachecks for Package 172 (preliminary + dynamic iter1)...")
        dc_out_172 = run_remote_ssh(f"bash {REMOTE_DIR_172}/run_datacheck.sh", timeout=300)
        print("Datacheck Output (P172):\n", dc_out_172)
        assert "P172_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS" in dc_out_172, "P172 mechanical DC failed"
        assert "P172_PHASE_DC: AUTHENTIC_DATACHECK_PASS" in dc_out_172, "P172 phase DC failed"
        assert "P172_ITER1_MECH: AUTHENTIC_DATACHECK_PASS" in dc_out_172, "P172 iter1 mech failed"
        assert "P172_ITER1_PHASE: AUTHENTIC_DATACHECK_PASS" in dc_out_172, "P172 iter1 phase failed"

        # Download receipts
        print("Downloading Package 172 receipts...")
        p172_jobs = ["P172_MECHANICAL_DC", "P172_PHASE_DC", "P172_ITER1_MECH", "P172_ITER1_PHASE"]
        for j in p172_jobs:
            for ext in [".dat", ".msg", ".stdout.txt"]:
                scp_download_file(f"{REMOTE_DIR_172}/{j}{ext}", PKG172_DIR / f"{j}{ext}")

        for j in p172_jobs:
            dat_text = (PKG172_DIR / f"{j}.dat").read_text(encoding="utf-8", errors="replace")
            assert "***ERROR" not in dat_text, f"Error in {j}.dat"
            assert ("ANALYSIS DATACHECK COMPLETE" in dat_text or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in dat_text), f"Missing completion in {j}.dat"
        print("Package 172 Datachecks Verified: All 4 subproblems Exit 0, 0 errors, authentic completion banners.")

        # 4. Stage and Datacheck Arm 2: Package 173 (Control Corrected)
        print("\n" + "-" * 70)
        print("STAGE & DATACHECK: ARM 2 (PACKAGE 173 - CONTROL CORRECTED)")
        print("-" * 70)
        run_remote_ssh(f"mkdir -p {REMOTE_DIR_173}")
        run_remote_ssh(f"rm -rf {REMOTE_DIR_173}/*")

        rem_tar_173 = f"{REMOTE_DIR_173}/package173_staging.tar.gz"
        rem_rt_173 = f"{REMOTE_DIR_173}/same_mesh_controls_runtime.tar.gz"
        print(f"Uploading {tar173_path.name}...")
        run_remote_upload(tar173_path, rem_tar_173, timeout=120)
        print(f"Uploading {runtime_tar_path.name}...")
        run_remote_upload(runtime_tar_path, rem_rt_173, timeout=120)

        extract_cmd_173 = (
            f"tar -C {REMOTE_DIR_173} -xzf {rem_tar_173} && rm -f {rem_tar_173} && "
            f"mkdir -p {REMOTE_DIR_173}/runtime && "
            f"tar -C {REMOTE_DIR_173}/runtime -xzf {rem_rt_173} && rm -f {rem_rt_173} && "
            f"chmod +x {REMOTE_DIR_173}/run_datacheck.sh {REMOTE_DIR_173}/submit_M1_C5_P173_CORRECTED_CONTROL.pbs"
        )
        run_remote_ssh(extract_cmd_173)
        print("Remote extraction completed.")

        # Syntax check and smoke test
        run_remote_ssh(f"bash -n {REMOTE_DIR_173}/submit_M1_C5_P173_CORRECTED_CONTROL.pbs", timeout=30)
        smoke_173 = run_remote_ssh(f"python3 {REMOTE_DIR_173}/smoke_import.py", timeout=60)
        assert "REMOTE_IMPORT_SUCCESS: True" in smoke_173, f"Smoke test failed for P173: {smoke_173}"
        print("Bash syntax and Python import smoke test passed.")

        # Execute datacheck
        print("Executing authentic Abaqus 2023 datachecks for Package 173 (preliminary + dynamic iter1)...")
        dc_out_173 = run_remote_ssh(f"bash {REMOTE_DIR_173}/run_datacheck.sh", timeout=300)
        print("Datacheck Output (P173):\n", dc_out_173)
        assert "P173_MECHANICAL_DC: AUTHENTIC_DATACHECK_PASS" in dc_out_173, "P173 mechanical DC failed"
        assert "P173_PHASE_DC: AUTHENTIC_DATACHECK_PASS" in dc_out_173, "P173 phase DC failed"
        assert "P173_ITER1_MECH: AUTHENTIC_DATACHECK_PASS" in dc_out_173, "P173 iter1 mech failed"
        assert "P173_ITER1_PHASE: AUTHENTIC_DATACHECK_PASS" in dc_out_173, "P173 iter1 phase failed"

        # Download receipts
        print("Downloading Package 173 receipts...")
        p173_jobs = ["P173_MECHANICAL_DC", "P173_PHASE_DC", "P173_ITER1_MECH", "P173_ITER1_PHASE"]
        for j in p173_jobs:
            for ext in [".dat", ".msg", ".stdout.txt"]:
                scp_download_file(f"{REMOTE_DIR_173}/{j}{ext}", PKG173_DIR / f"{j}{ext}")

        for j in p173_jobs:
            dat_text = (PKG173_DIR / f"{j}.dat").read_text(encoding="utf-8", errors="replace")
            assert "***ERROR" not in dat_text, f"Error in {j}.dat"
            assert ("ANALYSIS DATACHECK COMPLETE" in dat_text or "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in dat_text), f"Missing completion in {j}.dat"
        print("Package 173 Datachecks Verified: All 4 subproblems Exit 0, 0 errors, authentic completion banners.")

        # 5. Update manifests with downloaded receipts
        update_manifest_files(PKG172_DIR)
        update_manifest_files(PKG173_DIR)
        print("\nUpdated PACKAGE_MANIFEST.json for both packages.")

        # 6. Generate Formal Receipt JSON
        receipt = {
            "schema": 1,
            "task_id": "F1627-METHOD-C-SAME-MESH-EXTRACTOR-CONTRACT-QUALIFICATION",
            "status": "DATACHECKS_PASSED_ALL_8_SUBPROBLEMS_EXIT_0",
            "production_pbs_submissions": 0,
            "zero_pbs_enforced": True,
            "frozen_uel_sha256": FROZEN_UEL_HASH,
            "donor_provenance": {
                "checkpoint": "Checkpoint 03 (Job 1419566.mmaster02)",
                "target_uy_mm": 0.0018703125442191958,
                "donor_reference_force_kN": 0.17992419004440308,
                "donor_reference_total_energy_kNmm": 0.00022639903,
                "extraction_coverage": "100% direct extraction for u, d, H (13,278 nodes, 51,984 GPs)",
                "checkpoint_02_contamination_eliminated": True
            },
            "receiver_mesh": {
                "name": "C5_Identical_Receiver",
                "elements_quad": 12996,
                "physical_nodes": 13278,
                "reference_point_id": 999999,
                "slit_pairs": 53
            },
            "experimental_matrix": {
                "arm_1_control_old": {
                    "package_id": "package172_same_mesh_old_operator",
                    "package_dir": str(PKG172_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "remote_dir": REMOTE_DIR_172,
                    "operator": "element_averaged_mean",
                    "history_perturbation_peak_MPa": 6.3491085,
                    "history_perturbation_rms_MPa": 0.0680823,
                    "anderson_enabled": False,
                    "preliminary_mechanical_datacheck": {
                        "job": "P172_MECHANICAL_DC",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG172_DIR / "P172_MECHANICAL_DC.dat"),
                        "msg_sha256": sha256_file(PKG172_DIR / "P172_MECHANICAL_DC.msg"),
                    },
                    "preliminary_phase_datacheck": {
                        "job": "P172_PHASE_DC",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG172_DIR / "P172_PHASE_DC.dat"),
                        "msg_sha256": sha256_file(PKG172_DIR / "P172_PHASE_DC.msg"),
                    },
                    "dynamic_iter1_mechanical_datacheck": {
                        "job": "P172_ITER1_MECH",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG172_DIR / "P172_ITER1_MECH.dat"),
                        "msg_sha256": sha256_file(PKG172_DIR / "P172_ITER1_MECH.msg"),
                    },
                    "dynamic_iter1_phase_datacheck": {
                        "job": "P172_ITER1_PHASE",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG172_DIR / "P172_ITER1_PHASE.dat"),
                        "msg_sha256": sha256_file(PKG172_DIR / "P172_ITER1_PHASE.msg"),
                    }
                },
                "arm_2_control_corrected": {
                    "package_id": "package173_same_mesh_hardened_isoparametric",
                    "package_dir": str(PKG173_DIR.relative_to(REPO_ROOT)).replace("\\", "/"),
                    "remote_dir": REMOTE_DIR_173,
                    "operator": "hardened_isoparametric_gp_convex_clamp",
                    "history_perturbation_peak_MPa": 2.7089e-13,
                    "history_perturbation_rms_MPa": 2.2206e-15,
                    "anderson_enabled": False,
                    "preliminary_mechanical_datacheck": {
                        "job": "P173_MECHANICAL_DC",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG173_DIR / "P173_MECHANICAL_DC.dat"),
                        "msg_sha256": sha256_file(PKG173_DIR / "P173_MECHANICAL_DC.msg"),
                    },
                    "preliminary_phase_datacheck": {
                        "job": "P173_PHASE_DC",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG173_DIR / "P173_PHASE_DC.dat"),
                        "msg_sha256": sha256_file(PKG173_DIR / "P173_PHASE_DC.msg"),
                    },
                    "dynamic_iter1_mechanical_datacheck": {
                        "job": "P173_ITER1_MECH",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG173_DIR / "P173_ITER1_MECH.dat"),
                        "msg_sha256": sha256_file(PKG173_DIR / "P173_ITER1_MECH.msg"),
                    },
                    "dynamic_iter1_phase_datacheck": {
                        "job": "P173_ITER1_PHASE",
                        "status": "PASS",
                        "exit_code": 0,
                        "errors": 0,
                        "dat_sha256": sha256_file(PKG173_DIR / "P173_ITER1_PHASE.dat"),
                        "msg_sha256": sha256_file(PKG173_DIR / "P173_ITER1_PHASE.msg"),
                    }
                }
            }
        }

        RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(RECEIPT_PATH, "w", encoding="utf-8") as f:
            json.dump(receipt, f, indent=2)

        print(f"\nFormal receipt generated at: {RECEIPT_PATH.name}")
        print("=" * 80)
        print("ALL DATACHECKS QUALIFIED AND VERIFIED: PASS (0 ERRORS, EXIT 0)")
        print("=" * 80)

    finally:
        for tp in [tar172_path, tar173_path, runtime_tar_path]:
            if tp.is_file():
                tp.unlink()


if __name__ == "__main__":
    stage_and_datacheck()
