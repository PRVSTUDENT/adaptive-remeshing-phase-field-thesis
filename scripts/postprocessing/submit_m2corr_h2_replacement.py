#!/usr/bin/env python3
"""
F130SUB Technical Replacement Submission Script for M2CORR_H2_FULL_U050
Replaces failed job: 1389683.mmaster02
Task ID: F130SUB-M2-CORRECTED-H2-BASELINE-REPLACEMENT-SUBMIT1
"""

import sys
import os
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

FORTRAN_SOURCE = ROOT / "models/generated/mode_ii/production_control_batch/f42_mixed_uel_transactional.for"
EXPECTED_UEL_SHA256 = "ed1586d6427a4b1a01d99f7e219891ec7be9fe911e066d9360724942e7d27720"

H2_SOURCE_INP = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/M2REF_H2_FULL_U050.inp"
H2_DEST_DIR = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050"

PBS_TEMPLATE = """#!/bin/bash
#PBS -N M2CORR_H2_FULL_U050
#PBS -l nodes=1:ppn=1
#PBS -l mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

cd $PBS_O_WORKDIR

# Load notifications
if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notification_install_terminal_trap
    notify_start "M2CORR_H2_FULL_U050"
fi

export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH
source /etc/profile.d/lmod.sh 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus execution for M2CORR_H2_FULL_U050..."
/cluster/application/abaqus/2023/Commands/abaqus job=M2CORR_H2_FULL_U050 input=M2CORR_H2_FULL_U050.inp user=f42_mixed_uel_transactional.for interactive 2>&1
EXIT_CODE=$?

echo "Abaqus exited with code $EXIT_CODE"
exit $EXIT_CODE
"""

SUBMIT_WRAPPER_TEMPLATE = """#!/bin/bash
set -euo pipefail

JOB_NAME="M2CORR_H2_FULL_U050"
EXPECTED_MANIFEST_SHA256="{manifest_sha256}"
EXPECTED_UEL_SHA256="{uel_sha256}"

echo "=== PRE-SUBMISSION GUARDED VERIFICATION: $JOB_NAME (REPLACEMENT FOR 1389683.mmaster02) ==="

# 1. Verify UEL SHA256
ACTUAL_UEL_SHA256=$(sha256sum f42_mixed_uel_transactional.for | awk '{{print $1}}')
if [ "$ACTUAL_UEL_SHA256" != "$EXPECTED_UEL_SHA256" ]; then
    echo "ERROR: UEL SHA256 mismatch! Expected $EXPECTED_UEL_SHA256, got $ACTUAL_UEL_SHA256"
    exit 1
fi

# 2. Verify Manifest SHA256
ACTUAL_MANIFEST_SHA256=$(sha256sum manifest.json | awk '{{print $1}}')
if [ "$ACTUAL_MANIFEST_SHA256" != "$EXPECTED_MANIFEST_SHA256" ]; then
    echo "ERROR: Manifest SHA256 mismatch! Expected $EXPECTED_MANIFEST_SHA256, got $ACTUAL_MANIFEST_SHA256"
    exit 1
fi

echo "MANIFEST AND REPAIRED UEL VERIFICATION PASSED FOR $JOB_NAME"

# 3. Submit via qsub
SUBMIT_OUTPUT=$(qsub submit_M2CORR_H2_FULL_U050.pbs)
JOB_ID=$(echo "$SUBMIT_OUTPUT" | grep -E '^[0-9]+\\.' || echo "$SUBMIT_OUTPUT")
echo "SUBMITTED_REPLACEMENT_JOB_ID=$JOB_ID"

# 4. Trigger Telegram submission notification
if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notify_submitted "$JOB_NAME" "$JOB_ID"
fi
"""

def prepare_replacement_package(dest_dir, job_name, source_inp, uel_content):
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy & update INP
    inp_content = source_inp.read_text(encoding="utf-8", errors="ignore")
    inp_content = f"*HEADING\n{job_name} - Technical Replacement with UMAT Stub\n" + "\n".join(inp_content.splitlines()[1:])
    inp_file = dest_dir / f"{job_name}.inp"
    inp_file.write_text(inp_content, encoding="utf-8", newline="\n")
    
    # 2. Write UEL
    uel_file = dest_dir / "f42_mixed_uel_transactional.for"
    uel_file.write_text(uel_content, encoding="utf-8", newline="\n")
    
    # 3. Compute Hashes & Write Manifest
    inp_sha256 = hashlib.sha256(inp_content.encode("utf-8")).hexdigest()
    uel_sha256 = hashlib.sha256(uel_content.encode("utf-8")).hexdigest()
    
    manifest = {
        "job_name": job_name,
        "replaces_job_id": "1389683.mmaster02",
        "inp_sha256": inp_sha256,
        "uel_sha256": uel_sha256,
        "physical_element_count": 33852,
        "formulation": "UNDEGRADED_PSI_PLUS_TRANSACTIONAL_UEXTERNALDB_WITH_UMAT_STUB"
    }
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    (dest_dir / "manifest.json").write_bytes(manifest_bytes)
    
    # 4. Write PBS script
    pbs_content = PBS_TEMPLATE.format(job_name=job_name)
    (dest_dir / f"submit_{job_name}.pbs").write_text(pbs_content, encoding="utf-8", newline="\n")
    
    # 5. Write guarded submit wrapper
    wrapper_content = SUBMIT_WRAPPER_TEMPLATE.format(
        manifest_sha256=manifest_sha256,
        uel_sha256=uel_sha256
    )
    wrapper_file = dest_dir / f"guarded_submit_{job_name}.sh"
    wrapper_file.write_text(wrapper_content, encoding="utf-8", newline="\n")
    
    return manifest_sha256, uel_sha256

def main():
    print("================================================================================")
    print("F130SUB TECHNICAL REPLACEMENT PACKAGE PREPARATION & GUARDED SUBMISSION")
    print("================================================================================")

    uel_content = FORTRAN_SOURCE.read_text(encoding="utf-8", errors="ignore")
    actual_uel_sha256 = hashlib.sha256(uel_content.encode("utf-8")).hexdigest()
    assert actual_uel_sha256 == EXPECTED_UEL_SHA256, f"Expected {EXPECTED_UEL_SHA256}, got {actual_uel_sha256}"

    # 1. Prepare replacement package
    h2_manifest_sha, _ = prepare_replacement_package(H2_DEST_DIR, "M2CORR_H2_FULL_U050", H2_SOURCE_INP, uel_content)
    print(f"Prepared M2CORR_H2_FULL_U050 technical replacement package (Manifest SHA256: {h2_manifest_sha})")

    # 2. Sync to cluster
    remote_h2_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050"
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_h2_dir}"], check=True)

    for f in H2_DEST_DIR.iterdir():
        subprocess.run(["scp", "-i", SSH_KEY, str(f), f"{SSH_HOST}:{remote_h2_dir}/"], check=True)

    # Convert Windows CRLF to LF and make submit wrapper executable
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"sed -i 's/\\r$//' {remote_h2_dir}/* && chmod +x {remote_h2_dir}/*.sh"], check=True)

    # 3. Execute guarded submission on cluster
    print("\nExecuting guarded replacement submission for M2CORR_H2_FULL_U050...")
    h2_res = subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"cd {remote_h2_dir} && ./guarded_submit_M2CORR_H2_FULL_U050.sh"], capture_output=True, text=True, check=True)
    print(h2_res.stdout)

if __name__ == "__main__":
    main()
