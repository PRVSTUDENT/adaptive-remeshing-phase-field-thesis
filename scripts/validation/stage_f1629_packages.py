#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stage_f1629_packages.py
=======================
Deploys and stages Package 174 (M1_C6_R12_PICARD_BASELINE) and
Package 175 (M1_C6_R12_ANDERSON_M2) to cluster scratch directories:
  - /scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline
  - /scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2
Verifies runtime dependency closure, remote bash -n syntax, and smoke tests.
Task: F1629-METHOD-C-C6-R12-OVERNIGHT-CONTROLLED-PAIR
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
PKG_174 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "174_c6_r12_picard_baseline"
PKG_175 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "175_c6_r12_anderson_m2"
SSH_WRAPPER = REPO_ROOT / ".agents" / "scripts" / "Invoke-GuardedSsh.ps1"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

REMOTE_174_DIR = "/scratch9/pr21vyci/runs/mode1_c6_r12_picard_baseline"
REMOTE_175_DIR = "/scratch9/pr21vyci/runs/mode1_c6_r12_anderson_m2"


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


def stage():
    print("=" * 80)
    print("STAGING F1629 PACKAGES: 174 (PICARD BASELINE) & 175 (ANDERSON M2)")
    print("=" * 80)

    # 1. Verify frozen production UEL
    for pkg in [PKG_174, PKG_175]:
        uel_local = pkg / "f42_mixed_uel.for"
        actual_uel_hash = sha256_file(uel_local)
        assert actual_uel_hash == FROZEN_UEL_HASH, f"UEL hash mismatch in {pkg.name}: {actual_uel_hash}"
    print(f"1. Verified frozen production UEL in both packages: {FROZEN_UEL_HASH}")

    # 2. Package tarballs
    tar_174 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "pkg174_staging.tar.gz"
    tar_175 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "pkg175_staging.tar.gz"
    runtime_tar = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f1629_runtime.tar.gz"

    print("\n2. Creating tarballs...")
    for pkg, t_path in [(PKG_174, tar_174), (PKG_175, tar_175)]:
        with tarfile.open(t_path, "w:gz") as tar:
            for f in sorted(pkg.iterdir()):
                if f.is_file() and not f.name.endswith((".tar.gz")):
                    if f.suffix in (".sh", ".pbs", ".py"):
                        content = f.read_bytes().replace(b"\r\n", b"\n")
                        f.write_bytes(content)
                    tar.add(f, arcname=f.name)

    # Runtime tarball with driver, accelerator, extractor and full dependency closure
    runtime_files = [
        "scripts/__init__.py",
        "scripts/state_transfer/__init__.py",
        "scripts/state_transfer/anderson_acceleration.py",
        "scripts/state_transfer/c3_int_to_c4_spatial_mapping.py",
        "scripts/state_transfer/c4_to_c5_spatial_mapping.py",
        "scripts/state_transfer/driver_package146_147_pdas_continuation.py",
        "scripts/state_transfer/driver_package171_r12_c6_coupled_pdas.py",
        "scripts/validation/__init__.py",
        "scripts/validation/extract_package148_iteration.py",
    ]
    with tarfile.open(runtime_tar, "w:gz") as tar:
        for rf in runtime_files:
            rf_path = REPO_ROOT / rf
            if rf_path.is_file():
                tar.add(rf_path, arcname=rf)

    print(f"Package 174 tarball: {tar_174.stat().st_size / (1024*1024):.2f} MB")
    print(f"Package 175 tarball: {tar_175.stat().st_size / (1024*1024):.2f} MB")
    print(f"Runtime tarball: {runtime_tar.stat().st_size / 1024:.2f} KB")

    try:
        # 3. Stage Arm A (Package 174)
        print(f"\n3. Staging Package 174 to {REMOTE_174_DIR}...")
        run_remote_ssh(f"mkdir -p {REMOTE_174_DIR}")
        run_remote_ssh(f"rm -rf {REMOTE_174_DIR}/*")
        remote_t174 = f"{REMOTE_174_DIR}/pkg174_staging.tar.gz"
        remote_rt174 = f"{REMOTE_174_DIR}/f1629_runtime.tar.gz"
        run_remote_upload(tar_174, remote_t174, timeout=120)
        run_remote_upload(runtime_tar, remote_rt174, timeout=120)

        extract_174 = (
            f"tar -C {REMOTE_174_DIR} -xzf {remote_t174} && rm -f {remote_t174} && "
            f"mkdir -p {REMOTE_174_DIR}/runtime && "
            f"tar -C {REMOTE_174_DIR}/runtime -xzf {remote_rt174} && rm -f {remote_rt174} && "
            f"chmod +x {REMOTE_174_DIR}/run_datacheck.sh {REMOTE_174_DIR}/submit_M1_C6_R12_PICARD_BASELINE.pbs"
        )
        run_remote_ssh(extract_174)

        # 4. Stage Arm B (Package 175)
        print(f"\n4. Staging Package 175 to {REMOTE_175_DIR}...")
        run_remote_ssh(f"mkdir -p {REMOTE_175_DIR}")
        run_remote_ssh(f"rm -rf {REMOTE_175_DIR}/*")
        remote_t175 = f"{REMOTE_175_DIR}/pkg175_staging.tar.gz"
        remote_rt175 = f"{REMOTE_175_DIR}/f1629_runtime.tar.gz"
        run_remote_upload(tar_175, remote_t175, timeout=120)
        run_remote_upload(runtime_tar, remote_rt175, timeout=120)

        extract_175 = (
            f"tar -C {REMOTE_175_DIR} -xzf {remote_t175} && rm -f {remote_t175} && "
            f"mkdir -p {REMOTE_175_DIR}/runtime && "
            f"tar -C {REMOTE_175_DIR}/runtime -xzf {remote_rt175} && rm -f {remote_rt175} && "
            f"chmod +x {REMOTE_175_DIR}/run_datacheck.sh {REMOTE_175_DIR}/submit_M1_C6_R12_ANDERSON_M2.pbs"
        )
        run_remote_ssh(extract_175)

        # 5. Remote bash syntax check on both PBS scripts
        print("\n5. Remote Bash Syntax Checks...")
        run_remote_ssh(f"bash -n {REMOTE_174_DIR}/submit_M1_C6_R12_PICARD_BASELINE.pbs", timeout=30)
        print("  - Package 174 PBS bash -n syntax check: PASSED cleanly.")
        run_remote_ssh(f"bash -n {REMOTE_175_DIR}/submit_M1_C6_R12_ANDERSON_M2.pbs", timeout=30)
        print("  - Package 175 PBS bash -n syntax check: PASSED cleanly.")

        # 6. Remote Python smoke import in each scratch dir
        print("\n6. Remote Python Import Smoke Tests...")
        out_174 = run_remote_ssh(f"python3 {REMOTE_174_DIR}/smoke_import.py", timeout=60)
        assert "REMOTE_IMPORT_SUCCESS: True" in out_174, f"Smoke test failed in Pkg 174: {out_174}"
        print("  - Package 174 smoke test: PASSED.")

        out_175 = run_remote_ssh(f"python3 {REMOTE_175_DIR}/smoke_import.py", timeout=60)
        assert "REMOTE_IMPORT_SUCCESS: True" in out_175, f"Smoke test failed in Pkg 175: {out_175}"
        print("  - Package 175 smoke test: PASSED.")

        print("\n" + "=" * 80)
        print("BOTH PACKAGES (174 & 175) STAGED AND QUALIFIED FOR EXECUTION!")
        print("=" * 80)

    finally:
        for t in [tar_174, tar_175, runtime_tar]:
            if t.is_file():
                t.unlink()


if __name__ == "__main__":
    stage()
