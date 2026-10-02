#!/usr/bin/env python3
"""
Remote Qualification Runner for M2REF_H1_FULL_U050 and M2REF_H2_FULL_U050 Batch
"""

import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"
REMOTE_BASE = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch"

def run_ssh(cmd):
    print(f"\n[SSH] {cmd}")
    full_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, cmd]
    res = subprocess.run(full_cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("[STDERR]", res.stderr)
    return res

def upload_pkg(local_dir, remote_dir):
    print(f"\nUploading {local_dir.name} -> {remote_dir}...")
    run_ssh(f"mkdir -p {remote_dir}")
    scp_cmd = ["scp", "-i", SSH_KEY, "-r", f"{str(local_dir)}/*", f"{SSH_HOST}:{remote_dir}/"]
    res = subprocess.run(scp_cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Upload complete for {local_dir.name}")
    else:
        print(f"Upload failed: {res.stderr}")
        sys.exit(1)

def main():
    print("================================================================================")
    print("REMOTE QUALIFICATION FOR UNIFORM FULL REFERENCES BATCH (H1 and H2)")
    print("================================================================================")

    h1_dir = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050"
    h2_dir = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050"

    upload_pkg(h1_dir, f"{REMOTE_BASE}/M2REF_H1_FULL_U050")
    upload_pkg(h2_dir, f"{REMOTE_BASE}/M2REF_H2_FULL_U050")

    # 1. Manifest Validation
    print("\n--- 1. MANIFEST VALIDATION ON CLUSTER ---")
    res1 = run_ssh(f"cd {REMOTE_BASE}/M2REF_H1_FULL_U050 && python3 validate_package_manifest.py")
    if "ALL FILES MATCH MANIFEST SHA256: PASS" not in res1.stdout:
        print("ERROR: H1 manifest check failed!")
        sys.exit(1)

    res2 = run_ssh(f"cd {REMOTE_BASE}/M2REF_H2_FULL_U050 && python3 validate_package_manifest.py")
    if "ALL FILES MATCH MANIFEST SHA256: PASS" not in res2.stdout:
        print("ERROR: H2 manifest check failed!")
        sys.exit(1)

    # 2. Abaqus 2023 Datacheck on H1
    print("\n--- 2. ABAQUS 2023 DATACHECK ON H1 ---")
    datacheck_cmd_h1 = (
        f"cd {REMOTE_BASE}/M2REF_H1_FULL_U050 && "
        "module load intel/2024.2.0 gcc/11.4.0 abaqus/2023 || true ; "
        "abaqus job=M2REF_H1_FULL_U050_DATACHECK input=M2REF_H1_FULL_U050.inp user=f42_mixed_uel.for datacheck interactive"
    )
    res_dc_h1 = run_ssh(datacheck_cmd_h1)
    if "Abaqus JOB M2REF_H1_FULL_U050_DATACHECK COMPLETED" not in res_dc_h1.stdout:
        print("ERROR: H1 Datacheck failed!")
        sys.exit(1)
    print("H1 DATACHECK PASS: Exit 0")

    # 3. Abaqus 2023 Datacheck on H2
    print("\n--- 3. ABAQUS 2023 DATACHECK ON H2 ---")
    datacheck_cmd_h2 = (
        f"cd {REMOTE_BASE}/M2REF_H2_FULL_U050 && "
        "module load intel/2024.2.0 gcc/11.4.0 abaqus/2023 || true ; "
        "abaqus job=M2REF_H2_FULL_U050_DATACHECK input=M2REF_H2_FULL_U050.inp user=f42_mixed_uel.for datacheck interactive"
    )
    res_dc_h2 = run_ssh(datacheck_cmd_h2)
    if "Abaqus JOB M2REF_H2_FULL_U050_DATACHECK COMPLETED" not in res_dc_h2.stdout:
        print("ERROR: H2 Datacheck failed!")
        sys.exit(1)
    print("H2 DATACHECK PASS: Exit 0")

    # 4. Guarded Wrapper Dry-Run Checks
    print("\n--- 4. GUARDED WRAPPER DRY-RUN CHECKS ---")
    res_wr_h1 = run_ssh(f"cd {REMOTE_BASE}/M2REF_H1_FULL_U050 && chmod +x submit_m2ref_h1_full_u050.sh && ./submit_m2ref_h1_full_u050.sh")
    if "DRY-RUN MODE: Validation passed" not in res_wr_h1.stdout:
        print("ERROR: H1 dry run failed!")
        sys.exit(1)

    res_wr_h2 = run_ssh(f"cd {REMOTE_BASE}/M2REF_H2_FULL_U050 && chmod +x submit_m2ref_h2_full_u050.sh && ./submit_m2ref_h2_full_u050.sh")
    if "DRY-RUN MODE: Validation passed" not in res_wr_h2.stdout:
        print("ERROR: H2 dry run failed!")
        sys.exit(1)

    print("\n================================================================================")
    print("REMOTE QUALIFICATION COMPLETE: BOTH PACKAGES PASSED ALL GATES (0 QSUB CALLS)")
    print("================================================================================")

if __name__ == '__main__':
    main()
