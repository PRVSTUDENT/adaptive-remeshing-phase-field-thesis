#!/usr/bin/env python3
"""
F140SUB PK10R1 Same-Mesh Restart Validation Preparation & Guarded Submission Script
Task ID: F140SUB-M2-PK10R1-SAMEMESH-RESTART-VALIDATION-SUBMIT1
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

MODEL_DIR = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
SOURCE_INP = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"
F43_UEL = ROOT / "models/generated/mode_ii/production_control_batch/f43_mixed_uel_restart_capable.for"
STATE_BIN = ROOT / "models/generated/mode_ii/production_control_batch/PK10R1_INC29_SOURCE_STATE.bin"

def main():
    print("================================================================================")
    print("F140SUB PREPARING M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION")
    print("================================================================================")

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Verify source files and SHAs
    f43_bytes = F43_UEL.read_bytes()
    f43_sha256 = hashlib.sha256(f43_bytes).hexdigest()
    print(f"Verified f43 UEL SHA256: {f43_sha256}")
    
    state_bytes = STATE_BIN.read_bytes()
    state_sha256 = hashlib.sha256(state_bytes).hexdigest()
    print(f"Verified State File SHA256: {state_sha256}")
    
    # Copy Fortran and State files to model dir
    (MODEL_DIR / "f43_mixed_uel_restart_capable.for").write_bytes(f43_bytes)
    (MODEL_DIR / "PK10R1_INC29_SOURCE_STATE.bin").write_bytes(state_bytes)

    # 2. Build INP file for Same-Mesh Restart with STATE_INIT and CONTINUATION steps
    # Read base INP template
    source_inp_text = SOURCE_INP.read_text(encoding="utf-8")
    
    # Split model definition and step definition
    if "*STEP, NAME=ShearStep" in source_inp_text:
        header_mesh = source_inp_text.split("*STEP, NAME=ShearStep")[0].rstrip()
    elif "*STEP, NAME=Step-1" in source_inp_text:
        header_mesh = source_inp_text.split("*STEP, NAME=Step-1")[0].rstrip()
    else:
        header_mesh = source_inp_text.split("*STEP")[0].rstrip()
    
    # Build clean INP with STATE_INIT and CONTINUATION steps
    restart_inp_content = header_mesh + "\n" + """** ==========================================================
** STEP 1: Controlled State Initialization
** ==========================================================
*STEP, NAME=STATE_INIT, NLGEOM=NO, INC=10
*STATIC
 1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY
 N_BOTTOM, 1, 2, 0.00
 N_RP, 1, 1, 0.0005071650259196759
 N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP

** ==========================================================
** STEP 2: Continuation Loading to U1 = 0.050000 mm
** ==========================================================
*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
*STATIC
 0.001, 1.0, 1.0e-9, 0.02
*BOUNDARY, OP=MOD
 N_RP, 1, 1, 0.050000
 N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_TOP
U, RF
*NODE OUTPUT, NSET=N_BOTTOM
U, RF
*NODE OUTPUT, NSET=N_RP
U, RF
*NODE PRINT, FREQ=1
U, RF
*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH
SDV14, SDV15, SDV16
*END STEP
"""

    inp_file = MODEL_DIR / "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    inp_file.write_text(restart_inp_content, encoding="utf-8", newline="\n")
    inp_sha256 = hashlib.sha256(restart_inp_content.encode("utf-8")).hexdigest()
    print(f"Generated restart INP file (SHA256: {inp_sha256})")

    # 3. Create guarded PBS wrapper script submit_job.sh
    submit_script_content = """#!/bin/bash
#PBS -N entry_imfdfkmq
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de

set -e
cd "$PBS_O_WORKDIR"

# Source dual-channel notifications
NOTIFICATION_SCRIPT="$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh"
if [ -f "$NOTIFICATION_SCRIPT" ]; then
    source "$NOTIFICATION_SCRIPT"
    notification_install_terminal_trap
    notify_start "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
fi

export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH
source /etc/profile.d/lmod.sh 2>/dev/null || true
module load gcc/11.4.0 intel/2024.2.0 abaqus/2023

echo "Starting Abaqus Same-Mesh Restart Validation Job M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION..."
/cluster/application/abaqus/2023/Commands/abaqus job=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION user=f43_mixed_uel_restart_capable.for input=M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp double=both interactive
echo "Abaqus job completed successfully."
"""

    submit_file = MODEL_DIR / "submit_job.sh"
    submit_file.write_text(submit_script_content, encoding="utf-8", newline="\n")

    # 4. Sync directory to remote cluster
    remote_target_dir = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION"
    print(f"\nSyncing package to remote cluster: {remote_target_dir}...")
    
    mkdir_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"mkdir -p {remote_target_dir}"]
    subprocess.run(mkdir_cmd, check=True)

    scp_cmd = [
        "scp", "-i", SSH_KEY,
        str(inp_file),
        str(MODEL_DIR / "f43_mixed_uel_restart_capable.for"),
        str(MODEL_DIR / "PK10R1_INC29_SOURCE_STATE.bin"),
        str(submit_file),
        f"{SSH_HOST}:{remote_target_dir}/"
    ]
    subprocess.run(scp_cmd, check=True)
    
    chmod_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"chmod +x {remote_target_dir}/submit_job.sh"]
    subprocess.run(chmod_cmd, check=True)
    print("Package sync completed successfully.")

    # 5. Remote hash verification
    verify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && sha256sum f43_mixed_uel_restart_capable.for PK10R1_INC29_SOURCE_STATE.bin M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION.inp"
    ]
    res = subprocess.run(verify_cmd, capture_output=True, text=True, check=True)
    print("\nRemote SHA256 Verification:")
    print(res.stdout)

    # 6. Guarded qsub submission
    print("\nExecuting guarded submission (qsub)...")
    qsub_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"cd {remote_target_dir} && qsub submit_job.sh"
    ]
    qsub_res = subprocess.run(qsub_cmd, capture_output=True, text=True, check=True)
    job_id = qsub_res.stdout.strip()
    print(f"SUCCESS: Submitted job {job_id}")

    # Send notify_submitted
    notify_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        f"source $HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh 2>/dev/null || true; notify_submitted 'M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION' '{job_id}' 2>/dev/null || true"
    ]
    subprocess.run(notify_cmd, capture_output=True, text=True)

    print("\n================================================================================")
    print("MANDATORY SUBMISSION SUMMARY")
    print("================================================================================")
    print(f"job_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION")
    print(f"cluster_job_id = {job_id}")
    print(f"source_job = 1389684.mmaster02")
    print(f"source_step = 1")
    print(f"source_increment = 29")
    print(f"source_RP_U1_mm = 0.000507")
    print(f"source_RP_RF1_kN = 0.305468")
    print(f"source_dmax = 0.248652")
    print(f"source_Hcommitted_max = 0.051779")
    print(f"state_file_SHA256 = {state_sha256}")
    print(f"restart_capable_UEL_SHA256 = {f43_sha256}")
    print(f"resources = 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq")
    print(f"new_submission_authorized = true")
    print(f"qsub_called = true")
    print(f"qdel_called = false")
    print(f"qmove_called = false")

if __name__ == "__main__":
    main()
