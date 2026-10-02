#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate and Qualify the Continuous Target Control Diagnostic Package:
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL
"""

import os
import sys
import hashlib
import json
import shutil
import subprocess

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as fp:
        while chunk := fp.read(8192):
            h.update(chunk)
    return h.hexdigest()

def generate_package():
    src_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    pkg_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    
    if not os.path.exists(pkg_dir):
        os.makedirs(pkg_dir)
        
    src_inp = os.path.join(src_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp")
    src_for = os.path.join(src_dir, "f44_mixed_uel_restart_stateinit.for")
    
    tgt_inp = os.path.join(pkg_dir, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp")
    tgt_for = os.path.join(pkg_dir, "f44_mixed_uel_restart_stateinit.for")
    
    print("================================================================================")
    print("GENERATING CONTINUOUS TARGET CONTROL DIAGNOSTIC PACKAGE")
    print("================================================================================")
    
    # 1. Read source INP up to Step 1
    with open(src_inp, 'r') as fp:
        inp_lines = fp.readlines()
        
    # Find where STEP 1 starts
    step1_idx = None
    for idx, line in enumerate(inp_lines):
        if line.strip().startswith('*STEP, NAME=STATE_INSTALL'):
            # Step begins here; check previous comment line
            step1_idx = idx
            if idx > 0 and inp_lines[idx-1].strip().startswith('**'):
                step1_idx = idx - 1
            if idx > 1 and inp_lines[idx-2].strip().startswith('** ====='):
                step1_idx = idx - 2
            break
            
    if step1_idx is None:
        raise ValueError("Could not find STEP 1 in source INP!")
        
    mesh_header_lines = inp_lines[:step1_idx]
    
    # Update Heading
    new_header = [
        "*HEADING\n",
        "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL - Continuous Virgin Control on Stage-D Mesh\n",
        "** Target Mesh: Exact Stage-D Sliver-Free Graded Nonmatching 8836 quads (Nx=94, Ny=94)\n",
        "** Continuous Monotonic Shear from U1 = 0.0 to 0.050 mm (No Transfer, Virgin d=0, H=0)\n",
        "**\n"
    ]
    
    # Skip first 6 lines of old header and prepend new header
    combined_lines = new_header + mesh_header_lines[6:]
    
    # Append Single Continuous Step
    continuous_step_lines = [
        "** ==========================================================\n",
        "** STEP 1: Continuous Monotonic Shear to U1 = 0.050 mm\n",
        "** ==========================================================\n",
        "*STEP, NAME=ShearStep, NLGEOM=NO, INC=10000\n",
        "*STATIC\n",
        "0.001, 1.0, 1.0e-9, 0.02\n",
        "*BOUNDARY, OP=NEW\n",
        "N_BOTTOM, 1, 2, 0.0\n",
        "N_RP, 1, 1, 0.050000\n",
        "N_RP, 2, 2, 0.0\n",
        "*OUTPUT, FIELD, FREQ=1\n",
        "*NODE OUTPUT\n",
        "U, RF\n",
        "*NODE PRINT, FREQ=1\n",
        "U, RF\n",
        "*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH\n",
        "SDV14, SDV15, SDV16\n",
        "*END STEP\n"
    ]
    
    all_target_lines = combined_lines + continuous_step_lines
    
    with open(tgt_inp, 'w') as fp:
        fp.writelines(all_target_lines)
        
    print("Created continuous INP: %s (%d lines)" % (tgt_inp, len(all_target_lines)))
    
    # 2. Copy Fortran UEL Subroutine (Clean Virgin Initialization)
    # Ensure Fortran code explicitly zeroes state if no file present
    shutil.copy(src_for, tgt_for)
    print("Copied Fortran subroutine: %s" % tgt_for)
    
    # 3. Create PBS Launcher with Dual-Channel Notifications
    pbs_path = os.path.join(pkg_dir, "submit_job.pbs")
    pbs_content = """#!/bin/bash
#PBS -N M2_STAGE_D_CONT_CTRL
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q batch
#PBS -m ae
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

# ==============================================================================
# PBS JOB LAUNCHER: M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL
# ==============================================================================

set -eo pipefail

JOB_NAME="M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
JOB_DIR="/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
cd "$JOB_DIR"

# Dual-Channel Notification Helper
NOTIFY_SCRIPT="/home/pr21vyci/projects/adaptive-remeshing/scripts/infrastructure/notify.sh"
notify() {
    local event="$1"
    local msg="$2"
    if [ -f "$NOTIFY_SCRIPT" ]; then
        bash "$NOTIFY_SCRIPT" "$JOB_NAME" "$PBS_JOBID" "$event" "$msg" || true
    fi
}

trap 'notify "FAILED" "Job terminated unexpectedly with exit status $?"' ERR

notify "STARTED" "Job execution started on $(hostname)"

# Environment Modules
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

# Execute Abaqus
echo "Starting Abaqus execution at $(date)"
abaqus job="$JOB_NAME" user=f44_mixed_uel_restart_stateinit.for input="$JOB_NAME.inp" interactive cpus=1

EXIT_CODE=$?
echo "Abaqus completed at $(date) with exit code $EXIT_CODE"

if [ $EXIT_CODE -eq 0 ]; then
    notify "COMPLETED" "Abaqus job completed successfully"
else
    notify "FAILED" "Abaqus job completed with solver failure code $EXIT_CODE"
fi

exit $EXIT_CODE
"""
    with open(pbs_path, 'w') as fp:
        fp.write(pbs_content)
    print("Created PBS launcher: %s" % pbs_path)

if __name__ == "__main__":
    generate_package()
