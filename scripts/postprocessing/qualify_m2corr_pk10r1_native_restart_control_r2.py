#!/usr/bin/env python3
"""
F178REPAIR Preflight Datacheck Qualification Script
Package: M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2
Task ID: F178REPAIR-M2-PK10R1-NATIVE-RESTART-CONTROL-DAT-OUTPUT-FIX1
"""

import sys
import os
import json
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

PKG_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2"
INP_FILE = PKG_DIR / "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2.inp"
UEL_FILE = PKG_DIR / "f42_mixed_uel_transactional.for"
PBS_FILE = PKG_DIR / "run_native_restart_control.pbs"
MANIFEST_FILE = PKG_DIR / "manifest.json"

EXPECTED_INP_SHA256 = "c31bc43c14617f76c3ae1b6acd97545b1e4ff0ac13ed3e28932fc35e530f58d5"
EXPECTED_PBS_SHA256 = "b35e7573210e61476a2693d58b330609715694f943bcdddf2f14fb8207ceee42"
EXPECTED_MANIFEST_SHA256 = "6fc970d779ff46dd96e7d8303d68bc9d60a874c4a274c224fdf4b8770775160f"
EXPECTED_UEL_SHA256 = "e3b373253069f9b36085ee426568ce002a7f195a4d5356c6c6a5549c97767138"

def main():
    print("================================================================================")
    print("F178REPAIR NATIVE RESTART CONTROL R2 PREFLIGHT DATACHECK QUALIFICATION")
    print("================================================================================")

    # 1. Local SHA256 Verification
    inp_sha = hashlib.sha256(INP_FILE.read_bytes()).hexdigest()
    pbs_sha = hashlib.sha256(PBS_FILE.read_bytes()).hexdigest()
    manifest_sha = hashlib.sha256(MANIFEST_FILE.read_bytes()).hexdigest()
    uel_sha = hashlib.sha256(UEL_FILE.read_bytes()).hexdigest()

    print(f"INP SHA256:      {inp_sha}")
    print(f"PBS SHA256:      {pbs_sha}")
    print(f"Manifest SHA256: {manifest_sha}")
    print(f"UEL SHA256:      {uel_sha}")

    assert inp_sha == EXPECTED_INP_SHA256, f"INP SHA mismatch: {inp_sha} != {EXPECTED_INP_SHA256}"
    assert pbs_sha == EXPECTED_PBS_SHA256, f"PBS SHA mismatch: {pbs_sha} != {EXPECTED_PBS_SHA256}"
    assert manifest_sha == EXPECTED_MANIFEST_SHA256, f"Manifest SHA mismatch: {manifest_sha} != {EXPECTED_MANIFEST_SHA256}"
    assert uel_sha == EXPECTED_UEL_SHA256, f"UEL SHA mismatch: {uel_sha} != {EXPECTED_UEL_SHA256}"

    print("Local SHA256 Hash Verification: PASS")

    # 2. Remote Sync
    remote_target_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2"
    print(f"\nSyncing R2 package to cluster directory {remote_target_dir}...")

    mkdir_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_target_dir}"]
    subprocess.run(mkdir_cmd, check=True)

    scp_cmd = [
        "scp", "-i", SSH_KEY,
        str(INP_FILE),
        str(UEL_FILE),
        str(PBS_FILE),
        str(MANIFEST_FILE),
        f"{SSH_HOST}:{remote_target_dir}/"
    ]
    subprocess.run(scp_cmd, check=True)

    # 3. Copy oldjob database files on cluster
    source_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1"
    source_job = "M2CORR_PK10R1_CONTINUOUS_U050_STATECAPTURE_R1"
    target_job = "M2CORR_PK10R1_NATIVE_RESTART_CONTROL_INC29_R2"

    copy_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && "
        f"cp -f ~/{source_dir}/{source_job}.res {source_job}.res && "
        f"cp -f ~/{source_dir}/{source_job}.stt {source_job}.stt && "
        f"cp -f ~/{source_dir}/{source_job}.mdl {source_job}.mdl && "
        f"cp -f ~/{source_dir}/{source_job}.prt {source_job}.prt && "
        f"cp -f ~/{source_dir}/{source_job}.odb {source_job}.odb && "
        f"cp -f ~/{source_dir}/{source_job}.res {target_job}.res && "
        f"cp -f ~/{source_dir}/{source_job}.stt {target_job}.stt && "
        f"cp -f ~/{source_dir}/{source_job}.mdl {target_job}.mdl && "
        f"cp -f ~/{source_dir}/{source_job}.prt {target_job}.prt && "
        f"cp -f ~/{source_dir}/{source_job}.odb {target_job}.odb"
    ]
    print("\nCopying source binary restart files into remote R2 workspace...")
    subprocess.run(copy_cmd, check=True)
    print("Remote file setup complete.")

    # 4. Run Abaqus 2023 datacheck (Preprocessing only, NO qsub, NO solver execution)
    print("\nExecuting Abaqus 2023 datacheck preflight...")
    datacheck_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"source /etc/profile.d/lmod.sh 2>/dev/null || true && "
        f"module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 2>/dev/null && "
        f"cd {remote_target_dir} && "
        f"abaqus job={target_job} user=f42_mixed_uel_transactional.for oldjob={source_job} datacheck interactive"
    ]
    res_dc = subprocess.run(datacheck_cmd, capture_output=True, text=True)
    print("\nAbaqus Datacheck Command Output:")
    print(res_dc.stdout)
    if res_dc.stderr:
        print("Stderr:", res_dc.stderr)

    # 5. Read DAT file and verify criteria
    dat_read_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cat {remote_target_dir}/{target_job}.dat"
    ]
    res_dat = subprocess.run(dat_read_cmd, capture_output=True, text=True, check=True)
    dat_text = res_dat.stdout

    print("\n--------------------------------------------------------------------------------")
    print("DATACHECK VERIFICATION CHECKS")
    print("--------------------------------------------------------------------------------")

    step1_inc29_found = "STEP    1  INCREMENT   29  HAS BEEN FOUND ON THE RESTART FILE" in dat_text
    datacheck_complete = "ANALYSIS DATACHECK COMPLETE" in dat_text
    fatal_errors = "FATAL ERROR" in dat_text

    print(f"Restart STEP 1 INC 29 found: {step1_inc29_found}")
    print(f"Datacheck Complete:          {datacheck_complete}")
    print(f"Fatal Errors Present:        {fatal_errors}")

    assert step1_inc29_found, "STEP 1 INC 29 not found in DAT file!"
    assert datacheck_complete, "DAT check did not complete successfully!"
    assert not fatal_errors, "Fatal errors detected in DAT file!"

    print("\nDATACHECK QUALIFICATION RESULT: PASS")
    print("================================================================================")


if __name__ == "__main__":
    main()
