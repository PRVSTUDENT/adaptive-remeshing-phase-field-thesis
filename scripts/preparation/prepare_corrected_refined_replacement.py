#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare Corrected Refined Replacement Package:
M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL
"""

import os
import sys
import shutil
import hashlib
import json

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def clean_lf(filepath):
    with open(filepath, "rb") as f:
        content = f.read()
    content_lf = content.replace(b"\r\n", b"\n")
    with open(filepath, "wb") as f:
        f.write(content_lf)

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    src_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL")
    dst_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL")
    
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    # 1. Copy text support files and clean LF
    for fname in ["MODE_STAGED.flag", "f44_mixed_uel_restart_stateinit.for",
                  "STAGE_E_PRIMARY_STATE_BOUNDARY.inp", "STAGE_E_U3_ONLY_BOUNDARY.inp"]:
        src_f = os.path.join(src_dir, fname)
        dst_f = os.path.join(dst_dir, fname)
        shutil.copy2(src_f, dst_f)
        clean_lf(dst_f)
        
    # Copy binary file verbatim (NO LF processing)
    src_bin = os.path.join(src_dir, "STAGE_D_COMMITTED_STATE.bin")
    dst_bin = os.path.join(dst_dir, "STAGE_D_COMMITTED_STATE.bin")
    shutil.copy2(src_bin, dst_bin)
    
    # Verify binary size
    assert os.path.getsize(dst_bin) == 6400016, "State binary size mismatch!"
    
    # 2. Build corrected INP deck with minimal Step 3 continuation controls
    src_inp = os.path.join(src_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL.inp")
    dst_inp = os.path.join(dst_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.inp")
    
    with open(src_inp, "r") as f:
        inp_content = f.read()
        
    # Target Step 3 replacement
    target_step3_block = """*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_RP, 1, 1, 1.051289000000e-02
N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP"""

    replacement_step3_block = """*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=200
*STATIC
0.001, 1.0, 1.0e-11, 1.0
*CONTROLS, PARAMETERS=TIME INCREMENTATION
4, 8, 9, 16, 10, 4, 50, 12
*BOUNDARY, OP=NEW
N_BOTTOM, 1, 2, 0.0
N_RP, 1, 1, 1.051289000000e-02
N_RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT, NSET=N_RP
U, RF
*END STEP"""

    assert target_step3_block in inp_content, "Target Step 3 block not found in original INP!"
    
    # Replace job header / heading comment
    corrected_inp_content = inp_content.replace(
        "** JOB NAME: M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL",
        "** JOB NAME: M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL"
    ).replace(
        target_step3_block,
        replacement_step3_block
    )
    
    with open(dst_inp, "w") as f:
        f.write(corrected_inp_content)
    clean_lf(dst_inp)
    
    # 3. Create PBS launcher
    pbs_content = """#!/bin/bash
#PBS -N M2E_REF_R1_XFER
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR || exit 1

# Clean old lock files
rm -f *.lck

# Correct compute-node module sequence
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

export PYTHONUNBUFFERED=1
JOBNAME=M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL
USER_SUBROUTINE=f44_mixed_uel_restart_stateinit.for

echo "[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)"
abaqus job=$JOBNAME input=$JOBNAME.inp user=$USER_SUBROUTINE cpus=1 interactive
EXIT_STATUS=$?
echo "[PBS] Solver execution exited with status $EXIT_STATUS at $(date)"
exit $EXIT_STATUS
"""
    pbs_path = os.path.join(dst_dir, "submit_job.pbs")
    with open(pbs_path, "w") as f:
        f.write(pbs_content)
    clean_lf(pbs_path)
    
    # 4. Generate Machine-Readable One-Difference Manifest
    manifest_data = {
        "replacement_package": "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL",
        "base_package": "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL",
        "base_job_id": "1391281.mmaster02",
        "provenance": {
            "source_donor_job": "1390447.mmaster02",
            "source_donor_frame": 17,
            "source_donor_u1_mm": 0.01051289,
            "target_mesh": "Refined (33,600 quads, 34,027 nodes, h_tip=0.002 mm)",
            "history_operator": "HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP"
        },
        "hashes": {
            "inp_sha256": sha256_file(dst_inp),
            "bin_sha256": sha256_file(dst_bin),
            "for_sha256": sha256_file(os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")),
            "pbs_sha256": sha256_file(pbs_path)
        },
        "one_difference_audit": {
            "mesh_changed": False,
            "state_binary_changed": False,
            "uel_subroutine_changed": False,
            "material_props_changed": False,
            "step_semantics_changed": False,
            "step1_state_install_changed": False,
            "step2_mech_equilibration_changed": False,
            "step3_phase_release_controls_modified": True,
            "step3_changes": {
                "before": {
                    "static_card": "1.0, 1.0, 1.0e-5, 1.0",
                    "controls_card": None,
                    "I_A": 5,
                    "dt_min": 1.0e-5
                },
                "after": {
                    "static_card": "0.001, 1.0, 1.0e-11, 1.0",
                    "controls_card": "4, 8, 9, 16, 10, 4, 50, 12",
                    "I_A": 12,
                    "dt_min": 1.0e-11
                }
            },
            "step4_continuation_changed": False
        }
    }
    
    manifest_path = os.path.join(base_dir, "refined_r1_one_difference_manifest.json")
    with open(manifest_path, "w") as fp:
        json.dump(manifest_data, fp, indent=2)
        
    print("================================================================================")
    print("PREPARED CORRECTED REFINED REPLACEMENT PACKAGE:")
    print("Package Dir: %s" % dst_dir)
    print("INP SHA256 : %s" % manifest_data["hashes"]["inp_sha256"])
    print("BIN SHA256 : %s (size = %d bytes)" % (manifest_data["hashes"]["bin_sha256"], os.path.getsize(dst_bin)))
    print("Manifest   : %s" % manifest_path)
    print("================================================================================")

if __name__ == "__main__":
    main()
