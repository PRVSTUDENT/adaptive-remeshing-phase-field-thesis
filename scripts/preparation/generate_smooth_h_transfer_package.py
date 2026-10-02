#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package builder for M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H
"""

import os
import shutil
import hashlib
import json

def build_package():
    src_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    id_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL"
    dst_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H"
    os.makedirs(dst_dir, exist_ok=True)

    # 1. Copy Boundary files from 1390279 (exact mapped boundary files)
    shutil.copy2(os.path.join(src_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp"), os.path.join(dst_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp"))
    shutil.copy2(os.path.join(src_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp"), os.path.join(dst_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp"))

    # 2. Copy Mode 1 UEL and flag
    mode1_uel = os.path.join(id_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil.copy2(mode1_uel, os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for"))
    with open(os.path.join(dst_dir, "MODE_STAGED.flag"), "w") as fp:
        fp.write("MODE_1_STAGED_RESTART\n")

    # 3. Create INP with explicit Mode 1 architecture (PROPERTIES=7, PROPS(7)=1.0)
    inp_src = os.path.join(src_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp")
    with open(inp_src, "r") as fp:
        content = fp.read()

    # Ensure PROPERTIES=7 and PROPS(7)=1.0
    content = content.replace("PROPERTIES=6", "PROPERTIES=7")
    content = content.replace("210.0, 0.3, 0.0027, 0.015, 1e-07, 8836", "210.0, 0.3, 0.0027, 0.015, 1e-07, 8836, 1.0")

    inp_dst = os.path.join(dst_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H.inp")
    with open(inp_dst, "w") as fp:
        fp.write(content)

    # 4. Create PBS launcher
    pbs_content = """#PBS -N M2_SMOOTH_H
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q normal_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -j oe

cd $PBS_O_WORKDIR

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "=== PBS JOB EXECUTION ENVIRONMENT ==="
echo "Node: $(hostname)"
echo "Job ID: $PBS_JOBID"
echo "Working directory: $(pwd)"
echo "Start time: $(date)"

abaqus job=M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H user=f44_mixed_uel_restart_stateinit.for input=M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H.inp interactive

EXIT_STATUS=$?
echo "Abaqus exit status: $EXIT_STATUS"
echo "End time: $(date)"
exit $EXIT_STATUS
"""
    with open(os.path.join(dst_dir, "submit_job.pbs"), "w") as fp:
        fp.write(pbs_content)

    # 5. Create one-difference scientific manifest against 1390279
    one_diff = {
        "benchmark_control_job": "1390279.mmaster02",
        "diagnostic_candidate_job": "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H",
        "mesh_geometry": "IDENTICAL (Stage-D 8,836 quads, 9,073 nodes)",
        "mapped_mechanical_displacement": "IDENTICAL (Installed from STAGE_D_PRIMARY_STATE_BOUNDARY.inp)",
        "mapped_nodal_phase_field": "IDENTICAL (Installed from STAGE_D_PRIMARY_STATE_BOUNDARY.inp)",
        "uel_formulation": "IDENTICAL (Explicit Mode 1 Staged UEL, PROPERTIES=7, PROPS(7)=1.0)",
        "staging_sequence": "IDENTICAL (STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION)",
        "single_scientific_difference": "History Transfer Operator in STAGE_D_COMMITTED_STATE.bin changed from HOST_NEAREST_GP to HOST_ISOPARAMETRIC_BILINEAR_CLAMPED"
    }
    with open(os.path.join(dst_dir, "one_difference_scientific_manifest.json"), "w") as fp:
        json.dump(one_diff, fp, indent=2)

    # 6. Generate SHA-256 manifest
    manifest = {}
    for fname in sorted(os.listdir(dst_dir)):
        fpath = os.path.join(dst_dir, fname)
        if os.path.isfile(fpath) and fname != "manifest.json":
            with open(fpath, "rb") as fp:
                manifest[fname] = hashlib.sha256(fp.read()).hexdigest()

    with open(os.path.join(dst_dir, "manifest.json"), "w") as fp:
        json.dump(manifest, fp, indent=2)

    print("Successfully built package in %s" % dst_dir)
    print("Files and hashes:\n%s" % json.dumps(manifest, indent=2))

if __name__ == "__main__":
    build_package()
