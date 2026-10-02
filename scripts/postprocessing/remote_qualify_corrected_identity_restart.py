#!/usr/bin/env python3
"""
Remote Qualification & Single Permitted Guarded Submission Script for PK10R1_CORRECTED_IDENTITY_RESTART_U050
Task ID: F122STATE-M2-PK10R1-CORRECTED-IDENTITY-RESTART-QUAL-AND-SUBMIT1
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

JOB_NAME = "PK10R1_CORRECTED_IDENTITY_RESTART_U050"
LOCAL_PKG_DIR = ROOT / f"models/generated/mode_ii/production_control_batch/{JOB_NAME}"
REMOTE_PKG_DIR = f"projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/{JOB_NAME}"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def main():
    print("================================================================================")
    print(f"REMOTE QUALIFICATION & GUARDED SUBMISSION: {JOB_NAME}")
    print("================================================================================")

    # 1. Verify Local Manifest
    manifest_path = LOCAL_PKG_DIR / "PACKAGE_MANIFEST.json"
    if not manifest_path.exists():
        print("ERROR: Local package manifest missing!")
        sys.exit(1)
        
    local_manifest = json.loads(manifest_path.read_text())
    expected_hash = local_manifest["manifest_sha256"]
    print(f"1. Local Package Manifest SHA256: {expected_hash}")

    # Re-verify all file hashes locally
    for fn, sha in local_manifest["files"].items():
        fp = LOCAL_PKG_DIR / fn
        if not fp.exists():
            print(f"ERROR: Missing package file {fn}")
            sys.exit(1)
        actual_sha = get_file_sha256(fp)
        if actual_sha != sha:
            print(f"ERROR: Hash mismatch for {fn}: {actual_sha} vs {sha}")
            sys.exit(1)
    print("   All local file hashes match manifest: PASS")

    # 2. Sync Package to Remote Cluster
    print(f"\n2. Syncing package to remote cluster: {REMOTE_PKG_DIR}...")
    mkdir_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {REMOTE_PKG_DIR}"]
    subprocess.run(mkdir_cmd, check=True)

    # Copy files
    for fp in LOCAL_PKG_DIR.glob("*"):
        if fp.is_file():
            scp_cmd = ["scp", "-i", SSH_KEY, str(fp), f"{SSH_HOST}:{REMOTE_PKG_DIR}/{fp.name}"]
            subprocess.run(scp_cmd, check=True)
    print("   Package synced to cluster: PASS")

    # Fix permissions and line endings on cluster
    chmod_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"chmod +x {REMOTE_PKG_DIR}/*.sh {REMOTE_PKG_DIR}/*.py && dos2unix {REMOTE_PKG_DIR}/*.sh {REMOTE_PKG_DIR}/*.py 2>/dev/null || sed -i 's/\\r$//' {REMOTE_PKG_DIR}/*.sh {REMOTE_PKG_DIR}/*.py"
    ]
    subprocess.run(chmod_cmd, check=True)

    # 3. Verify Remote Manifest
    print("\n3. Verifying remote package manifest SHA256...")
    verify_remote_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_PKG_DIR} && python3 validate_package_manifest.py"
    ]
    res_ver = subprocess.run(verify_remote_cmd, capture_output=True, text=True)
    print("   Remote Manifest Check Output:\n", res_ver.stdout)
    if "MANIFEST_VALIDATION_PASS" not in res_ver.stdout:
        print("ERROR: Remote manifest validation failed!")
        sys.exit(1)

    # 4. Dry Run Guarded Wrapper
    print("\n4. Running guarded wrapper dry run...")
    dry_run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_PKG_DIR} && ./submit_pk10r1_corrected_identity_restart_u050.sh --dry-run"
    ]
    res_dry = subprocess.run(dry_run_cmd, capture_output=True, text=True)
    print("   Dry Run Output:\n", res_dry.stdout)
    if "DRY_RUN_PASS" not in res_dry.stdout:
        print("ERROR: Dry run failed!")
        sys.exit(1)

    # 5. Abaqus 2023 Datacheck
    print("\n5. Executing Abaqus 2023 Datacheck on cluster...")
    datacheck_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || source /etc/profile.d/modules.sh 2>/dev/null || true; module purge 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7; cd {REMOTE_PKG_DIR} && (rm -f {JOB_NAME}.lck test_compile.* 2>/dev/null || true) && /cluster/application/abaqus/2023/Commands/abaqus job={JOB_NAME} input={JOB_NAME}.inp user=f42_mixed_uel.for datacheck interactive 2>&1"
    ]
    res_dc = subprocess.run(datacheck_cmd, capture_output=True, text=True, timeout=300)
    print("   Datacheck Stdout:\n", res_dc.stdout)
    if "COMPLETED" not in res_dc.stdout and res_dc.returncode != 0:
        print("ERROR: Abaqus Datacheck failed!")
        sys.exit(1)

    # Inspect datacheck dat log on remote
    check_dat_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_PKG_DIR} && grep -E 'ANALYSIS DATACHECK COMPLETE|ANALYSIS HAS COMPLETED|COMPLETED' {JOB_NAME}.dat || true"
    ]
    res_check = subprocess.run(check_dat_cmd, capture_output=True, text=True)
    print("   Datacheck Verification:\n", res_check.stdout)
    if "DATACHECK COMPLETE" not in res_check.stdout and "COMPLETED" not in res_check.stdout:
        print("ERROR: Datacheck output does not confirm completion!")
        sys.exit(1)
    print("   Abaqus Datacheck: DATACHECK_PASS")

    # 6. Telegram Connectivity Verification
    print("\n6. Verifying Telegram notification contract...")
    tele_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_PKG_DIR} && source ./job_notifications.sh && notification_load_config && notification_test_telegram"
    ]
    res_tele = subprocess.run(tele_cmd, capture_output=True, text=True)
    print("   Telegram Output:\n", res_tele.stdout)

    # 7. Execute Single Permitted Guarded Submission
    print("\n7. Executing single permitted guarded submission (--execute)...")
    sub_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {REMOTE_PKG_DIR} && ./submit_pk10r1_corrected_identity_restart_u050.sh --execute"
    ]
    res_sub = subprocess.run(sub_cmd, capture_output=True, text=True)
    print("   Submission Output:\n", res_sub.stdout)
    
    if "SUBMITTED:" not in res_sub.stdout:
        print("ERROR: Submission failed!")
        sys.exit(1)
        
    submitted_id = res_sub.stdout.split("SUBMITTED:")[1].strip().split()[0]
    print(f"\n================================================================================")
    print(f"SUCCESSFULLY SUBMITTED JOB: {submitted_id}")
    print(f"Package: {JOB_NAME}")
    print(f"Manifest SHA256: {expected_hash}")
    print(f"================================================================================")

if __name__ == "__main__":
    main()
