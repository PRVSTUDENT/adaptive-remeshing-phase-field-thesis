#!/usr/bin/env python3
"""
F134SUB Package Preparation & Guarded Submission Script
Jobs: M2CORR_H1_FREEU2_FULL_U050 & M2CORR_H2_FREEU2_FULL_U050
Task ID: F134SUB-M2-CORRECTED-UNIFORM-BASELINES-SUBMIT1
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

H1_SOURCE_INP = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/M2REF_H1_FULL_U050.inp"
H2_SOURCE_INP = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/M2REF_H2_FULL_U050.inp"

H1_DEST_DIR = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050"
H2_DEST_DIR = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050"

PBS_TEMPLATE = """#!/bin/bash
#PBS -N {job_name}
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
    notify_start "{job_name}"
fi

export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH
source /etc/profile.d/lmod.sh 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus execution for {job_name}..."
/cluster/application/abaqus/2023/Commands/abaqus job={job_name} input={job_name}.inp user=f42_mixed_uel_transactional.for interactive 2>&1
EXIT_CODE=$?

echo "Abaqus exited with code $EXIT_CODE"
exit $EXIT_CODE
"""

SUBMIT_WRAPPER_TEMPLATE = """#!/bin/bash
set -euo pipefail

JOB_NAME="{job_name}"
EXPECTED_MANIFEST_SHA256="{manifest_sha256}"
EXPECTED_UEL_SHA256="{uel_sha256}"

echo "=== PRE-SUBMISSION GUARDED VERIFICATION: $JOB_NAME ==="

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

echo "MANIFEST AND UEL VERIFICATION PASSED FOR $JOB_NAME"

# 3. Submit via qsub
SUBMIT_OUTPUT=$(qsub submit_{job_name}.pbs)
JOB_ID=$(echo "$SUBMIT_OUTPUT" | grep -E '^[0-9]+\\.' || echo "$SUBMIT_OUTPUT")
echo "SUBMITTED_JOB_ID=$JOB_ID"

# 4. Trigger Telegram submission notification
if [ -f "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh" ]; then
    source "$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
    notify_submitted "$JOB_NAME" "$JOB_ID"
fi
"""

def modify_inp_remove_top_u2(source_inp, job_name):
    content = source_inp.read_text(encoding="utf-8", errors="ignore")
    lines = content.splitlines()
    
    new_lines = []
    skip_next = False
    
    for i, l in enumerate(lines):
        # Header update
        if i == 0 and l.startswith("*HEADING"):
            new_lines.append(f"*HEADING\n{job_name} - Corrected Uniform Baseline (Top U2 Free)")
            continue
            
        # Check if line is top_nodes, 2, 2
        if "top_nodes, 2, 2" in l or "top_nodes, 2" in l:
            # Skip this boundary condition line!
            continue
        new_lines.append(l)
        
    return "\n".join(new_lines) + "\n"

def prepare_package(dest_dir, job_name, source_inp, uel_content, phys_elems):
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Modify & write INP
    inp_content = modify_inp_remove_top_u2(source_inp, job_name)
    (dest_dir / f"{job_name}.inp").write_text(inp_content, encoding="utf-8", newline="\n")
    
    # 2. Write UEL
    (dest_dir / "f42_mixed_uel_transactional.for").write_text(uel_content, encoding="utf-8", newline="\n")
    
    # 3. Compute Hashes & Write Manifest
    inp_sha256 = hashlib.sha256(inp_content.encode("utf-8")).hexdigest()
    uel_sha256 = hashlib.sha256(uel_content.encode("utf-8")).hexdigest()
    
    manifest = {
        "job_name": job_name,
        "inp_sha256": inp_sha256,
        "uel_sha256": uel_sha256,
        "physical_element_count": phys_elems,
        "boundary_condition": "MODE_II_TOP_U2_FREE",
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
        job_name=job_name,
        manifest_sha256=manifest_sha256,
        uel_sha256=uel_sha256
    )
    (dest_dir / f"guarded_submit_{job_name}.sh").write_text(wrapper_content, encoding="utf-8", newline="\n")
    
    return manifest_sha256, uel_sha256

def main():
    print("================================================================================")
    print("F134SUB CORRECTED UNIFORM BASELINES PREPARATION & GUARDED SUBMISSION")
    print("================================================================================")

    uel_content = FORTRAN_SOURCE.read_text(encoding="utf-8", errors="ignore")
    actual_uel_sha = hashlib.sha256(uel_content.encode("utf-8")).hexdigest()
    assert actual_uel_sha == EXPECTED_UEL_SHA256, f"Expected {EXPECTED_UEL_SHA256}, got {actual_uel_sha}"

    # 1. Prepare H1 Package
    h1_manifest_sha, _ = prepare_package(H1_DEST_DIR, "M2CORR_H1_FREEU2_FULL_U050", H1_SOURCE_INP, uel_content, 12064)
    print(f"Prepared M2CORR_H1_FREEU2_FULL_U050 (Manifest SHA256: {h1_manifest_sha})")

    # 2. Prepare H2 Package
    h2_manifest_sha, _ = prepare_package(H2_DEST_DIR, "M2CORR_H2_FREEU2_FULL_U050", H2_SOURCE_INP, uel_content, 33852)
    print(f"Prepared M2CORR_H2_FREEU2_FULL_U050 (Manifest SHA256: {h2_manifest_sha})")

    # 3. Sync & Submit H1 to cluster
    remote_h1_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050"
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_h1_dir}"], check=True)
    for f in H1_DEST_DIR.iterdir():
        subprocess.run(["scp", "-i", SSH_KEY, str(f), f"{SSH_HOST}:{remote_h1_dir}/"], check=True)
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"sed -i 's/\\r$//' {remote_h1_dir}/* && chmod +x {remote_h1_dir}/*.sh"], check=True)

    print("\nExecuting guarded submission for M2CORR_H1_FREEU2_FULL_U050...")
    h1_res = subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"cd {remote_h1_dir} && ./guarded_submit_M2CORR_H1_FREEU2_FULL_U050.sh"], capture_output=True, text=True, check=True)
    print(h1_res.stdout)

    # 4. Sync & Submit H2 to cluster
    remote_h2_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050"
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_h2_dir}"], check=True)
    for f in H2_DEST_DIR.iterdir():
        subprocess.run(["scp", "-i", SSH_KEY, str(f), f"{SSH_HOST}:{remote_h2_dir}/"], check=True)
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"sed -i 's/\\r$//' {remote_h2_dir}/* && chmod +x {remote_h2_dir}/*.sh"], check=True)

    print("\nExecuting guarded submission for M2CORR_H2_FREEU2_FULL_U050...")
    h2_res = subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"cd {remote_h2_dir} && ./guarded_submit_M2CORR_H2_FREEU2_FULL_U050.sh"], capture_output=True, text=True, check=True)
    print(h2_res.stdout)

if __name__ == "__main__":
    main()
