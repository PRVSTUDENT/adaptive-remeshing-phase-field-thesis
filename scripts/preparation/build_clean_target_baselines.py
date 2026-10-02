#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Construct Clean Target Baseline Packages directly from Default Baselines 1390527 and 1390528:
1. Refined Target: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL
   - Source: 1390527 (33,600 quads)
   - STATIC: 0.001, 1.0, 1.0e-11, 0.02
   - CONTROLS Line 1: 4, 8, 9, 16, 10, 4, 50, 12
   - Line 2: Omitted
2. Coarsened Target: M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL
   - Source: 1390528 (8,200 quads)
   - STATIC: 0.001, 1.0, 1.0e-11, 0.02
   - CONTROLS Line 1: 4, 8, 9, 16, 10, 4, 50, 12
   - Line 2: Omitted
"""

import os
import sys
import shutil
import hashlib
import json

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def build_clean_package(src_inp, dst_dir, dst_name):
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
        
    dst_inp = os.path.join(dst_dir, dst_name + ".inp")
    
    with open(src_inp, "r") as f:
        lines = f.readlines()
        
    new_lines = []
    in_step = False
    in_static = False
    static_done = False
    controls_done = False
    
    for idx, line in enumerate(lines):
        line_s = line.strip().upper()
        if line_s.startswith("*STEP"):
            in_step = True
            new_lines.append(line)
            continue
            
        if in_step and line_s.startswith("*STATIC"):
            in_static = True
            new_lines.append(line)
            continue
            
        if in_static and not static_done:
            # Replace static line with dt_min = 1.0e-11
            new_lines.append("0.001, 1.0, 1.0e-11, 0.02\n")
            # Insert path-neutral CONTROLS
            new_lines.append("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
            new_lines.append("4, 8, 9, 16, 10, 4, 50, 12\n")
            static_done = True
            controls_done = True
            in_static = False
            continue
            
        if in_step and line_s.startswith("*CONTROLS, PARAMETERS=TIME INCREMENTATION"):
            # Skip any existing controls block and its data lines
            continue
        if in_step and controls_done and lines[idx-1].strip().upper().startswith("*CONTROLS, PARAMETERS=TIME INCREMENTATION"):
            # Skip old controls data line
            continue
        else:
            new_lines.append(line)
            
    with open(dst_inp, "wb") as f:
        for nl in new_lines:
            f.write(nl.encode('utf-8'))
            
    # Copy UEL subroutine
    src_for = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for"
    dst_for = os.path.join(dst_dir, "f44_mixed_uel_restart_stateinit.for")
    shutil.copyfile(src_for, dst_for)
    
    # Write strict Unix LF PBS script
    dst_pbs = os.path.join(dst_dir, "submit_job.pbs")
    pbs_content = """#!/bin/bash
#PBS -N %(short_name)s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

# Clean old lock files
rm -f *.lck

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode start --job-name "%(job_name)s"

abaqus job=%(job_name)s input=%(job_name)s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive
ABAQUS_RC=$?

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode end --job-name "%(job_name)s" --exit-code "$ABAQUS_RC"

exit ${ABAQUS_RC}
""" % {"short_name": dst_name[:15], "job_name": dst_name}

    with open(dst_pbs, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode('utf-8'))
        
    return {
        "inp_path": dst_inp,
        "inp_sha256": get_file_sha256(dst_inp),
        "for_sha256": get_file_sha256(dst_for),
        "pbs_sha256": get_file_sha256(dst_pbs)
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Refined
    src_ref = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL.inp"
    dst_ref_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    res_ref = build_clean_package(src_ref, dst_ref_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    
    # 2. Coarsened
    src_coarse = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL.inp"
    dst_coarse_dir = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    res_coarse = build_clean_package(src_coarse, dst_coarse_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    
    manifest = {
        "stage": "Stage E Target Continuous Baselines (Path-Neutral dt_min=1e-11 & I_A=12 Protocol)",
        "protocol": {
            "I_A": 12,
            "dt_min": "1.0e-11 s",
            "defaults_preserved": "I_0=4, I_R=8, I_P=9, I_C=16, I_L=10, I_G=4, I_S=50, Line 2 omitted"
        },
        "packages": {
            "refined": {
                "name": "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL",
                "dir": dst_ref_dir,
                "provenance": res_ref
            },
            "coarsened": {
                "name": "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL",
                "dir": dst_coarse_dir,
                "provenance": res_coarse
            }
        }
    }
    
    manifest_path = os.path.join(base_dir, "stage_e_target_baselines_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    print("================================================================================")
    print("CLEAN TARGET BASELINES PACKAGES BUILD COMPLETE:")
    print("================================================================================")
    print("Refined INP SHA          : %s" % res_ref["inp_sha256"])
    print("Coarsened INP SHA        : %s" % res_coarse["inp_sha256"])
    print("Subroutine FOR SHA       : %s" % res_ref["for_sha256"])
    print("Manifest saved to        : %s" % manifest_path)

if __name__ == "__main__":
    main()
